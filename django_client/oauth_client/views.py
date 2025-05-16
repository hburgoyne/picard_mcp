import json
import uuid
import base64
import hashlib
import os
import requests
from datetime import datetime, timedelta
import urllib.parse

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from .models import OAuthToken
from .forms import UserRegistrationForm, UserLoginForm


# Helper functions for PKCE (Proof Key for Code Exchange)
def generate_code_verifier():
    """Generate a code verifier for PKCE"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    return code_verifier.rstrip('=')


def generate_code_challenge(code_verifier):
    """Generate a code challenge for PKCE using S256 method"""
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    return code_challenge.rstrip('=')


def home(request):
    """Home page view"""
    return render(request, 'oauth_client/home.html')


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'oauth_client/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'oauth_client/login.html', {'form': form})


def logout_view(request):
    """User logout view"""
    logout(request)
    return redirect('home')


@login_required
def oauth_authorize(request):
    """Redirect user to MCP server for authorization"""
    print("=== OAuth Authorization Flow Starting ===")
    print(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    
    # Generate a random state to prevent CSRF attacks
    state = str(uuid.uuid4())
    request.session['oauth_state'] = state
    print(f"Generated state: {state}")
    
    # Generate PKCE code verifier and challenge
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    print(f"Generated code_verifier: {code_verifier}")
    print(f"Generated code_challenge: {code_challenge}")
    
    # Store the code verifier in the session for later use
    request.session['code_verifier'] = code_verifier
    
    # Build the authorization URL - use MCP_SERVER_URL for browser redirects
    auth_url = f"{settings.MCP_SERVER_URL}/oauth/authorize"
    params = {
        'response_type': 'code',
        'client_id': settings.OAUTH_CLIENT_ID,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'scope': settings.OAUTH_SCOPES,  # This is already a space-separated string
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    print(f"Authorization URL: {auth_url}?{urllib.parse.urlencode(params)}")
    print(f"Client ID: {settings.OAUTH_CLIENT_ID}")
    print(f"Redirect URI: {settings.OAUTH_REDIRECT_URI}")
    print(f"Requested scopes: {settings.OAUTH_SCOPES}")
    
    # Construct the full URL with query parameters
    auth_url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
    
    return redirect(auth_url)


@login_required
def oauth_callback(request):
    """Handle callback from MCP server with authorization code"""
    code = request.GET.get('code')
    if not code:
        print("Missing authorization code")
        return JsonResponse({'error': 'missing_code'}, status=400)
    
    # Exchange authorization code for tokens
    # Use MCP_SERVER_INTERNAL_URL for server-to-server communication
    token_url = f"{getattr(settings, 'MCP_SERVER_INTERNAL_URL', settings.MCP_SERVER_URL)}/oauth/token"
    print(f"Token URL: {token_url}")
    print(f"Client ID: {settings.OAUTH_CLIENT_ID}")
    print(f"Redirect URI: {settings.OAUTH_REDIRECT_URI}")
    print(f"Code Verifier: {request.session.get('code_verifier')}")
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'client_id': settings.OAUTH_CLIENT_ID,
        'client_secret': settings.OAUTH_CLIENT_SECRET,
        'code_verifier': request.session.get('code_verifier')
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        print(f"Failed to obtain access token: {response.text}")
        return JsonResponse({'error': 'Failed to obtain access token'}, status=400)
    
    # Parse the response
    token_data = response.json()
    
    # Calculate the expiration time
    expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    # Save the token to the database
    token, created = OAuthToken.objects.update_or_create(
        user=request.user,
        defaults={
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': expires_at,
            'scope': token_data.get('scope', '')
        }
    )
    
    return redirect('dashboard')


@login_required
def dashboard(request):
    """User dashboard view"""
    try:
        token = OAuthToken.objects.get(user=request.user)
        has_token = True
    except OAuthToken.DoesNotExist:
        has_token = False
        token = None
    
    return render(request, 'oauth_client/dashboard.html', {
        'has_token': has_token,
        'token': token
    })


@login_required
def refresh_token(request):
    """Refresh the access token"""
    try:
        token = OAuthToken.objects.get(user=request.user)
    except OAuthToken.DoesNotExist:
        return JsonResponse({'error': 'No token found'}, status=400)
    
    # Exchange the refresh token for a new access token
    # Use MCP_SERVER_INTERNAL_URL for server-to-server communication
    token_url = f"{getattr(settings, 'MCP_SERVER_INTERNAL_URL', settings.MCP_SERVER_URL)}/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': token.refresh_token,
        'client_id': settings.OAUTH_CLIENT_ID,
        'client_secret': settings.OAUTH_CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        return JsonResponse({'error': 'Failed to refresh token'}, status=400)
    
    # Parse the response
    token_data = response.json()
    
    # Calculate the expiration time
    expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    # Update the token in the database
    token.access_token = token_data.get('access_token')
    token.refresh_token = token_data.get('refresh_token', token.refresh_token)
    token.expires_at = expires_at
    token.scope = token_data.get('scope', token.scope)
    token.save()
    
    return JsonResponse({'success': True})
