#!/usr/bin/env python3
"""
Test script to verify Render deployment is working correctly.
Run this after deployment to check all services.
"""
import requests
import sys
import time
from urllib.parse import urljoin

def test_service_health(base_url, service_name, health_path="/health"):
    """Test if a service is healthy."""
    url = urljoin(base_url, health_path)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(f"❌ {service_name} returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ {service_name} connection failed: {e}")
        return False

def test_oauth_endpoints(mcp_base_url):
    """Test basic OAuth endpoints are available."""
    try:
        # Test OAuth discovery
        response = requests.get(f"{mcp_base_url}/api/oauth/.well-known/oauth-authorization-server", timeout=10)
        if response.status_code == 200:
            print("✅ OAuth discovery endpoint working")
            return True
        else:
            print(f"❌ OAuth discovery failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ OAuth endpoint test failed: {e}")
        return False

def test_django_pages(django_base_url):
    """Test basic Django pages are accessible."""
    pages_to_test = [
        ("/", "Home page"),
        ("/login/", "Login page"),
        ("/register/", "Register page"),
    ]
    
    all_passed = True
    for path, description in pages_to_test:
        try:
            response = requests.get(f"{django_base_url}{path}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description} accessible")
            else:
                print(f"❌ {description} returned status {response.status_code}")
                all_passed = False
        except requests.RequestException as e:
            print(f"❌ {description} failed: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main test function."""
    print("🚀 Testing Render deployment...\n")
    
    # Service URLs (update these to match your Render service names)
    mcp_server_url = "https://picard-mcp-server.onrender.com"
    django_client_url = "https://picard-django-client.onrender.com"
    
    # Test service health
    print("Testing service health...")
    mcp_healthy = test_service_health(mcp_server_url, "MCP Server")
    django_healthy = test_service_health(django_client_url, "Django Client", "/health/")
    
    print()
    
    # Test OAuth endpoints
    if mcp_healthy:
        print("Testing OAuth endpoints...")
        oauth_working = test_oauth_endpoints(mcp_server_url)
        print()
    else:
        oauth_working = False
    
    # Test Django pages
    if django_healthy:
        print("Testing Django pages...")
        django_pages_working = test_django_pages(django_client_url)
        print()
    else:
        django_pages_working = False
    
    # Summary
    print("📊 Test Summary:")
    print(f"  MCP Server Health: {'✅' if mcp_healthy else '❌'}")
    print(f"  Django Client Health: {'✅' if django_healthy else '❌'}")
    print(f"  OAuth Endpoints: {'✅' if oauth_working else '❌'}")
    print(f"  Django Pages: {'✅' if django_pages_working else '❌'}")
    
    if all([mcp_healthy, django_healthy, oauth_working, django_pages_working]):
        print("\n🎉 All tests passed! Your deployment is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the logs and troubleshoot.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
