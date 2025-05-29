# Render Deployment Guide

This guide will help you deploy your Picard MCP system to Render using the Blueprint feature.

## Prerequisites

1. A Render account
2. Your GitHub repository with the Picard MCP code
3. An OpenAI API key (for LLM features)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository contains:
- ✅ `render.yml` (Blueprint configuration)
- ✅ `mcp_server/scripts/startup_tasks.py` (Database setup and admin user creation)
- ✅ `django_client/scripts/render_startup.py` (Django migrations and OAuth registration)

### 2. Deploy to Render

1. **Connect Repository**: 
   - Go to your Render dashboard
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing your Picard MCP code

2. **Configure Environment Variables**:
   The following environment variables will be automatically configured via the Blueprint:
   - Database credentials (auto-generated)
   - Service URLs
   - Admin credentials (auto-generated)
   
   **Manual Configuration Required**:
   - `OPENAI_API_KEY`: Set this in the MCP server service environment variables

3. **Deploy**:
   - Click "Apply" to deploy the Blueprint
   - Render will create:
     - 2 PostgreSQL databases (one for MCP server, one for Django client)
     - MCP server web service
     - Django client web service

### 3. Post-Deployment

1. **Verify Services**:
   - MCP Server: `https://picard-mcp-server.onrender.com/health`
   - Django Client: `https://picard-django-client.onrender.com/health/`

2. **Admin Access**:
   - The admin password is auto-generated
   - Check the MCP server environment variables for `ADMIN_PASSWORD`
   - Admin username: `admin`

3. **OAuth Registration**:
   - OAuth client registration happens automatically during Django startup
   - If it fails, check the Django client logs

## Database Migrations

### How Migrations Work on Render

**MCP Server**:
- Migrations run during the pre-deploy phase via `startup_tasks.py`
- Uses Alembic for database schema management
- Creates admin user automatically

**Django Client**:
- Migrations run during build phase via `render_startup.py`
- Uses Django's built-in migration system
- Registers OAuth client with MCP server automatically

### Manual Migration Commands (if needed)

If you need to run migrations manually:

**MCP Server**:
```bash
# From Render shell (if available on paid plans)
cd mcp_server && alembic upgrade head
```

**Django Client**:
```bash
# From Render shell (if available on paid plans)
cd django_client && python manage.py migrate
```

### Creating New Migrations

**MCP Server**:
```bash
# Local development
cd mcp_server
alembic revision --autogenerate -m "Description of changes"
```

**Django Client**:
```bash
# Local development
cd django_client
python manage.py makemigrations
```

## OAuth Client Registration

### Automatic Registration

The Django client automatically registers itself with the MCP server during startup:

1. **During Build**: `render_startup.py` runs and:
   - Waits for the MCP server to be available
   - Uses admin credentials to register an OAuth client
   - Sets the client credentials in environment variables

2. **Process**:
   - Creates a confidential OAuth client
   - Sets redirect URI to `https://picard-django-client.onrender.com/oauth/callback`
   - Configures scopes: `memories:read memories:write`

### Manual Registration (if automatic fails)

If automatic registration fails, you can register manually:

1. **Get Admin Credentials**:
   - Check MCP server environment variables for `ADMIN_PASSWORD`
   - Username is `admin`

2. **Register Client**:
```bash
curl -X POST "https://picard-mcp-server.onrender.com/api/admin/clients/register" \
  -H "Authorization: Basic $(echo -n 'admin:YOUR_ADMIN_PASSWORD' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Picard MCP Django Client (Render)",
    "redirect_uris": ["https://picard-django-client.onrender.com/oauth/callback"],
    "scopes": ["memories:read", "memories:write"],
    "is_confidential": true
  }'
```

3. **Update Django Environment**:
   - Set `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` in Django service environment variables

## Free Tier Considerations

### Limitations:
- Services sleep after 15 minutes of inactivity
- No persistent storage (except databases)
- Limited to 512MB RAM per service
- No shell access for free tier

### Workarounds:
- ✅ All startup tasks are automated in build/pre-deploy phases
- ✅ Database migrations handled during deployment
- ✅ OAuth registration handled during startup
- ✅ No manual shell commands required

## Testing Render Configuration Locally

Use the production-like Docker Compose file to test your Render configuration:

```bash
# Test production-like environment locally
docker-compose -f docker-compose.prod.yml up --build

# Clean up
docker-compose -f docker-compose.prod.yml down --volumes
```

This simulates the Render environment with:
- Production environment variables
- Gunicorn server (like Render)
- Automated startup scripts
- Separate PostgreSQL instances

## Troubleshooting

### Common Issues:

1. **Service Won't Start**:
   - Check service logs in Render dashboard
   - Verify environment variables are set correctly
   - Ensure database is healthy

2. **Database Connection Issues**:
   - Verify database credentials in environment variables
   - Check if pgvector extension is installed (MCP server)

3. **OAuth Registration Fails**:
   - Check if MCP server is running and healthy
   - Verify admin credentials
   - Check Django client logs for error details

4. **Static Files Not Loading (Django)**:
   - Ensure `collectstatic` runs during build
   - Check `STATIC_ROOT` and `STATIC_URL` settings

### Debugging Steps:

1. **Check Service Health**:
   ```bash
   curl https://picard-mcp-server.onrender.com/health
   curl https://picard-django-client.onrender.com/health/
   ```

2. **Review Logs**:
   - Go to Render dashboard
   - Select your service
   - View "Logs" tab for detailed error information

3. **Verify Environment Variables**:
   - Check that all required variables are set
   - Ensure database URLs are correctly formatted

## Updating Your Deployment

1. **Code Changes**:
   - Push changes to your GitHub repository
   - Render will automatically redeploy

2. **Database Schema Changes**:
   - Create migrations locally first
   - Commit migration files to repository
   - Deploy - migrations run automatically

3. **Environment Variable Changes**:
   - Update via Render dashboard
   - Restart services if needed

## Security Notes

- Admin passwords are auto-generated and stored securely
- OAuth client secrets are auto-generated
- All services use HTTPS in production
- Database connections are encrypted
- CSRF protection enabled for Django

## Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review Render documentation
3. Check service logs in Render dashboard
4. Test locally with `docker-compose.prod.yml`
