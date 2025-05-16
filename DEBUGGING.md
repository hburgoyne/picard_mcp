# OAuth Debugging Guide

This guide provides detailed steps and information for debugging OAuth issues in the Picard MCP server implementation.

## Resolved Issues

1. **Scope Validation Error**
   - Fixed scope handling between string and list formats
   - Added proper scope conversion in token response
   - Resolved undefined variable errors

2. **Token Response Format**
   - Fixed token response structure to match MCP server expectations
   - Added proper error handling for token responses
   - Resolved Pydantic validation issues with scope handling

## Current Issues

### 1. AccessToken Validation Error

#### Error Details
```
ValidationError: 1 validation error for AccessToken
client_id
  Input should be a valid string [type=string_type, input_value=1, input_type=int]
```

#### Error Context
- Occurs when accessing protected endpoints like `/tools/memories` and `/tools/submit_memory`
- Happens during token validation in authentication middleware
- The client_id is being passed as an integer when it should be a string

#### Next Debugging Steps
1. **Check Token Decoding Logic**
   - Verify how JWT tokens are decoded in `load_access_token`
   - Add logging to track client_id type during token validation
   - Ensure client_id is properly converted to string before creating AccessToken

2. **Review AccessToken Model**
   - Confirm client_id field type in AccessToken model
   - Check for type conversion issues
   - Add validation for client_id format

3. **Test Token Structure**
   - Verify token payload structure
   - Check if client_id is being encoded correctly
   - Test with different client_id formats

### 2. Authentication Flow

#### Working Components
1. **OAuth Flow**
   - Client registration working
   - Authorization code exchange successful
   - Token exchange with proper scope handling
   - PKCE implementation verified

2. **Scope Handling**
   - Scope validation working
   - Proper scope conversion between string and list
   - Correct scope comparison logic

#### Next Focus Areas
1. **Token Validation**
   - Fix client_id type conversion
   - Ensure consistent token payload structure
   - Add proper error handling for token validation

2. **API Endpoints**
   - Test protected endpoints with valid tokens
   - Verify scope requirements for each endpoint
   - Add proper error responses for invalid tokens

### Debugging Commands

1. **Check Token Structure**
```bash
docker-compose exec app python -c "
from app.auth.provider import PicardOAuthProvider
import asyncio

async def test_token_validation():
    provider = PicardOAuthProvider()
    try:
        # Add your test token here
        token = 'your_test_token'
        auth_info = await provider.load_access_token(token)
        print(f'Authentication Info: {auth_info}')
    except Exception as e:
        print(f'Error: {str(e)}')

asyncio.run(test_token_validation())
"
```

2. **Check Client Information**
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
            print(f'Client Type: {type(client.client_id)}')
            print(f'Scopes: {client.allowed_scopes}')

asyncio.run(check_client())
"
```

## Debugging Strategy

1. **Focus on Token Validation**
   - Prioritize fixing the AccessToken validation error
   - Add detailed logging in token validation flow
   - Verify token payload structure

2. **Test Protected Endpoints**
   - Test each protected endpoint with valid tokens
   - Verify scope requirements
   - Add proper error handling

3. **Maintain Working Components**
   - Keep OAuth flow working
   - Maintain scope validation
   - Preserve PKCE implementation

## Additional Resources

### OAuth Documentation
- OAuth 2.0 Authorization Code Flow: https://tools.ietf.org/html/rfc6749
- PKCE Specification: https://tools.ietf.org/html/rfc7636
- MCP OAuth Implementation: https://github.com/mcp-protocol/mcp-python

### Error Reference
- `invalid_scope`: The requested scope is not valid, not granted by the resource owner, or not supported by the authorization server.
