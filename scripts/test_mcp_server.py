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
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, Any, List, Optional, Tuple

import httpx
from jose import jwt

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
        # Set DOCKER_ENV to indicate we're running inside Docker
        os.environ['DOCKER_ENV'] = 'yes'
        
        # Determine base URL based on environment
        if os.environ.get('DOCKER_ENV'):
            # Running inside Docker
            self.base_url = base_url or "http://app:8000"
        else:
            # Running outside Docker
            self.base_url = base_url or "http://localhost:8001"  # Use port 8001 to match Docker config
            
        # Get OAuth credentials from environment variables if available
        self.client_id = os.environ.get('OAUTH_CLIENT_ID', settings.OAUTH_CLIENT_ID)
        self.client_secret = os.environ.get('OAUTH_CLIENT_SECRET', settings.OAUTH_CLIENT_SECRET)
        self.redirect_uri = os.environ.get('OAUTH_REDIRECT_URI', settings.OAUTH_REDIRECT_URI)
        
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
        logger.info(f"Running in Docker: {os.environ.get('DOCKER_ENV', 'no')}")
    
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
        
        try:
            # Set DOCKER_ENV to indicate we're running inside Docker
            os.environ['DOCKER_ENV'] = 'yes'
            
            # Determine base URL based on environment
            if os.environ.get('DOCKER_ENV'):
                # Running inside Docker
                self.base_url = "http://app:8000"
            else:
                # Running outside Docker
                self.base_url = "http://localhost:8001"  # Use port 8001 to match Docker config
                
            # Get OAuth credentials from environment variables if available
            self.client_id = os.environ.get('OAUTH_CLIENT_ID', settings.OAUTH_CLIENT_ID)
            self.client_secret = os.environ.get('OAUTH_CLIENT_SECRET', settings.OAUTH_CLIENT_SECRET)
            self.redirect_uri = os.environ.get('OAUTH_REDIRECT_URI', settings.OAUTH_REDIRECT_URI)
            
            logger.info(f"Initialized MCP server test suite with base URL: {self.base_url}")
            logger.info(f"Client ID: {self.client_id}")
            logger.info(f"Redirect URI: {self.redirect_uri}")
            logger.info(f"Running in Docker: {os.environ.get('DOCKER_ENV', 'no')}")
            
            # Generate PKCE parameters
            self.code_verifier = secrets.token_urlsafe(32)
            code_challenge_bytes = hashlib.sha256(self.code_verifier.encode('ascii')).digest()
            self.code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode('ascii').rstrip('=')
            
            # 1. Get authorization URL
            # Use root path since MCP server is mounted at /
            auth_url = f"{self.base_url}/authorize?" + urlencode({
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'response_type': 'code',
                'scope': ' '.join(['memories:read', 'memories:write']),
                'state': secrets.token_urlsafe(16),
                'code_challenge': self.code_challenge,
                'code_challenge_method': 'S256'
            })
            logger.info(f"Authorization URL: {auth_url}")
            
            # 2. Simulate authorization request
            async with httpx.AsyncClient() as client:
                # Make the authorization request
                response = await client.get(auth_url)
                
                if response.status_code != 302:
                    raise Exception(f"Authorization request failed: {response.status_code}")
                
                # Extract the authorization code from the redirect URL
                redirect_url = response.headers.get('location')
                if not redirect_url:
                    raise Exception("No redirect URL found in response")
                
                # Parse the redirect URL to get the code
                params = parse_qs(urlparse(redirect_url).query)
                auth_code = params.get('code', [None])[0]
                
                if not auth_code:
                    raise Exception("No authorization code found in redirect URL")
                
                logger.info(f"Received authorization code: {auth_code[:10]}...")
                code = auth_code
            
            # 3. Exchange authorization code for tokens
            async with httpx.AsyncClient() as client:
                try:
                    # First, try to get the token endpoint URL from the well-known configuration
                    well_known_url = f"{self.base_url}/.well-known/oauth-authorization-server"
                    logger.info(f"Fetching OAuth configuration from: {well_known_url}")
                    
                    response = await client.get(well_known_url)
                    if response.status_code == 200:
                        config = response.json()
                        # If we're running in Docker, convert localhost to app service name
                        token_endpoint = config.get('token_endpoint', f"{self.base_url}/oauth/token")
                        token_endpoint = token_endpoint.replace('/token', '/token')
                        if os.environ.get('DOCKER_ENV'):
                            token_endpoint = token_endpoint.replace('http://localhost:8001', 'http://app:8000')
                    else:
                        # Fall back to default endpoint if well-known config not available
                        token_endpoint = f"{self.base_url}/oauth/token"
                    
                    logger.info(f"Using token endpoint: {token_endpoint}")
                    
                    response = await client.post(
                        token_endpoint,
                        data={
                            'grant_type': 'authorization_code',
                            'code': code,
                            'redirect_uri': self.redirect_uri,
                            'client_id': self.client_id,
                            'client_secret': self.client_secret,
                            'scope': ' '.join(['memories:read', 'memories:write']),
                            'code_verifier': self.code_verifier
                        },
                        headers={
                            'Accept': 'application/json',
                            'Content-Type': 'application/x-www-form-urlencoded'
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"Token exchange failed: {response.status_code}"
                        try:
                            error_data = response.json()
                            error_msg += f" - {error_data.get('error_description', 'No error description')}"
                            logger.error(f"Token exchange response: {error_data}")
                        except:
                            error_msg += f" - {response.text}"
                        raise Exception(error_msg)
                    
                    token_data = response.json()
                    self.access_token = token_data['access_token']
                    
                    self.results['oauth_flow']['token_exchange'] = {
                        'passed': True,
                        'access_token': self.access_token[:10] + '...'  # Log only first 10 chars for security
                    }
                    logger.info("OAuth flow test completed successfully")
                    
                except httpx.RequestError as e:
                    raise Exception(f"Request error during token exchange: {str(e)}")
                except Exception as e:
                    logger.error(f"Token exchange failed: {str(e)}")
                    self.results['oauth_flow']['token_exchange'] = {
                        'passed': False,
                        'error': str(e)
                    }
                    return
                
        except Exception as e:
            logger.error(f"OAuth flow test failed: {str(e)}")
            self.results['oauth_flow']['token_exchange'] = {
                'passed': False,
                'error': str(e)
            }
    
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
                # Use the MCP tool endpoint
                endpoint = f"{self.base_url}/api/tools"
                logger.info(f"Trying endpoint: {endpoint}")
                response = await client.post(
                    endpoint,
                    json={
                        "tool": "submit_memory",
                        "data": memory_data
                    },
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
                
                # If the request failed
                self.record_test_result(
                    "memory_endpoints", 
                    "submit_memory", 
                    False, 
                    error=f"Request failed. Response: {response.status_code} {response.text}"
                )
        except Exception as e:
            self.record_test_result("memory_endpoints", "submit_memory", False, error=str(e))
    
    async def test_retrieve_memories(self):
        """Test retrieve_memories endpoint"""
        logger.info("Testing retrieve_memories endpoint")
        
        # Send retrieve_memories request
        try:
            async with httpx.AsyncClient() as client:
                # Use the MCP tool endpoint
                endpoint = f"{self.base_url}/api/tools"
                logger.info(f"Trying endpoint: {endpoint}")
                response = await client.post(
                    endpoint,
                    json={
                        "tool": "retrieve_memories",
                        "data": {}
                    },
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
                
                # If the request failed
                self.record_test_result(
                    "memory_endpoints", 
                    "retrieve_memories", 
                    False, 
                    error=f"Request failed. Response: {response.status_code} {response.text}"
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
                # Use the MCP tool endpoint
                endpoint = f"{self.base_url}/api/tools"
                logger.info(f"Trying endpoint: {endpoint}")
                response = await client.post(
                    endpoint,
                    json={
                        "tool": "modify_permissions",
                        "data": permission_data
                    },
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
                
                # If the request failed
                self.record_test_result(
                    "memory_endpoints", 
                    "modify_permissions", 
                    False, 
                    error=f"Request failed. Response: {response.status_code} {response.text}"
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
