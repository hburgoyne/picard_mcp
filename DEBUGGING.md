# OAuth Debugging Guide

This guide provides detailed steps and information for debugging OAuth issues in the Picard MCP server implementation.

## Current Issue: Scope Validation Error

### Error Details
When attempting to connect the Django client to the MCP server, we encounter an "invalid_scope" error despite the client being registered with the correct scopes.

#### Error Message
```
error=invalid_scope&error_description=Client+was+not+registered+with+scope+memories%3Aread
```

### Debugging Steps Taken

1. **Database Verification**
   - Confirmed client registration in database with scopes: `['memories:read', 'memories:write', 'memories:admin']`
   - Verified client ID and redirect URI match configuration

2. **Code Path Analysis**
   - Added extensive logging in `authorize` method of `PicardOAuthProvider`
   - Modified scope validation logic to be more lenient
   - Added checks for different scope attribute names

3. **Current Debugging Code**
```python
# In app/auth/provider.py
async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
    print("=== Authorization Request Received ===")
    print(f"Client ID: {client.client_id}")
    print(f"Redirect URI: {params.redirect_uri}")
    print(f"Requested Scope: {params.scope}")
    print(f"Requested Scopes (parsed): {params.scopes if hasattr(params, 'scopes') else 'No scopes attribute'}")
    print(f"State: {params.state}")
    print(f"Client object type: {type(client)}")
    print(f"Client dir: {dir(client)}")
    print(f"Client scopes: {client.scopes if hasattr(client, 'scopes') else 'No scopes attribute'}")
    print(f"Client allowed_scopes: {client.allowed_scopes if hasattr(client, 'allowed_scopes') else 'No allowed_scopes attribute'}")
```

### Next Debugging Steps

1. **Add More Detailed Logging**
   - Add logging in the MCP server's OAuth provider initialization
   - Log the exact scope comparison logic
   - Track scope transformation at each step

2. **Check Configuration**
   - Verify `AuthSettings` configuration in `main.py`
   - Check scope validation in `OAuthAuthorizationServerProvider`
   - Confirm scope parsing in request handling

3. **Test with Different Scopes**
   - Try with single scope: `memories:read`
   - Test with different scope combinations
   - Verify scope order matters

4. **Debug Client Request**
   - Add logging in Django client's OAuth flow
   - Verify exact scope string being sent
   - Check encoding of scope parameter

### Debugging Commands

1. **Check Client Registration**
```bash
docker-compose exec app python -c "
from app.models.oauth import OAuthClient
from app.database import get_db
import asyncio

async def check_client():
    async for db in get_db():
        result = await db.execute(select(OAuthClient))
        clients = result.scalars().all()
        for client in clients:
            print(f'Client ID: {client.client_id}')
            print(f'Scopes: {client.allowed_scopes}')
            print(f'Redirect URIs: {client.redirect_uris}')

asyncio.run(check_client())
"
```

2. **Test Authorization Flow**
```bash
docker-compose exec app python -c "
from app.auth.provider import PicardOAuthProvider
from app.models.oauth import OAuthClientInformationFull, AuthorizationParams
import asyncio

async def test_authorize():
    provider = PicardOAuthProvider()
    client = OAuthClientInformationFull(
        client_id="picard_client",
        client_secret="picard_secret",
        redirect_uris=["http://localhost:8000/oauth/callback"],
        scopes=["memories:read", "memories:write"]
    )
    params = AuthorizationParams(
        redirect_uri="http://localhost:8000/oauth/callback",
        scope="memories:read memories:write",
        state="test_state",
        code_challenge="test_challenge",
        code_challenge_method="S256"
    )
    try:
        result = await provider.authorize(client, params)
        print(f"Authorization successful: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")

asyncio.run(test_authorize())
"
```

### Known Working Points

1. **Client Registration**
   - Successfully registers with MCP server
   - Correct client ID and secret stored
   - Redirect URI matches configuration

2. **Database Storage**
   - Client information stored correctly
   - Scopes properly saved in database
   - Redirect URIs validated

3. **Basic OAuth Flow**
   - Authorization endpoint accessible
   - Redirects working
   - State parameter preserved

### Next Investigation Areas

1. **Scope Comparison Logic**
   - Investigate how scopes are compared in `OAuthAuthorizationServerProvider`
   - Check for case sensitivity issues
   - Verify scope parsing in request handling

2. **Client Object Handling**
   - Track how `OAuthClientInformationFull` is created
   - Verify scope attribute access
   - Check for attribute name mismatches

3. **Configuration Validation**
   - Review `AuthSettings` in `main.py`
   - Verify scope validation rules
   - Check for conflicting configurations

## Additional Resources

### OAuth Documentation
- OAuth 2.0 Authorization Code Flow: https://tools.ietf.org/html/rfc6749
- PKCE Specification: https://tools.ietf.org/html/rfc7636
- MCP OAuth Implementation: https://github.com/mcp-protocol/mcp-python

### Error Reference
- `invalid_scope`: The requested scope is not valid, not granted by the resource owner, or not supported by the authorization server.
