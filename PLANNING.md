### Document Purpose
**PLANNING.md:** Comprehensive guide to implementing the platform
- Lists tasks and subtasks required to implement the site
- Documents if a task has been completed with a checkbox
- Describes the setup locally and on Render
---

# Picard MCP Implementation Plan (MVP)

This document outlines the step-by-step implementation plan for the Picard MCP project MVP, focusing on simplicity and essential functionality.

## Phase 1: Project Setup and Configuration

### 1.1 Environment Setup
- [x] Create project repository structure
- [x] Set up virtual environments for both MCP server and Django client
- [x] Create `.env` files with required environment variables
- [x] Set up Docker and Docker Compose configuration

### 1.2 Database Configuration
- [x] Configure PostgreSQL with pgvector extension for MCP server
- [x] Configure simple PostgreSQL for Django client
- [x] Create minimal database schemas and initial migrations

### 1.3 Docker Configuration
- [x] Create Dockerfile for MCP server
- [x] Create Dockerfile for Django client
- [x] Create docker-compose.yml for local development
- [x] Test Docker setup with basic applications

## Phase 2: MCP Server Implementation (Core Functionality)

### 2.1 Core Server Setup
- [ ] Set up FastAPI application structure
- [ ] Configure ASGI server (Uvicorn)
- [ ] Implement basic server health check endpoints
- [ ] Set up minimal logging

### 2.2 Database Models
- [ ] Implement User model
- [ ] Implement Memory model with vector storage
- [ ] Implement OAuth Client model
- [ ] Implement Token model
- [ ] Create database migrations

### 2.3 OAuth 2.0 Implementation
- [ ] Implement client registration endpoint
- [ ] Implement authorization endpoint
- [ ] Implement token exchange endpoint
- [ ] Implement token refresh endpoint
- [ ] Implement token validation middleware
- [ ] Set up basic scope-based permission system

### 2.4 Memory Management
- [ ] Implement memory creation endpoint
- [ ] Implement memory retrieval endpoints
- [ ] Implement memory update endpoint
- [ ] Implement memory deletion endpoint
- [ ] Implement permission-based access control
- [ ] Implement basic memory encryption at rest

### 2.5 Vector Embedding and Search
- [ ] Integrate OpenAI API for text embeddings
- [ ] Implement vector storage with pgvector
- [ ] Implement basic semantic search functionality

### 2.6 LLM Integration
- [ ] Implement simple persona query functionality
- [ ] Set up basic context management for LLM queries
- [ ] Implement memory-based query processing

### 2.7 API Documentation
- [ ] Set up Swagger/OpenAPI documentation
- [ ] Document essential endpoints with examples

## Phase 3: Django Client Implementation (Minimal Testbed)

### 3.1 Core Application Setup
- [ ] Set up Django project structure
- [ ] Configure settings and environment variables
- [ ] Set up URL routing
- [ ] Create simple base templates with Bootstrap

### 3.2 User Management
- [ ] Implement basic user registration
- [ ] Implement user authentication
- [ ] Implement minimal user profile

### 3.3 OAuth Client Implementation
- [ ] Implement OAuth 2.0 client with PKCE
- [ ] Create token storage in database
- [ ] Implement token refresh logic
- [ ] Set up basic error handling

### 3.4 Memory Management UI
- [ ] Create simple memory creation form
- [ ] Create basic memory listing page
- [ ] Create simple memory editing form
- [ ] Create memory deletion functionality
- [ ] Implement basic permission toggle

### 3.5 Search and Query UI
- [ ] Implement basic search form
- [ ] Create simple persona query form
- [ ] Implement basic results display

### 3.6 API Integration
- [ ] Create MCP server API client
- [ ] Implement basic error handling for API calls

## Phase 4: Testing (Essential Only)

### 4.1 MCP Server Tests
- [ ] Write basic tests for critical endpoints
- [ ] Test OAuth flow
- [ ] Test core memory operations

### 4.2 Django Client Tests
- [ ] Test OAuth client integration
- [ ] Test basic memory operations

### 4.3 End-to-End Tests
- [ ] Create simple test script for system testing
- [ ] Test OAuth flow from client to server
- [ ] Test memory creation, retrieval, and querying

## Phase 5: Deployment

### 5.1 Local Deployment with Docker
- [ ] Finalize docker-compose.yml
- [ ] Test full system with Docker Compose

### 5.2 Render Deployment
- [ ] Create render.yaml blueprint
- [ ] Configure environment variables for Render
- [ ] Deploy MCP server to Render
- [ ] Deploy Django client to Render
- [ ] Test deployed application

## Implementation Timeline

| Phase | Estimated AI Prompting Sessions | Dependencies |
|-------|-------------------|--------------|
| Phase 1: Project Setup | 2-3 prompts | None |
| Phase 2: MCP Server | 1-2 prompts | Phase 1 |
| Phase 3: Django Client | 3-5 prompts | Phase 1 |
| Phase 4: Testing | 2-3 prompts | Phases 2 & 3 |
| Phase 5: Deployment | 1-2 prompts | Phase 4 |

## Getting Started

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/picard_mcp.git
   cd picard_mcp
   ```

2. Create `.env` files for both MCP server and Django client:
   
   For MCP server (`.env` in project root):
   ```
   # PostgreSQL Configuration
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=picard_mcp
   POSTGRES_HOST=db
   POSTGRES_PORT=5432

   # MCP Server Configuration
   MCP_SERVER_NAME=Picard MCP
   MCP_SERVER_HOST=0.0.0.0
   MCP_SERVER_PORT=8000
   MCP_ISSUER_URL=http://localhost:8001

   # OAuth Configuration
   OAUTH_CLIENT_ID=550e8400-e29b-41d4-a716-446655440000
   OAUTH_CLIENT_SECRET=a_strong_random_secret_at_least_32_characters
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   ```

   For Django client (`.env` in `django_client` directory):
   ```
   # Django settings
   DEBUG=True
   DJANGO_SECRET_KEY=django-insecure-key-for-development-only

   # Database settings
   DB_NAME=django_client
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432

   # MCP Server settings
   MCP_SERVER_URL=http://localhost:8001
   MCP_SERVER_INTERNAL_URL=http://mcp_server:8000

   # OAuth settings
   OAUTH_CLIENT_ID=550e8400-e29b-41d4-a716-446655440000
   OAUTH_CLIENT_SECRET=a_strong_random_secret_at_least_32_characters
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
   OAUTH_SCOPES=memories:read memories:write
   ```

3. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Register the Django client with the MCP server:
   ```bash
   docker exec picard_mcp-django_client-1 python register_oauth_client.py
   ```

5. Access the Django client at http://localhost:8000 and the MCP server at http://localhost:8001

### Render Deployment

1. Create a `render.yaml` file in the project root:
   ```yaml
   services:
     # MCP Server service
     - type: web
       name: picard-mcp-server
       env: python
       plan: starter
       buildCommand: cd mcp_server && pip install -r requirements.txt
       startCommand: cd mcp_server && uvicorn app.main:app --host 0.0.0.0 --port $PORT
       envVars:
         - key: POSTGRES_USER
           sync: false
         - key: POSTGRES_PASSWORD
           sync: false
         - key: POSTGRES_DB
           value: picard_mcp
         - key: POSTGRES_HOST
           fromService:
             type: pserv
             name: picard-mcp-db
             property: host
         - key: POSTGRES_PORT
           value: 5432
         - key: MCP_SERVER_NAME
           value: Picard MCP
         - key: MCP_SERVER_HOST
           value: 0.0.0.0
         - key: MCP_SERVER_PORT
           value: 8000
         - key: MCP_ISSUER_URL
           fromService:
             type: web
             name: picard-mcp-server
             property: url
         - key: OAUTH_CLIENT_ID
           generateValue: true
         - key: OAUTH_CLIENT_SECRET
           generateValue: true
         - key: OAUTH_REDIRECT_URI
           fromService:
             type: web
             name: picard-mcp-client
             property: url
           suffix: /oauth/callback
         - key: OPENAI_API_KEY
           sync: false
       healthCheckPath: /health
       autoDeploy: false

     # Django Client service
     - type: web
       name: picard-mcp-client
       env: python
       plan: starter
       buildCommand: cd django_client && pip install -r requirements.txt && python manage.py migrate
       startCommand: cd django_client && gunicorn django_client.wsgi:application
       envVars:
         - key: DEBUG
           value: false
         - key: DJANGO_SECRET_KEY
           generateValue: true
         - key: DB_NAME
           value: django_client
         - key: DB_USER
           sync: false
         - key: DB_PASSWORD
           sync: false
         - key: DB_HOST
           fromService:
             type: pserv
             name: picard-mcp-client-db
             property: host
         - key: DB_PORT
           value: 5432
         - key: MCP_SERVER_URL
           fromService:
             type: web
             name: picard-mcp-server
             property: url
         - key: MCP_SERVER_INTERNAL_URL
           fromService:
             type: web
             name: picard-mcp-server
             property: url
         - key: OAUTH_CLIENT_ID
           fromService:
             type: web
             name: picard-mcp-server
             envVarKey: OAUTH_CLIENT_ID
         - key: OAUTH_CLIENT_SECRET
           fromService:
             type: web
             name: picard-mcp-server
             envVarKey: OAUTH_CLIENT_SECRET
         - key: OAUTH_REDIRECT_URI
           fromService:
             type: web
             name: picard-mcp-client
             property: url
           suffix: /oauth/callback
         - key: OAUTH_SCOPES
           value: memories:read memories:write
       healthCheckPath: /health
       autoDeploy: false

     # MCP Server Database
     - type: pserv
       name: picard-mcp-db
       env: docker
       plan: starter
       disk:
         name: data
         mountPath: /var/lib/postgresql/data
         sizeGB: 10
       image: ankane/pgvector:latest
       envVars:
         - key: POSTGRES_USER
           sync: false
         - key: POSTGRES_PASSWORD
           sync: false
         - key: POSTGRES_DB
           value: picard_mcp

     # Django Client Database
     - type: pserv
       name: picard-mcp-client-db
       env: docker
       plan: starter
       disk:
         name: data
         mountPath: /var/lib/postgresql/data
         sizeGB: 10
       image: postgres:14
       envVars:
         - key: POSTGRES_USER
           sync: false
         - key: POSTGRES_PASSWORD
           sync: false
         - key: POSTGRES_DB
           value: django_client
   ```

2. Create a Render account and connect it to your GitHub repository.

3. In the Render dashboard, click on "Blueprint" and select your repository.

4. Set the required environment variables that are marked with `sync: false`:
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `OPENAI_API_KEY`
   - `DB_USER`
   - `DB_PASSWORD`

5. Deploy the blueprint, which will create all the services defined in the `render.yaml` file.

6. After deployment, run the client registration script:
   - Go to the "Shell" tab of the Django client service in the Render dashboard
   - Run: `python register_oauth_client.py`

7. Access your deployed applications using the URLs provided in the Render dashboard.

## Next Steps

1. Complete Phase 1: Project Setup and Configuration
2. Begin implementation of MCP server core functionality
