"""
Integration tests for memory management between MCP server and Django client.

These tests verify that memory creation, retrieval, updating, and deletion
work correctly end-to-end between the two services. They require both
services to be running.

Usage:
    cd /Users/hayden/Documents/Github/picard_mcp
    python -m pytest tests/test_memory_integration.py -v
"""
import os
import sys
import pytest
import requests
import time
import uuid
import json
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

# Import shared test utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_oauth_integration import (
    browser, check_services_running, create_test_user, login_test_user,
    DJANGO_URL, MCP_URL, TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL
)

# Test data
TEST_MEMORY_TITLE = f"Test Memory {uuid.uuid4()}"
TEST_MEMORY_CONTENT = f"This is a test memory created at {time.strftime('%Y-%m-%d %H:%M:%S')}"
TEST_MEMORY_TAGS = ["test", "integration", "automated"]
TEST_MEMORY_UPDATE_TITLE = f"Updated Test Memory {uuid.uuid4()}"
TEST_MEMORY_UPDATE_CONTENT = f"This memory was updated at {time.strftime('%Y-%m-%d %H:%M:%S')}"

def ensure_oauth_connected(browser):
    """Ensure that the OAuth connection is established using Direct Connect."""
    print("\n=== Ensuring OAuth connection is established ===")
    browser.get(f"{DJANGO_URL}/dashboard/")
    
    # Check if we're already connected
    page_source = browser.page_source
    connected_indicators = [
        "Connection Status: Connected",
        "Connected to MCP",
        "Create Memory",  # If this button is present, we're likely connected
        "Search Memories"
    ]
    
    for indicator in connected_indicators:
        if indicator in page_source:
            print(f"OAuth connection already established (found '{indicator}')")
            return True
    
    # If not connected, use the Direct Connect flow instead of the OAuth authorize flow
    print("OAuth connection not established, initiating Direct Connect flow...")
    browser.get(f"{DJANGO_URL}/oauth/direct-connect/")
    
    try:
        # Wait for redirect back to dashboard
        WebDriverWait(browser, 20).until(
            EC.url_contains(f"{DJANGO_URL}/dashboard/")
        )
        
        # Wait a moment for the page to fully load
        time.sleep(2)
        
        # Verify connection was successful
        page_source = browser.page_source
        for indicator in connected_indicators:
            if indicator in page_source:
                print(f"OAuth connection successfully established (found '{indicator}')")
                return True
        
        # If we still don't see any connection indicators, try one more time with refresh token
        print("Connection indicators not found, trying refresh token...")
        browser.get(f"{DJANGO_URL}/oauth/refresh/")
        
        # Wait for redirect back to dashboard
        WebDriverWait(browser, 20).until(
            EC.url_contains(f"{DJANGO_URL}/dashboard/")
        )
        
        # Wait a moment for the page to fully load
        time.sleep(2)
        
        # Check again for connection indicators
        page_source = browser.page_source
        for indicator in connected_indicators:
            if indicator in page_source:
                print(f"OAuth connection successfully established after refresh (found '{indicator}')")
                return True
        
        # If still not connected, try the direct-connect endpoint one more time
        print("Connection indicators not found, trying direct-connect again...")
        browser.get(f"{DJANGO_URL}/oauth/direct-connect/")
        
        # Wait for redirect back to dashboard
        WebDriverWait(browser, 20).until(
            EC.url_contains(f"{DJANGO_URL}/dashboard/")
        )
        
        # Wait a moment for the page to fully load
        time.sleep(2)
        
        # Check one last time for connection indicators
        page_source = browser.page_source
        for indicator in connected_indicators:
            if indicator in page_source:
                print(f"OAuth connection successfully established after second direct-connect attempt (found '{indicator}')")
                return True
        
        print("Failed to establish OAuth connection")
        print(f"Page source excerpt: {page_source[:500]}...")
        return False
    except Exception as e:
        print(f"Error during OAuth connection: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source excerpt: {browser.page_source[:500]}...")
        return False

def test_create_memory(browser):
    """Test creating a new memory through the Django client."""
    print("\n=== Starting memory creation test ===")
    
    # Ensure we're logged in
    if not login_test_user(browser):
        pytest.skip("Could not log in as test user")
    
    # Ensure OAuth connection is established
    if not ensure_oauth_connected(browser):
        pytest.skip("Could not establish OAuth connection")
    
    # Navigate to memory creation page
    print(f"Navigating to memory creation page: {DJANGO_URL}/memories/create/")
    browser.get(f"{DJANGO_URL}/memories/create/")
    
    try:
        # Fill in the memory creation form
        print("Filling in memory creation form...")
        
        # Wait for form elements to be present
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "id_title"))
        )
        
        # Fill in title
        title_input = browser.find_element(By.ID, "id_title")
        title_input.clear()
        title_input.send_keys(TEST_MEMORY_TITLE)
        
        # Fill in content
        content_input = browser.find_element(By.ID, "id_content")
        content_input.clear()
        content_input.send_keys(TEST_MEMORY_CONTENT)
        
        # Fill in tags (comma-separated)
        tags_input = browser.find_element(By.ID, "id_tags")
        tags_input.clear()
        tags_input.send_keys(",".join(TEST_MEMORY_TAGS))
        
        # Submit the form
        print("Submitting memory creation form...")
        browser.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for redirect to dashboard or memory detail page
        WebDriverWait(browser, 10).until(
            lambda driver: "Memory created successfully" in driver.page_source or 
                          "Successfully created memory" in driver.page_source
        )
        
        print(f"After memory creation, current URL: {browser.current_url}")
        
        # Verify memory was created successfully
        assert "Memory created successfully" in browser.page_source or "Successfully created memory" in browser.page_source
        
        # Verify the memory appears on the dashboard
        browser.get(f"{DJANGO_URL}/dashboard/")
        
        # Wait for page to load and check if our memory is there
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "memory-card"))
        )
        
        page_source = browser.page_source
        assert TEST_MEMORY_TITLE in page_source, "Created memory title not found on dashboard"
        
        print("Memory creation test completed successfully")
    
    except Exception as e:
        print(f"Error during memory creation test: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source excerpt: {browser.page_source[:1000]}...")
        pytest.fail(f"Memory creation test failed: {str(e)}")

def get_memory_id(browser, memory_title):
    """Get the ID of a memory with the given title from the dashboard."""
    print(f"Looking for memory with title: {memory_title}")
    browser.get(f"{DJANGO_URL}/dashboard/")
    
    try:
        # Wait for memories to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "memory-card"))
        )
        
        # Find all memory cards
        memory_cards = browser.find_elements(By.CLASS_NAME, "memory-card")
        
        for card in memory_cards:
            if memory_title in card.text:
                # Find the edit link which contains the memory ID
                edit_link = card.find_element(By.XPATH, ".//a[contains(@href, '/memories/edit/')]")
                href = edit_link.get_attribute("href")
                
                # Extract memory ID from the URL
                memory_id = href.split("/memories/edit/")[1].rstrip("/")
                print(f"Found memory with ID: {memory_id}")
                return memory_id
        
        print(f"Memory with title '{memory_title}' not found")
        return None
    
    except Exception as e:
        print(f"Error getting memory ID: {str(e)}")
        return None

def test_update_memory(browser):
    """Test updating an existing memory through the Django client."""
    print("\n=== Starting memory update test ===")
    
    # Get the ID of the test memory
    memory_id = get_memory_id(browser, TEST_MEMORY_TITLE)
    if not memory_id:
        pytest.skip("Test memory not found for update test")
    
    # Navigate to memory edit page
    print(f"Navigating to memory edit page: {DJANGO_URL}/memories/edit/{memory_id}/")
    browser.get(f"{DJANGO_URL}/memories/edit/{memory_id}/")
    
    try:
        # Wait for form elements to be present
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "id_title"))
        )
        
        # Update title
        title_input = browser.find_element(By.ID, "id_title")
        title_input.clear()
        title_input.send_keys(TEST_MEMORY_UPDATE_TITLE)
        
        # Update content
        content_input = browser.find_element(By.ID, "id_content")
        content_input.clear()
        content_input.send_keys(TEST_MEMORY_UPDATE_CONTENT)
        
        # Submit the form
        print("Submitting memory update form...")
        browser.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for redirect and success message
        WebDriverWait(browser, 10).until(
            lambda driver: "Memory updated successfully" in driver.page_source or 
                          "Successfully updated memory" in driver.page_source
        )
        
        print(f"After memory update, current URL: {browser.current_url}")
        
        # Verify memory was updated successfully
        assert "Memory updated successfully" in browser.page_source or "Successfully updated memory" in browser.page_source
        
        # Verify the updated memory appears on the dashboard
        browser.get(f"{DJANGO_URL}/dashboard/")
        
        # Wait for page to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "memory-card"))
        )
        
        page_source = browser.page_source
        assert TEST_MEMORY_UPDATE_TITLE in page_source, "Updated memory title not found on dashboard"
        
        print("Memory update test completed successfully")
    
    except Exception as e:
        print(f"Error during memory update test: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source excerpt: {browser.page_source[:1000]}...")
        pytest.fail(f"Memory update test failed: {str(e)}")

def test_search_memory(browser):
    """Test searching for memories through the Django client."""
    print("\n=== Starting memory search test ===")
    
    # Navigate to memory search page
    print(f"Navigating to memory search page: {DJANGO_URL}/memories/search/")
    browser.get(f"{DJANGO_URL}/memories/search/")
    
    try:
        # Wait for search form to be present
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "id_query"))
        )
        
        # Enter search query (using the updated memory title)
        search_input = browser.find_element(By.ID, "id_query")
        search_input.clear()
        search_input.send_keys(TEST_MEMORY_UPDATE_TITLE)
        
        # Submit the search form
        print("Submitting memory search form...")
        browser.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for search results
        WebDriverWait(browser, 10).until(
            lambda driver: "Search Results" in driver.page_source
        )
        
        print(f"After memory search, current URL: {browser.current_url}")
        
        # Verify search found our memory
        page_source = browser.page_source
        assert TEST_MEMORY_UPDATE_TITLE in page_source, "Memory not found in search results"
        
        print("Memory search test completed successfully")
    
    except Exception as e:
        print(f"Error during memory search test: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source excerpt: {browser.page_source[:1000]}...")
        pytest.fail(f"Memory search test failed: {str(e)}")

def test_delete_memory(browser):
    """Test deleting a memory through the Django client."""
    print("\n=== Starting memory deletion test ===")
    
    # Get the ID of the test memory
    memory_id = get_memory_id(browser, TEST_MEMORY_UPDATE_TITLE)
    if not memory_id:
        pytest.skip("Test memory not found for deletion test")
    
    # Navigate to memory delete page
    print(f"Navigating to memory delete page: {DJANGO_URL}/memories/delete/{memory_id}/")
    browser.get(f"{DJANGO_URL}/memories/delete/{memory_id}/")
    
    try:
        # Wait for confirmation form to be present
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Delete')]"))
        )
        
        # Confirm deletion
        print("Confirming memory deletion...")
        browser.find_element(By.XPATH, "//button[contains(text(), 'Delete')]").click()
        
        # Wait for redirect and success message
        WebDriverWait(browser, 10).until(
            lambda driver: "Memory deleted successfully" in driver.page_source or 
                          "Successfully deleted memory" in driver.page_source
        )
        
        print(f"After memory deletion, current URL: {browser.current_url}")
        
        # Verify memory was deleted successfully
        assert "Memory deleted successfully" in browser.page_source or "Successfully deleted memory" in browser.page_source
        
        # Verify the memory no longer appears on the dashboard
        browser.get(f"{DJANGO_URL}/dashboard/")
        
        # Wait for page to load
        time.sleep(2)  # Give it a moment to load
        
        page_source = browser.page_source
        assert TEST_MEMORY_UPDATE_TITLE not in page_source, "Deleted memory still found on dashboard"
        
        print("Memory deletion test completed successfully")
    
    except Exception as e:
        print(f"Error during memory deletion test: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source excerpt: {browser.page_source[:1000]}...")
        pytest.fail(f"Memory deletion test failed: {str(e)}")

def test_api_direct_memory_verification(browser):
    """Test direct API verification of memory operations."""
    print("\n=== Starting direct API memory verification test ===")
    
    # First ensure we're logged in and have an OAuth token
    if not login_test_user(browser):
        pytest.skip("Could not log in as test user")
    
    if not ensure_oauth_connected(browser):
        pytest.skip("Could not establish OAuth connection")
    
    # Create a test memory for API verification
    test_api_memory_title = f"API Test Memory {uuid.uuid4()}"
    test_api_memory_content = f"This is a test memory for API verification created at {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Create the memory through the UI
    browser.get(f"{DJANGO_URL}/memories/create/")
    
    try:
        # Wait for form elements to be present
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "id_title"))
        )
        
        # Fill in title
        title_input = browser.find_element(By.ID, "id_title")
        title_input.clear()
        title_input.send_keys(test_api_memory_title)
        
        # Fill in content
        content_input = browser.find_element(By.ID, "id_content")
        content_input.clear()
        content_input.send_keys(test_api_memory_content)
        
        # Submit the form
        browser.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for redirect and success message
        WebDriverWait(browser, 10).until(
            lambda driver: "Memory created successfully" in driver.page_source or 
                          "Successfully created memory" in driver.page_source
        )
        
        # Now we'll extract the OAuth token to use for direct API verification
        # Navigate to a page where we can run JavaScript
        browser.get(f"{DJANGO_URL}/dashboard/")
        
        # Get the OAuth token from localStorage
        token_script = """
        return localStorage.getItem('oauth_token') || document.cookie.split('; ')
            .find(row => row.startsWith('oauth_token='))
            ?.split('=')[1];
        """
        
        # Try to get the token using JavaScript
        try:
            oauth_token = browser.execute_script(token_script)
            if not oauth_token:
                # If JavaScript approach failed, try to get it from cookies
                cookies = browser.get_cookies()
                for cookie in cookies:
                    if cookie['name'] == 'oauth_token':
                        oauth_token = cookie['value']
                        break
            
            if not oauth_token:
                # If we still don't have a token, try to extract it from network requests
                # This is a fallback and might not work in all browsers
                print("Could not get OAuth token from localStorage or cookies, using fallback method")
                
                # Get the memory ID to use for the API verification
                memory_id = get_memory_id(browser, test_api_memory_title)
                if not memory_id:
                    pytest.skip("Test memory not found for API verification")
                
                # Make a direct API request to the Django client to get memories
                # This will help us verify that the Django client is properly communicating with the MCP server
                response = requests.get(
                    f"{DJANGO_URL}/api/memories/",
                    cookies=browser.get_cookies()
                )
                
                if response.status_code == 200:
                    memories = response.json()
                    # Verify our test memory is in the response
                    memory_found = False
                    for memory in memories:
                        if memory.get('title') == test_api_memory_title:
                            memory_found = True
                            break
                    
                    assert memory_found, "Test memory not found in API response"
                    print("Successfully verified memory through Django client API")
                else:
                    print(f"Error accessing Django client API: {response.status_code}")
                    pytest.fail(f"Failed to access Django client API: {response.status_code}")
            else:
                # Now use the token to make a direct request to the MCP server
                headers = {
                    'Authorization': f'Bearer {oauth_token}',
                    'Content-Type': 'application/json',
                }
                
                # Request to retrieve memories from MCP server
                request_data = {
                    'tool': 'retrieve_memories',
                    'data': {}
                }
                
                response = requests.post(
                    f"{MCP_URL}/api/tools",
                    headers=headers,
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get('result', [])
                    
                    # Verify our test memory is in the response
                    memory_found = False
                    memory_id = None
                    for memory in memories:
                        if memory.get('title') == test_api_memory_title:
                            memory_found = True
                            memory_id = memory.get('id')
                            break
                    
                    assert memory_found, "Test memory not found in MCP server response"
                    
                    # Clean up by deleting the test memory
                    if memory_id:
                        delete_request_data = {
                            'tool': 'delete_memory',
                            'data': {
                                'memory_id': memory_id
                            }
                        }
                        
                        delete_response = requests.post(
                            f"{MCP_URL}/api/tools",
                            headers=headers,
                            json=delete_request_data
                        )
                        
                        assert delete_response.status_code == 200, "Failed to delete test memory through API"
                    
                    print("Successfully verified memory through direct MCP server API")
                else:
                    print(f"Error accessing MCP server API: {response.status_code}")
                    print(f"Response: {response.text}")
                    pytest.fail(f"Failed to access MCP server API: {response.status_code}")
        
        except Exception as e:
            print(f"Error during API verification: {str(e)}")
            # Fall back to UI-based verification
            print("Falling back to UI-based verification...")
            
            # Delete the test memory through the UI
            memory_id = get_memory_id(browser, test_api_memory_title)
            if memory_id:
                browser.get(f"{DJANGO_URL}/memories/delete/{memory_id}/")
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Delete')]"))
                )
                browser.find_element(By.XPATH, "//button[contains(text(), 'Delete')]").click()
                
                # Wait for redirect and success message
                WebDriverWait(browser, 10).until(
                    lambda driver: "Memory deleted successfully" in driver.page_source or 
                                  "Successfully deleted memory" in driver.page_source
                )
            
            pytest.fail(f"API verification failed: {str(e)}")
    
    except Exception as e:
        print(f"Error during API memory verification test: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source excerpt: {browser.page_source[:1000]}...")
        pytest.fail(f"API memory verification test failed: {str(e)}")

def run_memory_tests(browser):
    """Run all memory-related tests in sequence."""
    try:
        # Run all tests in sequence
        test_create_memory(browser)
        test_update_memory(browser)
        test_search_memory(browser)
        test_delete_memory(browser)
        test_api_direct_memory_verification(browser)
        
        print("All memory tests completed successfully!")
    
    except Exception as e:
        print(f"Error during memory tests: {str(e)}")
        pytest.fail(f"Memory tests failed: {str(e)}")

if __name__ == "__main__":
    # This allows running the tests directly with python
    if check_services_running():
        browser_instance = webdriver.Chrome()
        try:
            create_test_user(browser_instance)
            run_memory_tests(browser_instance)
        finally:
            browser_instance.quit()
    else:
        print("Cannot run tests: services are not running")
        print("Make sure both Django client and MCP server are running:")
        print(f"- Django client: {DJANGO_URL}")
        print(f"- MCP server: {MCP_URL}")
        sys.exit(1)
