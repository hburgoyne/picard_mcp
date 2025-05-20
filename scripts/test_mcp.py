import sys
import os
import asyncio
import httpx
from urllib.parse import urlencode

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

async def test_oauth_flow():
    """Test OAuth 2.0 Authorization Code flow"""
    # When running inside Docker, we need to use the service name as hostname
    # rather than the MCP_SERVER_HOST which is set to 0.0.0.0
    base_url = "http://app:8000"
    client_id = settings.OAUTH_CLIENT_ID
    redirect_uri = settings.OAUTH_REDIRECT_URI
    
    # Step 1: Authorization Request
    # Generate a simple code challenge for PKCE
    import hashlib
    import base64
    import secrets
    
    # Generate code verifier
    code_verifier = secrets.token_urlsafe(32)
    
    # Generate code challenge using S256 method
    code_challenge_bytes = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode('ascii').rstrip('=')
    
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "memories:read memories:write",
        "state": "test_state",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    auth_url = f"{base_url}/oauth/authorize?{urlencode(auth_params)}"
    
    print(f"Authorization URL: {auth_url}")
    print("In a real application, the user would be redirected to this URL.")
    print("For testing, we'll simulate the redirect and authorization.")
    
    # Step 2: Simulate authorization and get code
    async with httpx.AsyncClient() as client:
        response = await client.get(auth_url, follow_redirects=True)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.text}")
            return
        
        # Extract code from redirect URL
        redirect_url = str(response.url)
        if "code=" not in redirect_url:
            print(f"Error: No authorization code in redirect URL: {redirect_url}")
            return
        
        code = redirect_url.split("code=")[1].split("&")[0]
        print(f"Received authorization code: {code}")
        
        # Step 3: Token Request
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "code_verifier": code_verifier
        }
        
        token_response = await client.post(f"{base_url}/oauth/token", data=token_data)
        
        if token_response.status_code != 200:
            print(f"Error: {token_response.status_code} {token_response.text}")
            return
        
        token_data = token_response.json()
        access_token = token_data["access_token"]
        print(f"Received access token: {access_token[:10]}...")
        
        # Step 4: Test memory endpoints
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Test submit_memory
        memory_data = {
            "text": "This is a test memory for vector embedding"
        }
        memory_response = await client.post(f"{base_url}/submit_memory", json=memory_data, headers=headers)
        
        if memory_response.status_code != 200:
            print(f"Error submitting memory: {memory_response.status_code} {memory_response.text}")
            return
        
        memory = memory_response.json()
        memory_id = memory["id"]
        print(f"Created memory with ID: {memory_id}")
        
        # Test retrieve_memories
        memories_response = await client.post(f"{base_url}/retrieve_memories", headers=headers)
        
        if memories_response.status_code != 200:
            print(f"Error retrieving memories: {memories_response.status_code} {memories_response.text}")
            return
        
        memories = memories_response.json()
        print(f"Retrieved {len(memories)} memories")
        
        # Test modify_permissions
        permission_data = {
            "memory_id": memory_id,
            "permission": "public"
        }
        permission_response = await client.post(
            f"{base_url}/modify_permissions", 
            json=permission_data, 
            headers=headers
        )
        
        if permission_response.status_code != 200:
            print(f"Error modifying permissions: {permission_response.status_code} {permission_response.text}")
            return
        
        updated_memory = permission_response.json()
        print(f"Updated memory permission to: {updated_memory['permission']}")
        
        # Test query_user
        query_data = {
            "user_id": 1,  # Assuming user ID 1 exists
            "prompt": "What are your thoughts on local politics?"
        }
        query_response = await client.post(f"{base_url}/query_user", json=query_data, headers=headers)
        
        if query_response.status_code != 200:
            print(f"Error querying user: {query_response.status_code} {query_response.text}")
            return
        
        query_result = query_response.json()
        print(f"LLM response: {query_result['response']}")
        
        print("All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_oauth_flow())
