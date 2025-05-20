#!/usr/bin/env python
import sys
import os
import asyncio
import httpx
from urllib.parse import urlencode

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

async def get_test_token():
    """Get a test access token for API testing"""
    # When running inside Docker, we need to use the service name as hostname
    base_url = "http://localhost:8000"
    client_id = settings.OAUTH_CLIENT_ID
    redirect_uri = settings.OAUTH_REDIRECT_URI
    
    # Step 1: Authorization Request
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "memories:read memories:write",
        "state": "test_state"
    }
    auth_url = f"{base_url}/oauth/authorize?{urlencode(auth_params)}"
    
    # Step 2: Simulate authorization and get code
    async with httpx.AsyncClient() as client:
        response = await client.get(auth_url, follow_redirects=True)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.text}", file=sys.stderr)
            return None
        
        # Extract code from redirect URL
        redirect_url = str(response.url)
        if "code=" not in redirect_url:
            print(f"Error: No authorization code in redirect URL: {redirect_url}", file=sys.stderr)
            return None
        
        code = redirect_url.split("code=")[1].split("&")[0]
        
        # Step 3: Token Request
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": settings.OAUTH_CLIENT_SECRET
        }
        
        token_response = await client.post(f"{base_url}/oauth/token", data=token_data)
        
        if token_response.status_code != 200:
            print(f"Error: {token_response.status_code} {token_response.text}", file=sys.stderr)
            return None
        
        token_data = token_response.json()
        access_token = token_data["access_token"]
        
        # Print only the token to stdout for use in scripts
        print(access_token)
        return access_token

if __name__ == "__main__":
    token = asyncio.run(get_test_token())
    if not token:
        sys.exit(1)
