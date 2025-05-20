#!/usr/bin/env python
"""
Comprehensive test suite for the Django client.
Tests integration with the MCP server, including OAuth flow and memory management.
"""
import sys
import os
import json
import asyncio
import logging
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, Any, List, Optional, Tuple

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("django_client_tests")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

class DjangoClientTest:
    """Test suite for Django client integration with MCP server"""
    
    def __init__(self, base_url: str = None):
        """Initialize test suite with base URL"""
        # Django client URL
        self.base_url = base_url or "http://localhost:8000"
        
        # MCP server URL (for direct comparison)
        self.mcp_server_url = "http://localhost:8001"
        
        # Test results
        self.results = {
            "oauth_flow": {},
            "memory_management": {},
            "user_interface": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
        
        # Session cookies
        self.cookies = {}
        
        logger.info(f"Initialized Django client test suite with base URL: {self.base_url}")
        logger.info(f"MCP server URL: {self.mcp_server_url}")
    
    async def run_all_tests(self):
        """Run all tests in the test suite"""
        logger.info("Starting Django client test suite")
        
        # Test user interface
        await self.test_user_interface()
        
        # Test OAuth flow
        await self.test_oauth_flow()
        
        # Test memory management (if OAuth flow succeeded)
        if self.cookies:
            await self.test_memory_management()
        else:
            logger.error("Skipping memory management tests due to OAuth flow failure")
            
        # Print test results
        self.print_results()
        
        return self.results
    
    def print_results(self):
        """Print test results in a readable format"""
        logger.info("=" * 50)
        logger.info("DJANGO CLIENT TEST RESULTS")
        logger.info("=" * 50)
        logger.info(f"Total tests: {self.results['total_tests']}")
        logger.info(f"Passed tests: {self.results['passed_tests']}")
        logger.info(f"Failed tests: {self.results['failed_tests']}")
        logger.info("=" * 50)
        
        # Print user interface results
        logger.info("User Interface Tests:")
        for test_name, result in self.results["user_interface"].items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            logger.info(f"  {test_name}: {status}")
            if not result["passed"]:
                logger.info(f"    Error: {result['error']}")
        
        # Print OAuth flow results
        logger.info("OAuth Flow Tests:")
        for test_name, result in self.results["oauth_flow"].items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            logger.info(f"  {test_name}: {status}")
            if not result["passed"]:
                logger.info(f"    Error: {result['error']}")
        
        # Print memory management results
        logger.info("Memory Management Tests:")
        for test_name, result in self.results["memory_management"].items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            logger.info(f"  {test_name}: {status}")
            if not result["passed"]:
                logger.info(f"    Error: {result['error']}")
    
    def record_test_result(self, category: str, test_name: str, passed: bool, error: str = None, data: Any = None):
        """Record test result"""
        self.results[category][test_name] = {
            "passed": passed,
            "error": error,
            "data": data
        }
        
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
        else:
            self.results["failed_tests"] += 1
            logger.error(f"Test '{test_name}' failed: {error}")
    
    async def test_user_interface(self):
        """Test Django client user interface"""
        logger.info("Testing Django client user interface")
        
        # Test home page
        await self.test_home_page()
        
        # Test login page
        await self.test_login_page()
        
        # Test memory page (unauthenticated)
        await self.test_memory_page_unauthenticated()
    
    async def test_home_page(self):
        """Test home page"""
        logger.info("Testing home page")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                
                # Check if the request succeeded
                if response.status_code == 200:
                    # Check if the page contains expected content
                    content = response.text
                    if "Welcome to Picard MCP" in content:
                        self.record_test_result("user_interface", "home_page", True)
                    else:
                        self.record_test_result(
                            "user_interface", 
                            "home_page", 
                            False, 
                            error="Home page does not contain expected content"
                        )
                else:
                    self.record_test_result(
                        "user_interface", 
                        "home_page", 
                        False, 
                        error=f"Home page request failed: {response.status_code}"
                    )
        except Exception as e:
            self.record_test_result("user_interface", "home_page", False, error=str(e))
    
    async def test_login_page(self):
        """Test login page"""
        logger.info("Testing login page")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/login/")
                
                # Check if the request succeeded
                if response.status_code == 200:
                    # Check if the page contains expected content
                    content = response.text
                    if "Login" in content and "Connect with MCP" in content:
                        self.record_test_result("user_interface", "login_page", True)
                    else:
                        self.record_test_result(
                            "user_interface", 
                            "login_page", 
                            False, 
                            error="Login page does not contain expected content"
                        )
                else:
                    self.record_test_result(
                        "user_interface", 
                        "login_page", 
                        False, 
                        error=f"Login page request failed: {response.status_code}"
                    )
        except Exception as e:
            self.record_test_result("user_interface", "login_page", False, error=str(e))
    
    async def test_memory_page_unauthenticated(self):
        """Test memory page when unauthenticated"""
        logger.info("Testing memory page (unauthenticated)")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/memories/")
                
                # Check if we get redirected to login page
                if response.status_code == 302 and "/login/" in response.headers.get("location", ""):
                    self.record_test_result("user_interface", "memory_page_unauthenticated", True)
                elif response.status_code == 200 and "Please login" in response.text:
                    # Some implementations might show a login message instead of redirecting
                    self.record_test_result("user_interface", "memory_page_unauthenticated", True)
                else:
                    self.record_test_result(
                        "user_interface", 
                        "memory_page_unauthenticated", 
                        False, 
                        error=f"Memory page did not redirect to login: {response.status_code}"
                    )
        except Exception as e:
            self.record_test_result("user_interface", "memory_page_unauthenticated", False, error=str(e))
    
    async def test_oauth_flow(self):
        """Test OAuth flow in Django client"""
        logger.info("Testing OAuth flow in Django client")
        
        # Test login initiation
        auth_url = await self.test_login_initiation()
        
        # Test authorization callback (if login initiation succeeded)
        if auth_url:
            await self.test_authorization_callback(auth_url)
        else:
            logger.error("Skipping authorization callback test due to login initiation failure")
    
    async def test_login_initiation(self) -> Optional[str]:
        """Test login initiation"""
        logger.info("Testing login initiation")
        
        try:
            async with httpx.AsyncClient(follow_redirects=False) as client:
                response = await client.get(f"{self.base_url}/oauth/login/")
                
                # Check if we get redirected to the MCP server's authorization endpoint
                if response.status_code == 302:
                    redirect_url = response.headers.get("location", "")
                    if "/oauth/authorize" in redirect_url:
                        logger.info(f"Redirected to authorization URL: {redirect_url}")
                        self.record_test_result("oauth_flow", "login_initiation", True, data={"auth_url": redirect_url})
                        return redirect_url
                    else:
                        self.record_test_result(
                            "oauth_flow", 
                            "login_initiation", 
                            False, 
                            error=f"Unexpected redirect URL: {redirect_url}"
                        )
                else:
                    self.record_test_result(
                        "oauth_flow", 
                        "login_initiation", 
                        False, 
                        error=f"Login initiation failed: {response.status_code} {response.text}"
                    )
        except Exception as e:
            self.record_test_result("oauth_flow", "login_initiation", False, error=str(e))
        
        return None
    
    async def test_authorization_callback(self, auth_url: str):
        """Test authorization callback"""
        logger.info("Testing authorization callback")
        
        try:
            # Simulate the full OAuth flow
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # Step 1: Follow the authorization URL (this should redirect to the callback URL)
                response = await client.get(auth_url)
                
                # Step 2: Check if we got redirected back to the Django client
                final_url = str(response.url)
                if self.base_url in final_url:
                    # Check if we're logged in (by checking cookies or content)
                    self.cookies = client.cookies
                    if self.cookies:
                        logger.info(f"Received {len(self.cookies)} cookies")
                        self.record_test_result("oauth_flow", "authorization_callback", True, data={"cookies": str(self.cookies)})
                    elif "Welcome" in response.text or "Dashboard" in response.text:
                        # If we can't check cookies, check for logged-in content
                        self.record_test_result("oauth_flow", "authorization_callback", True)
                    else:
                        self.record_test_result(
                            "oauth_flow", 
                            "authorization_callback", 
                            False, 
                            error="No cookies or logged-in content found"
                        )
                else:
                    self.record_test_result(
                        "oauth_flow", 
                        "authorization_callback", 
                        False, 
                        error=f"Not redirected back to Django client: {final_url}"
                    )
        except Exception as e:
            self.record_test_result("oauth_flow", "authorization_callback", False, error=str(e))
    
    async def test_memory_management(self):
        """Test memory management in Django client"""
        logger.info("Testing memory management in Django client")
        
        # Test memory page (authenticated)
        await self.test_memory_page_authenticated()
        
        # Test memory creation
        await self.test_create_memory()
        
        # Test memory permissions
        await self.test_memory_permissions()
    
    async def test_memory_page_authenticated(self):
        """Test memory page when authenticated"""
        logger.info("Testing memory page (authenticated)")
        
        try:
            async with httpx.AsyncClient(cookies=self.cookies) as client:
                response = await client.get(f"{self.base_url}/memories/")
                
                # Check if the request succeeded
                if response.status_code == 200:
                    # Check if the page contains expected content
                    content = response.text
                    if "My Memories" in content or "Memories" in content:
                        self.record_test_result("memory_management", "memory_page_authenticated", True)
                    else:
                        self.record_test_result(
                            "memory_management", 
                            "memory_page_authenticated", 
                            False, 
                            error="Memory page does not contain expected content"
                        )
                else:
                    self.record_test_result(
                        "memory_management", 
                        "memory_page_authenticated", 
                        False, 
                        error=f"Memory page request failed: {response.status_code}"
                    )
        except Exception as e:
            self.record_test_result("memory_management", "memory_page_authenticated", False, error=str(e))
    
    async def test_create_memory(self):
        """Test memory creation"""
        logger.info("Testing memory creation")
        
        try:
            async with httpx.AsyncClient(cookies=self.cookies) as client:
                # Get CSRF token if needed
                csrf_token = None
                form_page = await client.get(f"{self.base_url}/memories/create/")
                if form_page.status_code == 200:
                    # Extract CSRF token from the form
                    content = form_page.text
                    csrf_start = content.find('name="csrfmiddlewaretoken" value="')
                    if csrf_start != -1:
                        csrf_start += len('name="csrfmiddlewaretoken" value="')
                        csrf_end = content.find('"', csrf_start)
                        csrf_token = content[csrf_start:csrf_end]
                
                # Prepare form data
                form_data = {
                    "text": "This is a test memory created by the Django client test suite",
                    "permission": "private"
                }
                
                # Add CSRF token if found
                if csrf_token:
                    form_data["csrfmiddlewaretoken"] = csrf_token
                
                # Submit the form
                response = await client.post(
                    f"{self.base_url}/memories/create/",
                    data=form_data,
                    headers={"Referer": f"{self.base_url}/memories/create/"}
                )
                
                # Check if the request succeeded (redirect to memories list)
                if response.status_code == 302 and "/memories/" in response.headers.get("location", ""):
                    self.record_test_result("memory_management", "create_memory", True)
                elif response.status_code == 200 and "successfully created" in response.text:
                    # Some implementations might show a success message instead of redirecting
                    self.record_test_result("memory_management", "create_memory", True)
                else:
                    self.record_test_result(
                        "memory_management", 
                        "create_memory", 
                        False, 
                        error=f"Memory creation failed: {response.status_code} {response.text}"
                    )
        except Exception as e:
            self.record_test_result("memory_management", "create_memory", False, error=str(e))
    
    async def test_memory_permissions(self):
        """Test memory permissions management"""
        logger.info("Testing memory permissions management")
        
        try:
            async with httpx.AsyncClient(cookies=self.cookies) as client:
                # First, get the memories list to find a memory ID
                response = await client.get(f"{self.base_url}/memories/")
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Look for a memory ID in the page
                    memory_id = None
                    id_start = content.find('data-memory-id="')
                    if id_start != -1:
                        id_start += len('data-memory-id="')
                        id_end = content.find('"', id_start)
                        memory_id = content[id_start:id_end]
                    
                    # If we found a memory ID, test changing its permissions
                    if memory_id:
                        logger.info(f"Found memory ID: {memory_id}")
                        
                        # Get CSRF token if needed
                        csrf_token = None
                        csrf_start = content.find('name="csrfmiddlewaretoken" value="')
                        if csrf_start != -1:
                            csrf_start += len('name="csrfmiddlewaretoken" value="')
                            csrf_end = content.find('"', csrf_start)
                            csrf_token = content[csrf_start:csrf_end]
                        
                        # Prepare form data
                        form_data = {
                            "memory_id": memory_id,
                            "permission": "public"
                        }
                        
                        # Add CSRF token if found
                        if csrf_token:
                            form_data["csrfmiddlewaretoken"] = csrf_token
                        
                        # Submit the form
                        permission_response = await client.post(
                            f"{self.base_url}/memories/{memory_id}/permissions/",
                            data=form_data,
                            headers={"Referer": f"{self.base_url}/memories/"}
                        )
                        
                        # Check if the request succeeded
                        if permission_response.status_code == 302 or permission_response.status_code == 200:
                            self.record_test_result("memory_management", "memory_permissions", True)
                        else:
                            self.record_test_result(
                                "memory_management", 
                                "memory_permissions", 
                                False, 
                                error=f"Permission change failed: {permission_response.status_code}"
                            )
                    else:
                        self.record_test_result(
                            "memory_management", 
                            "memory_permissions", 
                            False, 
                            error="No memory ID found in the memories list"
                        )
                else:
                    self.record_test_result(
                        "memory_management", 
                        "memory_permissions", 
                        False, 
                        error=f"Failed to get memories list: {response.status_code}"
                    )
        except Exception as e:
            self.record_test_result("memory_management", "memory_permissions", False, error=str(e))

async def main():
    """Run the test suite"""
    # Create test suite
    test_suite = DjangoClientTest()
    
    # Run all tests
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
