from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone

import requests
import json
import uuid
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from urllib.parse import urlencode

from .models import OAuthToken, Memory, UserProfile
from .forms import MemoryForm, MemorySearchForm, UserQueryForm, UserRegistrationForm, UserProfileForm

def generate_code_verifier():
    """Generate a code verifier for PKCE."""
    code_verifier = secrets.token_urlsafe(64)
    return code_verifier

def generate_code_challenge(code_verifier):
    """Generate a code challenge from the code verifier using SHA-256."""
    code_challenge = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode().rstrip('=')
    return code_challenge

@login_required
def dashboard(request):
    """Dashboard view showing user's memories and OAuth connection status."""
    try:
        oauth_token = OAuthToken.objects.get(user=request.user)
        connected = True
        token_expired = oauth_token.is_expired
    except OAuthToken.DoesNotExist:
        connected = False
        token_expired = True
    
    # Get user's memories from local database
    memories = Memory.objects.filter(user=request.user)
    
    context = {
        'connected': connected,
        'token_expired': token_expired,
        'memories': memories,
    }
    return render(request, 'memory_app/dashboard.html', context)

@login_required
def oauth_authorize(request):
    """Initiate OAuth 2.0 authorization flow with the MCP server."""
    # Generate state and code_verifier
    state = secrets.token_urlsafe(32)
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # Store state and code_verifier in session
    request.session['oauth_state'] = state
    request.session['oauth_code_verifier'] = code_verifier
    
    # Prepare authorization URL
    params = {
        'response_type': 'code',
        'client_id': settings.OAUTH_CLIENT_ID,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'scope': settings.OAUTH_SCOPES,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    
    # Use the correct path for the authorization endpoint
    authorization_url = f"{settings.MCP_SERVER_URL}/api/oauth/authorize?{urlencode(params)}"
    return redirect(authorization_url)

@login_required
def oauth_callback(request):
    """Handle OAuth 2.0 callback from the MCP server."""
    # Get authorization code and state from query parameters
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    # Verify state
    if state != request.session.get('oauth_state'):
        messages.error(request, 'Invalid state parameter. Please try again.')
        return redirect('dashboard')
    
    # Exchange authorization code for tokens
    code_verifier = request.session.get('oauth_code_verifier')
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'client_id': settings.OAUTH_CLIENT_ID,
        'client_secret': settings.OAUTH_CLIENT_SECRET,
        'code_verifier': code_verifier,
    }
    
    try:
        response = requests.post(f"{settings.MCP_SERVER_URL}/api/oauth/token", data=token_data)
        response.raise_for_status()
        token_info = response.json()
        
        # Calculate token expiration
        expires_in = token_info.get('expires_in', 3600)  # Default to 1 hour
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Save tokens to database
        oauth_token, created = OAuthToken.objects.update_or_create(
            user=request.user,
            defaults={
                'access_token': token_info['access_token'],
                'refresh_token': token_info['refresh_token'],
                'expires_at': expires_at,
                'scope': token_info['scope'],
            }
        )
        
        messages.success(request, 'Successfully connected to MCP server.')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error connecting to MCP server: {str(e)}')
    
    # Clean up session
    if 'oauth_state' in request.session:
        del request.session['oauth_state']
    if 'oauth_code_verifier' in request.session:
        del request.session['oauth_code_verifier']
    
    return redirect('dashboard')

@login_required
def refresh_token(request):
    """Refresh the OAuth access token."""
    try:
        oauth_token = OAuthToken.objects.get(user=request.user)
        
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': oauth_token.refresh_token,
            'client_id': settings.OAUTH_CLIENT_ID,
            'client_secret': settings.OAUTH_CLIENT_SECRET,
        }
        
        # Send token refresh request
        response = requests.post(f"{settings.MCP_SERVER_URL}/api/oauth/token", data=token_data)
        response.raise_for_status()
        token_info = response.json()
        
        # Calculate token expiration
        expires_in = token_info.get('expires_in', 3600)  # Default to 1 hour
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Update tokens in database
        oauth_token.access_token = token_info['access_token']
        oauth_token.refresh_token = token_info['refresh_token']
        oauth_token.expires_at = expires_at
        oauth_token.scope = token_info['scope']
        oauth_token.save()
        
        messages.success(request, 'Successfully refreshed access token.')
    except OAuthToken.DoesNotExist:
        messages.error(request, 'No OAuth token found. Please connect to MCP server first.')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error refreshing token: {str(e)}')
    
    return redirect('dashboard')

@login_required
def create_memory(request):
    """Create a new memory in the MCP server."""
    if request.method == 'POST':
        form = MemoryForm(request.POST)
        if form.is_valid():
            try:
                # Get OAuth token
                oauth_token = OAuthToken.objects.get(user=request.user)
                
                # Check if token is expired and refresh if needed
                if oauth_token.is_expired:
                    return redirect('refresh_token')
                
                # Prepare memory data
                memory_data = {
                    'tool': 'submit_memory',
                    'data': {
                        'text': form.cleaned_data['text'],
                        'permission': form.cleaned_data['permission'],
                    }
                }
                
                # Add expiration date if provided
                if form.cleaned_data['expiration_date']:
                    memory_data['data']['expiration_date'] = form.cleaned_data['expiration_date'].isoformat()
                
                # Send request to MCP server
                headers = {
                    'Authorization': f'Bearer {oauth_token.access_token}',
                    'Content-Type': 'application/json',
                }
                
                response = requests.post(
                    f"{settings.MCP_SERVER_URL}/api/tools",
                    headers=headers,
                    json=memory_data
                )
                response.raise_for_status()
                result = response.json()
                
                # Create local copy of memory
                memory = Memory.objects.create(
                    id=uuid.UUID(result['data']['id']),
                    user=request.user,
                    text=form.cleaned_data['text'],
                    permission=form.cleaned_data['permission'],
                    expiration_date=form.cleaned_data['expiration_date'],
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                
                messages.success(request, 'Memory created successfully.')
                return redirect('dashboard')
            
            except OAuthToken.DoesNotExist:
                messages.error(request, 'Please connect to MCP server first.')
            except requests.exceptions.RequestException as e:
                messages.error(request, f'Error creating memory: {str(e)}')
    else:
        form = MemoryForm()
    
    return render(request, 'memory_app/create_memory.html', {'form': form})

@login_required
def edit_memory(request, memory_id):
    """Edit an existing memory in the MCP server."""
    memory = get_object_or_404(Memory, id=memory_id, user=request.user)
    
    if request.method == 'POST':
        form = MemoryForm(request.POST, instance=memory)
        if form.is_valid():
            try:
                # Get OAuth token
                oauth_token = OAuthToken.objects.get(user=request.user)
                
                # Check if token is expired and refresh if needed
                if oauth_token.is_expired:
                    return redirect('refresh_token')
                
                # Prepare memory data
                memory_data = {
                    'tool': 'update_memory',
                    'data': {
                        'memory_id': str(memory.id),
                        'text': form.cleaned_data['text'],
                    }
                }
                
                # Add expiration date if provided
                if form.cleaned_data['expiration_date']:
                    memory_data['data']['expiration_date'] = form.cleaned_data['expiration_date'].isoformat()
                
                # Send request to MCP server
                headers = {
                    'Authorization': f'Bearer {oauth_token.access_token}',
                    'Content-Type': 'application/json',
                }
                
                response = requests.post(
                    f"{settings.MCP_SERVER_URL}/api/tools",
                    headers=headers,
                    json=memory_data
                )
                response.raise_for_status()
                
                # Update permission if changed
                if form.cleaned_data['permission'] != memory.permission:
                    permission_data = {
                        'tool': 'modify_permissions',
                        'data': {
                            'memory_id': str(memory.id),
                            'permission': form.cleaned_data['permission'],
                        }
                    }
                    
                    response = requests.post(
                        f"{settings.MCP_SERVER_URL}/api/tools",
                        headers=headers,
                        json=permission_data
                    )
                    response.raise_for_status()
                
                # Update local copy of memory
                form.save()
                memory.updated_at = timezone.now()
                memory.save()
                
                messages.success(request, 'Memory updated successfully.')
                return redirect('dashboard')
            
            except OAuthToken.DoesNotExist:
                messages.error(request, 'Please connect to MCP server first.')
            except requests.exceptions.RequestException as e:
                messages.error(request, f'Error updating memory: {str(e)}')
    else:
        form = MemoryForm(instance=memory)
    
    return render(request, 'memory_app/edit_memory.html', {'form': form, 'memory': memory})

@login_required
def delete_memory(request, memory_id):
    """Delete a memory from the MCP server."""
    memory = get_object_or_404(Memory, id=memory_id, user=request.user)
    
    if request.method == 'POST':
        try:
            # Get OAuth token
            oauth_token = OAuthToken.objects.get(user=request.user)
            
            # Check if token is expired and refresh if needed
            if oauth_token.is_expired:
                return redirect('refresh_token')
            
            # Prepare memory data
            memory_data = {
                'tool': 'delete_memory',
                'data': {
                    'memory_id': str(memory.id),
                }
            }
            
            # Send request to MCP server
            headers = {
                'Authorization': f'Bearer {oauth_token.access_token}',
                'Content-Type': 'application/json',
            }
            
            response = requests.post(
                f"{settings.MCP_SERVER_URL}/api/tools",
                headers=headers,
                json=memory_data
            )
            response.raise_for_status()
            
            # Delete local copy of memory
            memory.delete()
            
            messages.success(request, 'Memory deleted successfully.')
        
        except OAuthToken.DoesNotExist:
            messages.error(request, 'Please connect to MCP server first.')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error deleting memory: {str(e)}')
    
    return redirect('dashboard')

@login_required
def search_memories(request):
    """Search for memories using semantic search."""
    if request.method == 'POST':
        form = MemorySearchForm(request.POST)
        if form.is_valid():
            try:
                # Get OAuth token
                oauth_token = OAuthToken.objects.get(user=request.user)
                
                # Check if token is expired and refresh if needed
                if oauth_token.is_expired:
                    return redirect('refresh_token')
                
                # Prepare search data
                search_data = {
                    'tool': 'query_memory',
                    'data': {
                        'query': form.cleaned_data['query'],
                        'limit': form.cleaned_data['limit'],
                    }
                }
                
                # Send request to MCP server
                headers = {
                    'Authorization': f'Bearer {oauth_token.access_token}',
                    'Content-Type': 'application/json',
                }
                
                response = requests.post(
                    f"{settings.MCP_SERVER_URL}/api/tools",
                    headers=headers,
                    json=search_data
                )
                response.raise_for_status()
                result = response.json()
                
                # Process search results
                memories = result['data']['memories']
                
                return render(request, 'memory_app/search_results.html', {
                    'form': form,
                    'memories': memories,
                    'query': form.cleaned_data['query'],
                })
            
            except OAuthToken.DoesNotExist:
                messages.error(request, 'Please connect to MCP server first.')
            except requests.exceptions.RequestException as e:
                messages.error(request, f'Error searching memories: {str(e)}')
                return redirect('search_memories')
    else:
        form = MemorySearchForm()
    
    return render(request, 'memory_app/search_memories.html', {'form': form})

@login_required
def query_user(request):
    """Query a user's persona based on their memories."""
    if request.method == 'POST':
        form = UserQueryForm(request.POST)
        if form.is_valid():
            try:
                # Get OAuth token
                oauth_token = OAuthToken.objects.get(user=request.user)
                
                # Check if token is expired and refresh if needed
                if oauth_token.is_expired:
                    return redirect('refresh_token')
                
                # Prepare query data
                query_data = {
                    'tool': 'query_user',
                    'data': {
                        'user_id': str(form.cleaned_data['user_id']),
                        'prompt': form.cleaned_data['prompt'],
                    }
                }
                
                # Send request to MCP server
                headers = {
                    'Authorization': f'Bearer {oauth_token.access_token}',
                    'Content-Type': 'application/json',
                }
                
                response = requests.post(
                    f"{settings.MCP_SERVER_URL}/api/tools",
                    headers=headers,
                    json=query_data
                )
                response.raise_for_status()
                result = response.json()
                
                # Process query results
                response_text = result['data']['response']
                
                return render(request, 'memory_app/query_results.html', {
                    'form': form,
                    'response': response_text,
                    'prompt': form.cleaned_data['prompt'],
                })
            
            except OAuthToken.DoesNotExist:
                messages.error(request, 'Please connect to MCP server first.')
            except requests.exceptions.RequestException as e:
                messages.error(request, f'Error querying user: {str(e)}')
                return redirect('query_user')
    else:
        form = UserQueryForm()
    
    return render(request, 'memory_app/query_user.html', {'form': form})

@login_required
def sync_memories(request):
    """Sync memories from the MCP server to the local database."""
    try:
        # Get OAuth token
        oauth_token = OAuthToken.objects.get(user=request.user)
        
        # Check if token is expired and refresh if needed
        if oauth_token.is_expired:
            return redirect('refresh_token')
        
        # Prepare request data
        request_data = {
            'tool': 'retrieve_memories',
            'data': {}
        }
        
        # Send request to MCP server
        headers = {
            'Authorization': f'Bearer {oauth_token.access_token}',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(
            f"{settings.MCP_SERVER_URL}/api/tools",
            headers=headers,
            json=request_data
        )
        response.raise_for_status()
        result = response.json()
        
        # Process memories
        remote_memories = result['data']['memories']
        
        # Clear existing memories
        Memory.objects.filter(user=request.user).delete()
        
        # Create local copies of memories
        for memory_data in remote_memories:
            memory = Memory(
                id=uuid.UUID(memory_data['id']),
                user=request.user,
                text=memory_data['text'],
                permission=memory_data['permission'],
                created_at=datetime.fromisoformat(memory_data['created_at']),
                updated_at=datetime.fromisoformat(memory_data['updated_at']),
            )
            
            if memory_data.get('expiration_date'):
                memory.expiration_date = datetime.fromisoformat(memory_data['expiration_date'])
            
            memory.save()
        
        messages.success(request, f'Successfully synced {len(remote_memories)} memories.')
    
    except OAuthToken.DoesNotExist:
        messages.error(request, 'Please connect to MCP server first.')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error syncing memories: {str(e)}')
    
    return redirect('dashboard')

def register(request):
    """Register a new user."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def profile_view(request):
    """View user profile."""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'memory_app/profile.html', {'form': form})
