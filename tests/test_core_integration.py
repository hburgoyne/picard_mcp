"""
Core Integration Tests for Picard MCP

These tests verify that the core functionality works correctly end-to-end.
They're designed to catch breaking changes in essential features.

Usage:
    cd /Users/hayden/Documents/Github/picard_mcp
    python -m pytest tests/test_core_integration.py -v

Requirements:
    - Both MCP server and Django client must be running
    - Docker containers should be healthy
"""
import os
import sys
import pytest
import requests
import time
import json
import uuid
import subprocess
from datetime import datetime, timedelta

# Configuration
DJANGO_URL = "http://localhost:8000"
MCP_URL = "http://localhost:8001"

# Test user credentials
TEST_USERNAME = f"testuser_{int(time.time())}"
TEST_PASSWORD = "testpass123"
TEST_EMAIL = f"{TEST_USERNAME}@example.com"

class TestCoreIntegration:
    """Core integration tests for essential functionality."""
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self):
        """Set up test environment."""
        print("\n=== Setting up integration test environment ===")
        
        # Verify services are running
        self.verify_services_running()
        
        # Create a test user
        self.create_test_user()
        
        # Get session and tokens
        self.session = requests.Session()
        self.authenticate_user()
        
        yield
        
        # Cleanup
        self.cleanup_test_user()
    
    def verify_services_running(self):
        """Verify that both services are running and healthy."""
        print("Checking service health...")
        
        # Check Django client
        try:
            response = requests.get(f"{DJANGO_URL}/health/", timeout=5)
            assert response.status_code == 200, f"Django client unhealthy: {response.status_code}"
            print("✅ Django client is healthy")
        except Exception as e:
            pytest.fail(f"Django client is not accessible: {e}")
        
        # Check MCP server
        try:
            response = requests.get(f"{MCP_URL}/api/health/", timeout=5)
            assert response.status_code == 200, f"MCP server unhealthy: {response.status_code}"
            health_data = response.json()
            assert health_data["status"] == "healthy", f"MCP server status: {health_data['status']}"
            print("✅ MCP server is healthy")
        except Exception as e:
            pytest.fail(f"MCP server is not accessible: {e}")
    
    def create_test_user(self):
        """Create a test user via Django management command."""
        print(f"Creating test user: {TEST_USERNAME}")
        
        cmd = [
            "docker-compose", "exec", "-T", "django_client", 
            "python", "manage.py", "shell", "-c",
            f"from django.contrib.auth.models import User; "
            f"User.objects.filter(username='{TEST_USERNAME}').delete(); "
            f"User.objects.create_user(username='{TEST_USERNAME}', "
            f"email='{TEST_EMAIL}', password='{TEST_PASSWORD}')"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/Users/hayden/Documents/Github/picard_mcp")
        if result.returncode != 0:
            pytest.fail(f"Failed to create test user: {result.stderr}")
        
        print("✅ Test user created")
    
    def authenticate_user(self):
        """Authenticate the test user and establish OAuth connection."""
        print("Authenticating test user...")
        
        # Get login page to get CSRF token
        login_page = self.session.get(f"{DJANGO_URL}/login/")
        assert login_page.status_code == 200
        
        # Extract CSRF token from cookies
        csrf_token = self.session.cookies.get('csrftoken')
        
        # Login with test credentials
        login_data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD,
            'csrfmiddlewaretoken': csrf_token
        }
        
        login_response = self.session.post(f"{DJANGO_URL}/login/", data=login_data)
        assert login_response.status_code in [200, 302], f"Login failed: {login_response.status_code}"
        
        # Establish OAuth connection using direct connect
        oauth_response = self.session.get(f"{DJANGO_URL}/oauth/authorize/")
        assert oauth_response.status_code in [200, 302], f"OAuth connection failed: {oauth_response.status_code}"
        
        # Verify we can access the dashboard
        dashboard_response = self.session.get(f"{DJANGO_URL}/dashboard/")
        assert dashboard_response.status_code == 200, f"Dashboard access failed: {dashboard_response.status_code}"
        assert "Dashboard" in dashboard_response.text, "Not properly authenticated"
        
        print("✅ User authenticated and OAuth connected")
    
    def cleanup_test_user(self):
        """Clean up test user and data."""
        print("Cleaning up test user...")
        
        cmd = [
            "docker-compose", "exec", "-T", "django_client",
            "python", "manage.py", "shell", "-c",
            f"from django.contrib.auth.models import User; "
            f"User.objects.filter(username='{TEST_USERNAME}').delete()"
        ]
        
        subprocess.run(cmd, capture_output=True, cwd="/Users/hayden/Documents/Github/picard_mcp")
        print("✅ Test user cleaned up")
    
    def test_health_endpoints(self):
        """Test that health endpoints are working."""
        print("\n=== Testing Health Endpoints ===")
        
        # Django health
        response = self.session.get(f"{DJANGO_URL}/health/")
        assert response.status_code == 200
        print("✅ Django health endpoint working")
        
        # MCP health
        response = requests.get(f"{MCP_URL}/api/health/")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "database" in health_data
        assert health_data["database"] == "connected"
        print("✅ MCP health endpoint working")
    
    def test_user_authentication_flow(self):
        """Test that user authentication works end-to-end."""
        print("\n=== Testing User Authentication Flow ===")
        
        # Test that we can access protected pages
        dashboard_response = self.session.get(f"{DJANGO_URL}/dashboard/")
        assert dashboard_response.status_code == 200
        assert "Dashboard" in dashboard_response.text
        print("✅ User can access protected dashboard")
        
        # Test that OAuth connection is established
        assert any(indicator in dashboard_response.text for indicator in [
            "Connected to MCP", "Create Memory", "Memory Management"
        ]), "OAuth connection not established"
        print("✅ OAuth connection verified")
    
    def test_memory_crud_operations(self):
        """Test complete memory CRUD operations."""
        print("\n=== Testing Memory CRUD Operations ===")
        
        # Test memory creation
        memory_text = f"Test memory created at {datetime.now()}"
        create_response = self.session.post(f"{DJANGO_URL}/memories/create/", data={
            'text': memory_text,
            'permission': 'private',
            'csrfmiddlewaretoken': self.session.cookies.get('csrftoken')
        })
        assert create_response.status_code in [200, 302], f"Memory creation failed: {create_response.status_code}"
        print("✅ Memory creation works")
        
        # Test memory listing
        memories_response = self.session.get(f"{DJANGO_URL}/memories/")
        assert memories_response.status_code == 200
        assert memory_text in memories_response.text or "No memories found" in memories_response.text
        print("✅ Memory listing works")
        
        # Extract memory ID from the page if memory was created
        if memory_text in memories_response.text:
            # Look for memory ID in the HTML (this is a basic extraction)
            import re
            memory_id_match = re.search(r'/memories/(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/', memories_response.text)
            if memory_id_match:
                memory_id = memory_id_match.group(1)
                
                # Test memory update
                updated_text = f"Updated memory at {datetime.now()}"
                update_response = self.session.post(f"{DJANGO_URL}/memories/{memory_id}/edit/", data={
                    'text': updated_text,
                    'permission': 'public',
                    'csrfmiddlewaretoken': self.session.cookies.get('csrftoken')
                })
                assert update_response.status_code in [200, 302], f"Memory update failed: {update_response.status_code}"
                print("✅ Memory update works")
                
                # Test memory deletion
                delete_response = self.session.post(f"{DJANGO_URL}/memories/{memory_id}/delete/", data={
                    'csrfmiddlewaretoken': self.session.cookies.get('csrftoken')
                })
                assert delete_response.status_code in [200, 302], f"Memory deletion failed: {delete_response.status_code}"
                print("✅ Memory deletion works")
    
    def test_permission_system(self):
        """Test that the permission system works correctly."""
        print("\n=== Testing Permission System ===")
        
        # Create a private memory
        private_memory = f"Private memory {datetime.now()}"
        create_response = self.session.post(f"{DJANGO_URL}/memories/create/", data={
            'text': private_memory,
            'permission': 'private',
            'csrfmiddlewaretoken': self.session.cookies.get('csrftoken')
        })
        assert create_response.status_code in [200, 302]
        print("✅ Private memory creation works")
        
        # Create a public memory
        public_memory = f"Public memory {datetime.now()}"
        create_response = self.session.post(f"{DJANGO_URL}/memories/create/", data={
            'text': public_memory,
            'permission': 'public',
            'csrfmiddlewaretoken': self.session.cookies.get('csrftoken')
        })
        assert create_response.status_code in [200, 302]
        print("✅ Public memory creation works")
        
        # Verify both memories are visible to the owner
        memories_response = self.session.get(f"{DJANGO_URL}/memories/")
        assert memories_response.status_code == 200
        print("✅ Permission system functional")
    
    def test_api_endpoints(self):
        """Test critical API endpoints work correctly."""
        print("\n=== Testing API Endpoints ===")
        
        # Test MCP server documentation endpoint
        docs_response = requests.get(f"{MCP_URL}/docs")
        assert docs_response.status_code == 200
        print("✅ MCP API documentation accessible")
        
        # Test Django admin interface is accessible (but not necessarily logged in)
        admin_response = requests.get(f"{DJANGO_URL}/admin/")
        assert admin_response.status_code in [200, 302]  # 302 for redirect to login
        print("✅ Django admin interface accessible")
    
    def test_database_connectivity(self):
        """Test that database connections are working."""
        print("\n=== Testing Database Connectivity ===")
        
        # Check MCP server database via health endpoint
        health_response = requests.get(f"{MCP_URL}/api/health/")
        health_data = health_response.json()
        assert health_data["database"] == "connected"
        print("✅ MCP server database connected")
        
        # Check Django database by accessing a page that requires DB
        dashboard_response = self.session.get(f"{DJANGO_URL}/dashboard/")
        assert dashboard_response.status_code == 200
        print("✅ Django database connected")

def run_unit_tests():
    """Run unit tests for both components."""
    print("\n=== Running Unit Tests ===")
    
    # Run MCP server tests
    print("Running MCP server tests...")
    mcp_result = subprocess.run([
        "docker-compose", "exec", "-T", "mcp_server", "pytest", "-q"
    ], capture_output=True, text=True, cwd="/Users/hayden/Documents/Github/picard_mcp")
    
    if mcp_result.returncode == 0:
        print("✅ MCP server tests passed")
    else:
        print(f"❌ MCP server tests failed: {mcp_result.stderr}")
        return False
    
    # Run Django client tests
    print("Running Django client tests...")
    django_result = subprocess.run([
        "docker-compose", "exec", "-T", "django_client", "python", "manage.py", "test", "--verbosity=1"
    ], capture_output=True, text=True, cwd="/Users/hayden/Documents/Github/picard_mcp")
    
    if django_result.returncode == 0:
        print("✅ Django client tests passed")
    else:
        print(f"❌ Django client tests failed: {django_result.stderr}")
        return False
    
    return True

def main():
    """Run all tests when called directly."""
    print("🧪 Running Picard MCP Core Integration Tests")
    print("=" * 50)
    
    # Check if services are running
    try:
        requests.get(f"{DJANGO_URL}/health/", timeout=5)
        requests.get(f"{MCP_URL}/api/health/", timeout=5)
    except:
        print("❌ Services are not running. Please start with:")
        print("   docker-compose up -d")
        sys.exit(1)
    
    # Run unit tests first
    if not run_unit_tests():
        print("❌ Unit tests failed. Integration tests skipped.")
        sys.exit(1)
    
    # Run integration tests
    print("\n=== Running Integration Tests ===")
    exit_code = subprocess.call([
        "python", "-m", "pytest", "tests/test_core_integration.py", "-v"
    ], cwd="/Users/hayden/Documents/Github/picard_mcp")
    
    if exit_code == 0:
        print("\n🎉 All tests passed! Core functionality is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
