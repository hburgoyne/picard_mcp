#!/usr/bin/env python
"""
OAuth Integration Test Runner for Render Deployment

This script runs integration tests against the deployed Render environment
to verify that the OAuth flow is working correctly, including credential
validation and automatic recovery from invalid credentials.

Usage:
    python run_render_tests.py --django-url DJANGO_URL --mcp-url MCP_URL

Example:
    python run_render_tests.py --django-url https://picard-django-client.onrender.com \
                              --mcp-url https://picard-mcp-server.onrender.com
"""
import argparse
import os
import sys
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_tests.log')
    ]
)

logger = logging.getLogger('render_tests')

def run_tests(django_url, mcp_url, admin_password=None):
    """Run OAuth integration tests against the deployed environment."""
    logger.info(f"Running tests against Django: {django_url} and MCP: {mcp_url}")
    
    # Set environment variables for the tests
    env = os.environ.copy()
    env['DJANGO_URL'] = django_url
    env['MCP_SERVER_URL'] = mcp_url
    
    if admin_password:
        env['ADMIN_PASSWORD'] = admin_password
    
    # Run OAuth credential monitoring first
    monitor_cmd = [
        'python', 'monitor_oauth.py',
        '--django-url', django_url,
        '--mcp-url', mcp_url
    ]
    
    if admin_password:
        monitor_cmd.extend(['--admin-password', admin_password])
    
    logger.info("Running OAuth credential monitoring...")
    monitor_result = subprocess.run(
        monitor_cmd,
        env=env,
        capture_output=True,
        text=True
    )
    
    logger.info(f"Monitoring completed with exit code: {monitor_result.returncode}")
    logger.info(f"Monitoring output: {monitor_result.stdout}")
    
    if monitor_result.stderr:
        logger.error(f"Monitoring errors: {monitor_result.stderr}")
    
    # Run the OAuth recovery tests
    logger.info("Running OAuth recovery tests...")
    
    pytest_cmd = [
        'pytest', 'test_oauth_recovery.py', '-v'
    ]
    
    test_result = subprocess.run(
        pytest_cmd,
        env=env,
        capture_output=True,
        text=True
    )
    
    logger.info(f"Tests completed with exit code: {test_result.returncode}")
    logger.info(f"Test output: {test_result.stdout}")
    
    if test_result.stderr:
        logger.error(f"Test errors: {test_result.stderr}")
    
    return test_result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Run OAuth integration tests against Render deployment')
    parser.add_argument('--django-url', required=True, help='URL of the Django client')
    parser.add_argument('--mcp-url', required=True, help='URL of the MCP server')
    parser.add_argument('--admin-password', help='Admin password for admin-only operations')
    
    args = parser.parse_args()
    
    success = run_tests(args.django_url, args.mcp_url, args.admin_password)
    
    if success:
        logger.info("All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("Tests failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
