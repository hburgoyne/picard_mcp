"""
Integration tests for the OAuth flow between MCP server and Django client.

These tests verify that the OAuth flow works correctly end-to-end between
the two services. They require both services to be running.

Usage:
    cd /Users/hayden/Documents/Github/picard_mcp
    python -m pytest tests/test_oauth_integration.py -v
"""
import os
import pytest
import requests
import time
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
    """Set up a headless browser for testing."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()

def create_test_user(browser):
    """Create a test user in the Django client if it doesn't exist."""
    # Check if user exists by trying to log in
    browser.get(f"{DJANGO_URL}/login/")
    
    username_input = browser.find_element(By.NAME, "username")
    password_input = browser.find_element(By.NAME, "password")
    
    username_input.send_keys(TEST_USERNAME)
    password_input.send_keys(TEST_PASSWORD)
    
    browser.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # If we're redirected to the dashboard, user exists
    if browser.current_url.startswith(f"{DJANGO_URL}/dashboard/"):
        return
    
    # Otherwise, create the user
    browser.get(f"{DJANGO_URL}/register/")
    
    username_input = browser.find_element(By.NAME, "username")
    email_input = browser.find_element(By.NAME, "email")
    password1_input = browser.find_element(By.NAME, "password1")
    password2_input = browser.find_element(By.NAME, "password2")
    
    username_input.send_keys(TEST_USERNAME)
    email_input.send_keys(TEST_EMAIL)
    password1_input.send_keys(TEST_PASSWORD)
    password2_input.send_keys(TEST_PASSWORD)
    
    browser.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # Verify registration was successful
    assert browser.current_url.startswith(f"{DJANGO_URL}/login/")
    
    # Log in with the new user
    username_input = browser.find_element(By.NAME, "username")
    password_input = browser.find_element(By.NAME, "password")
    
    username_input.send_keys(TEST_USERNAME)
    password_input.send_keys(TEST_PASSWORD)
    
    browser.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # Verify login was successful
    assert browser.current_url.startswith(f"{DJANGO_URL}/dashboard/")

def test_oauth_flow(browser):
    """Test the complete OAuth flow between Django client and MCP server."""
    # Create a test user and log in
    create_test_user(browser)
    
    # Navigate to the OAuth authorize endpoint
    browser.get(f"{DJANGO_URL}/oauth/authorize/")
    
    # We should be redirected to the MCP server's consent page
    WebDriverWait(browser, 10).until(
        EC.url_contains(f"{MCP_URL}/api/oauth/authorize")
    )
    
    # Verify we're on the consent page
    assert "Authorization Request" in browser.page_source
    assert "memories:read" in browser.page_source
    assert "memories:write" in browser.page_source
    
    # Accept the authorization request
    browser.find_element(By.NAME, "decision").click()
    
    # We should be redirected back to the Django client
    WebDriverWait(browser, 10).until(
        EC.url_contains(f"{DJANGO_URL}/dashboard")
    )
    
    # Verify the authorization was successful
    assert "Successfully connected to MCP server" in browser.page_source
    
    # Check that we can access the dashboard
    assert "Dashboard" in browser.page_source
    
    # Verify the token is stored by checking for the "Connected" status
    assert "Connected to MCP" in browser.page_source or "MCP Status: Connected" in browser.page_source

def test_token_refresh(browser):
    """Test that tokens can be refreshed."""
    # First ensure we're logged in and have a token
    browser.get(f"{DJANGO_URL}/dashboard/")
    
    if not browser.current_url.startswith(f"{DJANGO_URL}/dashboard/"):
        # Log in if needed
        browser.get(f"{DJANGO_URL}/login/")
        
        username_input = browser.find_element(By.NAME, "username")
        password_input = browser.find_element(By.NAME, "password")
        
        username_input.send_keys(TEST_USERNAME)
        password_input.send_keys(TEST_PASSWORD)
        
        browser.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # Navigate to the refresh token endpoint
    browser.get(f"{DJANGO_URL}/oauth/refresh/")
    
    # We should be redirected back to the dashboard
    WebDriverWait(browser, 10).until(
        EC.url_contains(f"{DJANGO_URL}/dashboard")
    )
    
    # Verify the refresh was successful
    assert "Token refreshed successfully" in browser.page_source or "Connected to MCP" in browser.page_source

if __name__ == "__main__":
    # This allows running the tests directly with python
    browser = webdriver.Chrome()
    try:
        create_test_user(browser)
        test_oauth_flow(browser)
        test_token_refresh(browser)
        print("All integration tests passed!")
    finally:
        browser.quit()
