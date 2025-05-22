### Document Purpose
**PROCESSES.md:** Some usefull processes to document
- Useful processes and instructions for different workflows while developing, testing, maintaining the platform.
---

## Important Commands:

Rebuild Docker containers
```
docker-compose down --remove-orphans && docker image prune -f && docker-compose up --build -d
```

Run Django tests in Docker container
```
docker-compose exec django_client python manage.py test
```

Run MCP server tests in Docker container
```
docker-compose exec mcp_server pytest -xvs
```

---

Create new branch, then back to main (used to create 'deploy' branch):
```
git checkout main
git checkout -b deploy
git push -u origin deploy
git checkout main
```

Then merge 'main' into 'deploy' to deploy recent developments to Render:
```
git checkout deploy
git merge main
git push origin deploy
git checkout main
```

---

## Testing OAuth Endpoints Manually

### Register a new OAuth client

```bash
curl -X POST "http://localhost:8001/api/oauth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["http://localhost:8000/callback"],
    "scopes": ["memories:read", "memories:write"],
    "is_confidential": true
  }'
```

### Test the authorization endpoint

```bash
# Replace CLIENT_ID with the client_id from the registration response
open "http://localhost:8001/api/oauth/authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=http://localhost:8000/callback&scope=memories:read&state=test_state"
```

### Exchange authorization code for tokens

```bash
# Replace CODE with the code from the redirect URL
# Replace CLIENT_ID and CLIENT_SECRET with the values from registration
curl -X POST "http://localhost:8001/api/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=CODE&redirect_uri=http://localhost:8000/callback&client_id=CLIENT_ID&client_secret=CLIENT_SECRET"
```

---

## MCP Server Administration

### Creating an Admin User

Before you can use the admin endpoints, you need to create an admin user:

```bash
# Create an admin user with default credentials
docker-compose exec mcp_server python scripts/create_admin_user.py
```

This will create an admin user with the following default credentials:
- Username: admin
- Password: adminpassword
- Email: admin@example.com

You can customize these credentials by setting the following environment variables in your .env file:
```
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
ADMIN_EMAIL=your_email@example.com
```

## OAuth Client Registration and Management

### Register a new OAuth client for Django

To register a new OAuth client for the Django application, run the following command:

```bash
docker-compose exec django_client python register_oauth_client.py
```

This will register a new OAuth client with the MCP server using admin authentication and update the Django client's `.env` file with the new client credentials.

**Note**: This script requires admin credentials to access the protected registration endpoint. The script will use the admin credentials from the environment variables `ADMIN_USERNAME` and `ADMIN_PASSWORD`. If these are not set, it will use the default credentials (admin/adminpassword).

### Update an existing OAuth client

If you need to update an existing client (e.g., to change redirect URIs or scopes):

```bash
# From the django_client directory
docker-compose exec django_client python register_oauth_client.py --update --client-id YOUR_CLIENT_ID
```

Where `YOUR_CLIENT_ID` is the UUID of the client you want to update.

### When to update OAuth client credentials

You may need to update OAuth client credentials in the following scenarios:

1. **Changing redirect URIs**: If you change the domain or path of your callback URL
2. **Modifying scopes**: If you need to add or remove permissions
3. **Security concerns**: If you suspect the client credentials have been compromised
4. **Deployment changes**: When moving from development to production environments

### Managing OAuth clients via Admin API

The MCP server provides admin endpoints for managing OAuth clients. These endpoints require HTTP Basic Authentication with your admin credentials:

```bash
# Register a new client
curl -X POST "http://localhost:8001/api/admin/clients/register" \
  -u "admin:adminpassword" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "New Client",
    "redirect_uris": ["http://localhost:8000/callback"],
    "scopes": ["memories:read", "memories:write"],
    "is_confidential": true
  }'

# List all registered clients
curl -X GET "http://localhost:8001/api/admin/clients" \
  -u "admin:adminpassword"

# Get details for a specific client
curl -X GET "http://localhost:8001/api/admin/clients/CLIENT_ID" \
  -u "admin:adminpassword"

# Update a client
curl -X PUT "http://localhost:8001/api/admin/clients/CLIENT_ID" \
  -u "admin:adminpassword" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Updated Client Name",
    "redirect_uris": ["http://localhost:8000/new-callback"],
    "scopes": ["memories:read", "memories:write"],
    "is_confidential": true
  }'

# Delete a client
curl -X DELETE "http://localhost:8001/api/admin/clients/CLIENT_ID" \
  -u "admin:adminpassword"
```

Replace `admin:adminpassword` with your actual admin credentials if you've customized them.

---