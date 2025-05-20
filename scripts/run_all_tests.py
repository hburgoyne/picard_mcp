#!/usr/bin/env python
"""
Main test runner script that executes all test suites and provides a consolidated report.
"""
import os
import sys
import json
import asyncio
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_runner")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test suites
from test_mcp_server import MCPServerTest
from test_django_client import DjangoClientTest

async def run_tests(args):
    """Run all test suites"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_suites": {}
    }
    
    # Run MCP server tests if requested
    if args.mcp or args.all:
        logger.info("=" * 80)
        logger.info("RUNNING MCP SERVER TESTS")
        logger.info("=" * 80)
        
        mcp_test = MCPServerTest(base_url=args.mcp_url)
        mcp_results = await mcp_test.run_all_tests()
        results["test_suites"]["mcp_server"] = mcp_results
    
    # Run Django client tests if requested
    if args.django or args.all:
        logger.info("=" * 80)
        logger.info("RUNNING DJANGO CLIENT TESTS")
        logger.info("=" * 80)
        
        django_test = DjangoClientTest(base_url=args.django_url)
        django_results = await django_test.run_all_tests()
        results["test_suites"]["django_client"] = django_results
    
    # Generate summary
    generate_summary(results)
    
    # Save results to file if requested
    if args.output:
        save_results(results, args.output)
    
    return results

def generate_summary(results: Dict[str, Any]):
    """Generate and print a summary of all test results"""
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for suite_name, suite_results in results["test_suites"].items():
        suite_total = suite_results.get("total_tests", 0)
        suite_passed = suite_results.get("passed_tests", 0)
        suite_failed = suite_results.get("failed_tests", 0)
        
        total_tests += suite_total
        total_passed += suite_passed
        total_failed += suite_failed
        
        logger.info(f"{suite_name}: {suite_passed}/{suite_total} tests passed ({suite_passed/suite_total*100:.1f}%)")
    
    logger.info("-" * 80)
    logger.info(f"OVERALL: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}%)")
    logger.info("=" * 80)
    
    # Print failures for quick reference
    if total_failed > 0:
        logger.info("FAILED TESTS:")
        for suite_name, suite_results in results["test_suites"].items():
            for category, tests in suite_results.items():
                if category in ["total_tests", "passed_tests", "failed_tests"]:
                    continue
                
                for test_name, test_result in tests.items():
                    if not test_result.get("passed", True):
                        logger.info(f"  {suite_name}.{category}.{test_name}: {test_result.get('error', 'Unknown error')}")

def save_results(results: Dict[str, Any], output_file: str):
    """Save test results to a file"""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to {output_file}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run test suites for MCP server and Django client")
    
    # Test selection arguments
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument("--all", action="store_true", help="Run all tests")
    test_group.add_argument("--mcp", action="store_true", help="Run MCP server tests")
    test_group.add_argument("--django", action="store_true", help="Run Django client tests")
    
    # URL configuration arguments
    url_group = parser.add_argument_group("URL Configuration")
    url_group.add_argument("--mcp-url", default="http://localhost:8001", help="MCP server URL")
    url_group.add_argument("--django-url", default="http://localhost:8000", help="Django client URL")
    
    # Output arguments
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--output", "-o", help="Output file for test results (JSON format)")
    
    args = parser.parse_args()
    
    # Default to running all tests if none specified
    if not (args.all or args.mcp or args.django):
        args.all = True
    
    return args

async def main():
    """Main entry point"""
    args = parse_args()
    await run_tests(args)

if __name__ == "__main__":
    asyncio.run(main())
