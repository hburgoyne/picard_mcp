#!/usr/bin/env python
"""
Comprehensive test suite for the MCP server.
Tests OAuth flow and memory endpoints.
"""
import sys
import os
import json
import asyncio
import hashlib
import base64
import secrets
import logging
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, Any, List, Optional, Tuple

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_server_tests")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

class MCPServerTest:
    """Test suite for MCP server endpoints"""
    
    def __init__(self, base_url: str = None):
        """Initialize test suite with base URL"""
        # When running inside Docker, we need to use the service name as hostname
        self.base_url = base_url or "http://app:8000"
        self.client_id = settings.OAUTH_CLIENT_ID
        self.client_secret = settings.OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.OAUTH_REDIRECT_URI
        
        # Test results
        self.results = {
            "oauth_flow": {},
            "memory_endpoints": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
        
        # Access token for authenticated requests
        self.access_token = None
        
        # Test memory ID
        self.test_memory_id = None
        
        # PKCE parameters
        self.code_verifier = None
        self.code_challenge = None
        
        logger.info(f"Initialized MCP server test suite with base URL: {self.base_url}")
        logger.info(f"Client ID: {self.client_id}")
        logger.info(f"Redirect URI: {self.redirect_uri}")
    
    async def run_all_tests(self):
        """Run all tests in the test suite"""
        logger.info("Starting MCP server test suite")
        
        # Test OAuth flow
        await self.test_oauth_flow()
        
        # Test memory endpoints (if OAuth flow succeeded)
        if self.access_token:
            await self.test_memory_endpoints()
        else:
            logger.error("Skipping memory endpoint tests due to OAuth flow failure")
            
        # Print test results
        self.print_results()
        
        return self.results
    
    def print_results(self):
        """Print test results in a readable format"""
        logger.info("=" * 50)
        logger.info("MCP SERVER TEST RESULTS")
        logger.info("=" * 50)
        logger.info(f"Total tests: {self.results['total_tests']}")
        logger.info(f"Passed tests: {self.results['passed_tests']}")
        logger.info(f"Failed tests: {self.results['failed_tests']}")
        logger.info("=" * 50)
        
        # Print OAuth flow results
        logger.info("OAuth Flow Tests:")
        for test_name, result in self.results["oauth_flow"].items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            logger.info(f"  {test_name}: {status}")
            if not result["passed"]:
                logger.info(f"    Error: {result['error']}")
        
        # Print memory endpoint results
        logger.info("Memory Endpoint Tests:")
        for test_name, result in self.results["memory_endpoints"].items():
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
    
    async def test_oauth_flow(self):
        """Test OAuth 2.0 Authorization Code flow"""
        logger.info("Testing OAuth 2.0 Authorization Code flow")
        
        # Step 1: Test authorization endpoint
        auth_code = await self.test_authorization_endpoint()
        
        # Step 2: Test token endpoint (if authorization succeeded)
        if auth_code:
            await self.test_token_endpoint(auth_code)
        else:
            logger.error("Skipping token endpoint test due to authorization failure")
    
    async def test_authorization_endpoint(self) -> Optional[str]:
        """Test authorization endpoint"""
        logger.info("Testing authorization endpoint")
        
        # Generate PKCE parameters
        self.code_verifier = secrets.token_urlsafe(32)
        code_challenge_bytes = hashlib.sha256(self.code_verifier.encode('ascii')).digest()
        self.code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode('ascii').rstrip('=')
        
        # Build authorization request
        auth_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "memories:read memories:write",
            "state": "test_state",
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256"
        }
        auth_url = f"{self.base_url}/oauth/authorize?{urlencode(auth_params)}"
        
        logger.info(f"Authorization URL: {auth_url}")
        
        # Send authorization request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(auth_url, follow_redirects=True)
                
                # Check if we got redirected to the callback URL
                if str(response.url).startswith(self.redirect_uri):
                    # Parse the callback URL
                    parsed_url = urlparse(str(response.url))
                    query_params = parse_qs(parsed_url.query)
                    
                    # Check if we got an authorization code
                    if "code" in query_params:
                        code = query_params["code"][0]
                        logger.info(f"Received authorization code: {code[:10]}...")
                        self.record_test_result("oauth_flow", "authorization_endpoint", True, data={"code": code})
                        return code
                    # Check if we got an error
                    elif "error" in query_params:
                        error = query_params["error"][0]
                        error_description = query_params.get("error_description", [""])[0]
                        error_message = f"Authorization error: {error} - {error_description}"
                        self.record_test_result("oauth_flow", "authorization_endpoint", False, error=error_message)
                        return None
                
                # If we didn't get redirected to the callback URL
                self.record_test_result(
                    "oauth_flow", 
                    "authorization_endpoint", 
                    False, 
                    error=f"Unexpected response: {response.status_code} {response.text}"
                )
                return None
        except Exception as e:
            self.record_test_result("oauth_flow", "authorization_endpoint", False, error=str(e))
            return None
    
    async def test_token_endpoint(self, auth_code: str):
        """Test token endpoint"""
        logger.info("Testing token endpoint")
        
        # Build token request
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": self.code_verifier
        }
        
        # Send token request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/oauth/token", data=token_data)
                
                # Check if we got a token
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Validate token response
                    if "access_token" in token_data and "token_type" in token_data:
                        self.access_token = token_data["access_token"]
                        logger.info(f"Received access token: {self.access_token[:10]}...")
                        self.record_test_result("oauth_flow", "token_endpoint", True, data=token_data)
                    else:
                        self.record_test_result(
                            "oauth_flow", 
                            "token_endpoint", 
                            False, 
                            error=f"Invalid token response: {token_data}"
                        )
                else:
                    self.record_test_result(
                        "oauth_flow", 
                        "token_endpoint", 
                        False, 
                        error=f"Token request failed: {response.status_code} {response.text}"
                    )
        except Exception as e:
            self.record_test_result("oauth_flow", "token_endpoint", False, error=str(e))
    
    async def test_memory_endpoints(self):
        """Test memory endpoints"""
        logger.info("Testing memory endpoints")
        
        # Test submit_memory endpoint
        await self.test_submit_memory()
        
        # Test retrieve_memories endpoint
        await self.test_retrieve_memories()
        
        # Test modify_permissions endpoint (if submit_memory succeeded)
        if self.test_memory_id:
            await self.test_modify_permissions()
        else:
            logger.error("Skipping modify_permissions test due to submit_memory failure")
        
        # Test query_user endpoint
        await self.test_query_user()
    
    async def test_submit_memory(self):
        """Test submit_memory endpoint"""
        logger.info("Testing submit_memory endpoint")
        
        # Build memory data
        memory_data = {
            "text": "This is a test memory created by the test suite"
        }
        
        # Send submit_memory request
        try:
            async with httpx.AsyncClient() as client:
                # Try different endpoint paths to handle potential routing issues
                endpoints_to_try = [
                    f"{self.base_url}/submit_memory",
                    f"{self.base_url}/tools/submit_memory"
                ]
                
                for endpoint in endpoints_to_try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    response = await client.post(
                        endpoint,
                        json=memory_data,
                        headers={"Authorization": f"Bearer {self.access_token}"}
                    )
                    
                    # Check if the request succeeded
                    if response.status_code == 200:
                        memory = response.json()
                        
                        # Validate memory response
                        if "id" in memory and "text" in memory:
                            self.test_memory_id = memory["id"]
                            logger.info(f"Created memory with ID: {self.test_memory_id}")
                            self.record_test_result("memory_endpoints", "submit_memory", True, data=memory)
                            return
                
                # If all endpoints failed
                self.record_test_result(
                    "memory_endpoints", 
                    "submit_memory", 
                    False, 
                    error=f"All endpoints failed. Last response: {response.status_code} {response.text}"
                )
        except Exception as e:
            self.record_test_result("memory_endpoints", "submit_memory", False, error=str(e))
    
    async def test_retrieve_memories(self):
        """Test retrieve_memories endpoint"""
        logger.info("Testing retrieve_memories endpoint")
        
        # Send retrieve_memories request
        try:
            async with httpx.AsyncClient() as client:
                # Try different endpoint paths to handle potential routing issues
                endpoints_to_try = [
                    f"{self.base_url}/retrieve_memories",
                    f"{self.base_url}/tools/retrieve_memories"
                ]
                
                for endpoint in endpoints_to_try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    response = await client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {self.access_token}"}
                    )
                    
                    # Check if the request succeeded
                    if response.status_code == 200:
                        memories = response.json()
                        
                        # Validate memories response
                        if isinstance(memories, list):
                            logger.info(f"Retrieved {len(memories)} memories")
                            self.record_test_result("memory_endpoints", "retrieve_memories", True, data=memories)
                            return
                
                # If all endpoints failed
                self.record_test_result(
                    "memory_endpoints", 
                    "retrieve_memories", 
                    False, 
                    error=f"All endpoints failed. Last response: {response.status_code} {response.text}"
                )
        except Exception as e:
            self.record_test_result("memory_endpoints", "retrieve_memories", False, error=str(e))
    
    async def test_modify_permissions(self):
        """Test modify_permissions endpoint"""
        logger.info("Testing modify_permissions endpoint")
        
        # Build permission data
        permission_data = {
            "memory_id": self.test_memory_id,
            "permission": "public"
        }
        
        # Send modify_permissions request
        try:
            async with httpx.AsyncClient() as client:
                # Try different endpoint paths to handle potential routing issues
                endpoints_to_try = [
                    f"{self.base_url}/modify_permissions",
                    f"{self.base_url}/tools/modify_permissions"
                ]
                
                for endpoint in endpoints_to_try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    response = await client.post(
                        endpoint,
                        json=permission_data,
                        headers={"Authorization": f"Bearer {self.access_token}"}
                    )
                    
                    # Check if the request succeeded
                    if response.status_code == 200:
                        memory = response.json()
                        
                        # Validate memory response
                        if "id" in memory and "permission" in memory:
                            logger.info(f"Updated memory permission to: {memory['permission']}")
                            self.record_test_result("memory_endpoints", "modify_permissions", True, data=memory)
                            return
                
                # If all endpoints failed
                self.record_test_result(
                    "memory_endpoints", 
                    "modify_permissions", 
                    False, 
                    error=f"All endpoints failed. Last response: {response.status_code} {response.text}"
                )
        except Exception as e:
            self.record_test_result("memory_endpoints", "modify_permissions", False, error=str(e))
    
    async def test_query_user(self):
        """Test query_user endpoint"""
        logger.info("Testing query_user endpoint")
        
        # Build query data
        query_data = {
            "user_id": 1,  # Assuming user ID 1 exists
            "prompt": "What are your thoughts on AI and memory systems?"
        }
        
        # Send query_user request
        try:
            async with httpx.AsyncClient() as client:
                # Try different endpoint paths to handle potential routing issues
                endpoints_to_try = [
                    f"{self.base_url}/query_user",
                    f"{self.base_url}/tools/query_user"
                ]
                
                for endpoint in endpoints_to_try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    response = await client.post(
                        endpoint,
                        json=query_data,
                        headers={"Authorization": f"Bearer {self.access_token}"}
                    )
                    
                    # Check if the request succeeded
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Validate query response
                        if "response" in result:
                            logger.info(f"LLM response: {result['response'][:50]}...")
                            self.record_test_result("memory_endpoints", "query_user", True, data=result)
                            return
                
                # If all endpoints failed
                self.record_test_result(
                    "memory_endpoints", 
                    "query_user", 
                    False, 
                    error=f"All endpoints failed. Last response: {response.status_code} {response.text}"
                )
        except Exception as e:
            self.record_test_result("memory_endpoints", "query_user", False, error=str(e))

async def main():
    """Run the test suite"""
    # Create test suite
    test_suite = MCPServerTest()
    
    # Run all tests
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
