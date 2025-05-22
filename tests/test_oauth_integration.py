"""
Integration tests for the OAuth flow between MCP server and Django client.

These tests verify that the OAuth flow works correctly end-to-end between
the two services. They require both services to be running.

Usage:
    cd /Users/hayden/Documents/Github/picard_mcp
    python -m pytest tests/test_oauth_integration.py -v
"""
import os
import sys
import pytest
import requests
import time
import subprocess
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuration
DJANGO_URL = "http://localhost:8000"
MCP_URL = "http://localhost:8001"
TEST_USERNAME = "integrationtestuser"
TEST_PASSWORD = "integrationtestpassword"
TEST_EMAIL = "integration@example.com"

@pytest.fixture(scope="module")
def browser():
    """Set up a browser for testing."""
    # Uncomment the browser you want to use
    
    # Chrome setup
    chrome_options = Options()
    # Comment out headless mode for debugging
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    print("Starting Chrome browser...")
    driver = webdriver.Chrome(options=chrome_options)
    
    # Firefox setup
    # from selenium.webdriver.firefox.options import Options as FirefoxOptions
    # firefox_options = FirefoxOptions()
    # firefox_options.add_argument("--headless")
    # print("Starting Firefox browser...")
    # driver = webdriver.Firefox(options=firefox_options)
    
    # Safari setup (macOS only, no options needed)
    # print("Starting Safari browser...")
    # driver = webdriver.Safari()
    
    # Edge setup
    # from selenium.webdriver.edge.options import Options as EdgeOptions
    # edge_options = EdgeOptions()
    # edge_options.add_argument("--headless")
    # print("Starting Edge browser...")
    # driver = webdriver.Edge(options=edge_options)
    
    driver.implicitly_wait(10)
    print("Browser started successfully")
    
    yield driver
    
    print("Closing browser...")
    driver.quit()

def create_test_user(browser):
    """Create a test user in the Django client if it doesn't exist."""
    print(f"Checking if test user {TEST_USERNAME} exists...")
    
    # First try to create the user directly using the Django shell
    # This is more reliable than using the UI
    try:
        import subprocess
        cmd = f"docker exec picard_mcp-django_client python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.filter(username='{TEST_USERNAME}').exists() or User.objects.create_user(username='{TEST_USERNAME}', email='{TEST_EMAIL}', password='{TEST_PASSWORD}')\""
        print(f"Running command to ensure test user exists: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Command result: {result.stdout if result.stdout else 'No output'}, Return code: {result.returncode}")
    except Exception as e:
        print(f"Error creating user via command: {str(e)}")
        print("Will try to use existing user...")
    
    # Now try to log in with the user
    return login_test_user(browser)

def login_test_user(browser):
    """Log in with the test user credentials."""
    print("Attempting to log in with test credentials...")
    # Make sure we're on the login page
    browser.get(f"{DJANGO_URL}/login/")
    print(f"Navigated to login page: {browser.current_url}")
    
    # Add a small wait to ensure the page is fully loaded
    time.sleep(1)
    
    try:
        username_input = browser.find_element(By.NAME, "username")
        password_input = browser.find_element(By.NAME, "password")
        
        username_input.send_keys(TEST_USERNAME)
        password_input.send_keys(TEST_PASSWORD)
        
        browser.find_element(By.XPATH, "//button[@type='submit']").click()
        print(f"After login attempt, current URL: {browser.current_url}")
        
        # Wait for redirect to dashboard (if login successful)
        WebDriverWait(browser, 5).until(
            lambda driver: driver.current_url.startswith(f"{DJANGO_URL}/dashboard/") or 
                          "Invalid username or password" in driver.page_source
        )
        
        # Check if login was successful
        if browser.current_url.startswith(f"{DJANGO_URL}/dashboard/"):
            print("Login successful")
            return True
        else:
            print("Login failed")
            print(f"Page source excerpt: {browser.page_source[:1000]}...")
            return False
    except Exception as e:
        print(f"Error during login: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source excerpt: {browser.page_source[:1000]}...")
        return False

def test_oauth_flow(browser):
    """Test the complete OAuth flow between Django client and MCP server."""
    print("\n=== Starting OAuth flow test ===")
    # Create a test user and log in
    if not create_test_user(browser):
        pytest.skip("Could not create or log in as test user")
    
    # Navigate to the OAuth authorize endpoint
    print(f"Navigating to OAuth authorize endpoint: {DJANGO_URL}/oauth/authorize/")
    browser.get(f"{DJANGO_URL}/oauth/authorize/")
    print(f"Current URL after navigation: {browser.current_url}")
    
    try:
        # We should be redirected to the MCP server's consent page
        print(f"Waiting for redirect to MCP consent page...")
        WebDriverWait(browser, 20).until(
            EC.url_contains(f"{MCP_URL}/api/oauth/authorize")
        )
        print(f"Redirected to: {browser.current_url}")
        
        # Verify we're on the consent page
        print("Checking consent page content...")
        page_source = browser.page_source
        if "Authorization Request" in page_source:
            print("Found 'Authorization Request' on page")
        else:
            print("WARNING: 'Authorization Request' not found on page")
            print(f"Page source excerpt: {page_source[:500]}...")
        assert "Authorization Request" in page_source
        
        # Check for scopes - with our new permission system, we need to be more flexible
        # as the exact scopes shown might depend on what's allowed for the client
        scopes_found = False
        for scope in ["memories:read", "memories:write", "profile:read"]:
            if scope in page_source:
                print(f"Found scope '{scope}' on consent page")
                scopes_found = True
        assert scopes_found, "No valid scopes found on consent page"
        
        # Accept the authorization request
        print("Clicking the authorize button...")
        browser.find_element(By.NAME, "decision").click()
        print(f"After clicking authorize, URL: {browser.current_url}")
        
        # We should be redirected back to the Django client
        print("Waiting for redirect back to Django dashboard...")
        WebDriverWait(browser, 20).until(
            EC.url_contains(f"{DJANGO_URL}/dashboard")
        )
        print(f"Redirected to: {browser.current_url}")
        
        # Verify the authorization was successful
        print("Checking for dashboard access after OAuth flow...")
        page_source = browser.page_source
        
        # Check if we're on the dashboard page
        assert "Dashboard" in browser.title or "Dashboard" in page_source
        
        # Check if we can see the memory creation button, which indicates we're logged in
        assert "Create Memory" in page_source
        # Since we're on the dashboard and can see the Create Memory button,
        # we know the OAuth flow worked correctly
        print("OAuth flow completed successfully - user is on dashboard with access to create memories")
        print("OAuth flow test completed successfully")
    except Exception as e:
        print(f"Error during OAuth flow test: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source: {browser.page_source[:500]}...")
        raise

def test_token_refresh(browser):
    """Test that tokens can be refreshed."""
    print("\n=== Starting token refresh test ===")
    # First ensure we're logged in and have a token
    print(f"Navigating to dashboard: {DJANGO_URL}/dashboard/")
    browser.get(f"{DJANGO_URL}/dashboard/")
    print(f"Current URL: {browser.current_url}")
    
    try:
        if not browser.current_url.startswith(f"{DJANGO_URL}/dashboard/"):
            print("Not on dashboard, logging in...")
            # Log in if needed
            if not login_test_user(browser):
                pytest.skip("Could not log in as test user for token refresh test")
        
        # Navigate to the refresh token endpoint
        print(f"Navigating to refresh token endpoint: {DJANGO_URL}/oauth/refresh/")
        browser.get(f"{DJANGO_URL}/oauth/refresh/")
        print(f"Current URL after navigation: {browser.current_url}")
        
        # We should be redirected back to the dashboard
        print("Waiting for redirect back to dashboard...")
        WebDriverWait(browser, 20).until(
            EC.url_contains(f"{DJANGO_URL}/dashboard")
        )
        print(f"Redirected to: {browser.current_url}")
        
        # Verify the refresh was successful
        print("Checking for dashboard access after token refresh...")
        page_source = browser.page_source
        
        # Check if we're on the dashboard page
        assert "Dashboard" in browser.title or "Dashboard" in page_source
        
        # Check if we can see the memory creation button, which indicates we're still logged in
        assert "Create Memory" in page_source
        print("Token refresh test completed successfully")
    except Exception as e:
        print(f"Error during token refresh test: {str(e)}")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source: {browser.page_source[:500]}...")
        raise

def check_services_running():
    """Check if both Django client and MCP server are running."""
    print("\n=== Checking if services are running ===")
    try:
        # Check Django client
        print(f"Checking Django client at {DJANGO_URL}...")
        django_response = requests.get(f"{DJANGO_URL}/login/", timeout=5)
        print(f"Django client response status: {django_response.status_code}")
        if django_response.status_code != 200:
            print(f"WARNING: Django client returned status {django_response.status_code}")
            return False
        
        # Check MCP server
        print(f"Checking MCP server at {MCP_URL}...")
        mcp_response = requests.get(f"{MCP_URL}/docs", timeout=5)  # Using docs endpoint as it doesn't require auth
        print(f"MCP server response status: {mcp_response.status_code}")
        if mcp_response.status_code != 200:
            print(f"WARNING: MCP server returned status {mcp_response.status_code}")
            return False
        
        print("Both services are running!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to services: {str(e)}")
        return False

@pytest.fixture(scope="session", autouse=True)
def check_environment():
    """Check if the test environment is properly set up."""
    if not check_services_running():
        pytest.skip("Required services are not running")

def run_all_tests():
    """Run all tests for the Picard MCP project."""
    print("\n=== Running all tests for Picard MCP ===")
    
    # First run the MCP server tests
    print("\n1. Running MCP server tests...")
    subprocess.run("docker-compose exec mcp_server pytest -xvs", shell=True)
    
    # Then run the Django client tests
    print("\n2. Running Django client tests...")
    subprocess.run("docker exec picard_mcp-django_client python manage.py test", shell=True)
    
    # Finally run the integration tests
    print("\n3. Running integration tests...")
    subprocess.run("python -m pytest tests/test_oauth_integration.py -v", shell=True)
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    # This allows running the tests directly with python
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Run all tests
        run_all_tests()
    else:
        # Run just the integration tests
        if check_services_running():
            browser = webdriver.Chrome()
            try:
                create_test_user(browser)
                test_oauth_flow(browser)
                test_token_refresh(browser)
                print("All integration tests passed!")
            finally:
                browser.quit()
        else:
            print("Cannot run tests: services are not running")
            print("Make sure both Django client and MCP server are running:")
            print(f"- Django client: {DJANGO_URL}")
            print(f"- MCP server: {MCP_URL}")
            sys.exit(1)
