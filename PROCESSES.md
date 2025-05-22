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
---