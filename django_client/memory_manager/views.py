import json
import requests
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from oauth_client.models import OAuthToken
from .models import Memory
from .forms import MemoryForm, QueryForm


@login_required
def memory_list(request):
    """List all memories for the current user"""
    try:
        token = OAuthToken.objects.get(user=request.user)
    except OAuthToken.DoesNotExist:
        return redirect('oauth_authorize')
    
    # Get memories from MCP server
    headers = {
        'Authorization': f'Bearer {token.access_token}',
        'Content-Type': 'application/json'
    }
    
    # Use MCP_SERVER_INTERNAL_URL for server-to-server communication
    mcp_url = getattr(settings, 'MCP_SERVER_INTERNAL_URL', settings.MCP_SERVER_URL)
    response = requests.get(f"{mcp_url}/tools/memories", headers=headers)
    
    if response.status_code == 401:
        # Token expired, redirect to refresh
        return redirect('refresh_token')
    
    if response.status_code != 200:
        return render(request, 'memory_manager/memory_list.html', {
            'error': f'Failed to fetch memories: {response.text}'
        })
    
    memories = response.json()
    
    return render(request, 'memory_manager/memory_list.html', {
        'memories': memories
    })


@login_required
def create_memory(request):
    """Create a new memory"""
    try:
        token = OAuthToken.objects.get(user=request.user)
    except OAuthToken.DoesNotExist:
        return redirect('oauth_authorize')
    
    if request.method == 'POST':
        form = MemoryForm(request.POST)
        if form.is_valid():
            memory_text = form.cleaned_data['text']
            is_public = form.cleaned_data['is_public']
            
            # Submit memory to MCP server
            headers = {
                'Authorization': f'Bearer {token.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'text': memory_text,
                'is_public': is_public
            }
            
            # Use MCP_SERVER_INTERNAL_URL for server-to-server communication
            mcp_url = getattr(settings, 'MCP_SERVER_INTERNAL_URL', settings.MCP_SERVER_URL)
            response = requests.post(
                f"{mcp_url}/tools/submit_memory",
                headers=headers,
                json=data
            )
            
            if response.status_code == 401:
                # Token expired, redirect to refresh
                return redirect('refresh_token')
            
            if response.status_code != 200:
                return render(request, 'memory_manager/create_memory.html', {
                    'form': form,
                    'error': f'Failed to create memory: {response.text}'
                })
            
            memory_data = response.json()
            
            # Save memory to local database
            memory = Memory.objects.create(
                user=request.user,
                memory_id=memory_data.get('id'),
                text=memory_text,
                is_public=is_public
            )
            
            return redirect('memory_list')
    else:
        form = MemoryForm()
    
    return render(request, 'memory_manager/create_memory.html', {
        'form': form
    })


@login_required
def update_memory(request, memory_id):
    """Update a memory's permissions"""
    try:
        token = OAuthToken.objects.get(user=request.user)
        memory = Memory.objects.get(memory_id=memory_id, user=request.user)
    except OAuthToken.DoesNotExist:
        return redirect('oauth_authorize')
    except Memory.DoesNotExist:
        return redirect('memory_list')
    
    if request.method == 'POST':
        form = MemoryForm(request.POST, instance=memory)
        if form.is_valid():
            is_public = form.cleaned_data['is_public']
            
            # Update memory on MCP server
            headers = {
                'Authorization': f'Bearer {token.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'id': memory_id,
                'is_public': is_public
            }
            
            # Use MCP_SERVER_INTERNAL_URL for server-to-server communication
            mcp_url = getattr(settings, 'MCP_SERVER_INTERNAL_URL', settings.MCP_SERVER_URL)
            response = requests.put(
                f"{mcp_url}/tools/update_memory",
                headers=headers,
                json=data
            )
            
            if response.status_code == 401:
                # Token expired, redirect to refresh
                return redirect('refresh_token')
            
            if response.status_code != 200:
                return render(request, 'memory_manager/update_memory.html', {
                    'form': form,
                    'memory': memory,
                    'error': f'Failed to update memory: {response.text}'
                })
            
            # Update local memory
            memory.is_public = is_public
            memory.save()
            
            return redirect('memory_list')
    else:
        form = MemoryForm(instance=memory)
    
    return render(request, 'memory_manager/update_memory.html', {
        'form': form,
        'memory': memory
    })


@login_required
def query_user(request):
    """Query the user's memories"""
    try:
        token = OAuthToken.objects.get(user=request.user)
    except OAuthToken.DoesNotExist:
        return redirect('oauth_authorize')
    
    response_data = None
    
    if request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            prompt = form.cleaned_data['prompt']
            
            # Submit query to MCP server
            headers = {
                'Authorization': f'Bearer {token.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'prompt': prompt
            }
            
            # Use MCP_SERVER_INTERNAL_URL for server-to-server communication
            mcp_url = getattr(settings, 'MCP_SERVER_INTERNAL_URL', settings.MCP_SERVER_URL)
            response = requests.post(
                f"{mcp_url}/tools/query",
                headers=headers,
                json=data
            )
            
            if response.status_code == 401:
                # Token expired, redirect to refresh
                return redirect('refresh_token')
            
            if response.status_code != 200:
                return render(request, 'memory_manager/query.html', {
                    'form': form,
                    'error': f'Failed to query: {response.text}'
                })
            
            response_data = response.json()
    else:
        form = QueryForm()
    
    return render(request, 'memory_manager/query.html', {
        'form': form,
        'response': response_data
    })
