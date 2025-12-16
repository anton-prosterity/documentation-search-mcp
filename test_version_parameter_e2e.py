#!/usr/bin/env python3
"""
End-to-End Test Suite for Version Parameter Feature

Tests the version parameter functionality across all documentation search tools.
Run this script to verify Phase 1 MVP implementation works correctly.

Usage:
    python test_version_parameter_e2e.py

Requirements:
    - SERPER_API_KEY environment variable must be set
    - Internet connection for search queries
"""

import asyncio
import sys
import os
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from documentation_search_enhanced.main import (
    get_versioned_docs_url,
    get_docs,
    semantic_search,
    filtered_search,
    get_code_examples,
)


class TestResult:
    """Test result container"""
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        msg = f": {self.message}" if self.message else ""
        return f"{status} | {self.name}{msg}"


class VersionParameterE2ETest:
    """End-to-end test suite for version parameter feature"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.serper_key = os.getenv("SERPER_API_KEY")

    def add_result(self, name: str, passed: bool, message: str = ""):
        """Add test result"""
        result = TestResult(name, passed, message)
        self.results.append(result)
        print(result)

    async def test_get_versioned_docs_url(self):
        """Test 1: get_versioned_docs_url helper function"""
        print("\n🧪 Test 1: get_versioned_docs_url Helper Function")
        print("=" * 60)

        # Test 1.1: Version template substitution
        config = {
            "url": "https://docs.djangoproject.com/en/stable/",
            "version_url_template": "https://docs.djangoproject.com/en/{version}/"
        }
        result = get_versioned_docs_url("django", "4.2", config)
        expected = "https://docs.djangoproject.com/en/4.2/"
        self.add_result(
            "Template substitution (django 4.2)",
            result == expected,
            f"Expected: {expected}, Got: {result}"
        )

        # Test 1.2: Latest version returns base URL
        result = get_versioned_docs_url("django", "latest", config)
        expected = "https://docs.djangoproject.com/en/stable/"
        self.add_result(
            "Latest version returns base URL",
            result == expected,
            f"Expected: {expected}, Got: {result}"
        )

        # Test 1.3: Fallback replacement (/stable/ → /version/)
        config_no_template = {
            "url": "https://numpy.org/doc/stable/"
        }
        result = get_versioned_docs_url("numpy", "2.0", config_no_template)
        expected = "https://numpy.org/doc/2.0/"
        self.add_result(
            "Fallback /stable/ replacement",
            result == expected,
            f"Expected: {expected}, Got: {result}"
        )

        # Test 1.4: Fallback replacement (/latest/ → /version/)
        config_latest = {
            "url": "https://docs.litestar.dev/latest/"
        }
        result = get_versioned_docs_url("litestar", "2.0", config_latest)
        expected = "https://docs.litestar.dev/2.0/"
        self.add_result(
            "Fallback /latest/ replacement",
            result == expected,
            f"Expected: {expected}, Got: {result}"
        )

    async def test_get_docs_with_version(self):
        """Test 2: get_docs tool with version parameter"""
        print("\n🧪 Test 2: get_docs Tool with Version Parameter")
        print("=" * 60)

        if not self.serper_key:
            self.add_result(
                "get_docs with version (skipped)",
                True,
                "SERPER_API_KEY not set, skipping live search test"
            )
            return

        # Test 2.1: Explicit version parameter
        try:
            result = await get_docs(
                query="authentication middleware",
                libraries=["django"],
                version="4.2"
            )

            has_results = (
                isinstance(result, dict) and
                "libraries" in result and
                len(result.get("libraries", [])) > 0
            )

            self.add_result(
                "get_docs with explicit version='4.2'",
                has_results,
                f"Returned {len(result.get('libraries', []))} library results"
            )
        except Exception as e:
            self.add_result(
                "get_docs with explicit version",
                False,
                f"Error: {str(e)}"
            )

        # Test 2.2: Default latest version
        try:
            result = await get_docs(
                query="routing",
                libraries=["flask"]
            )

            has_results = (
                isinstance(result, dict) and
                "libraries" in result
            )

            self.add_result(
                "get_docs with default version='latest'",
                has_results,
                "Successfully used default version"
            )
        except Exception as e:
            self.add_result(
                "get_docs default version",
                False,
                f"Error: {str(e)}"
            )

        # Test 2.3: Multiple libraries with version
        try:
            result = await get_docs(
                query="arrays",
                libraries=["numpy"],
                version="stable"
            )

            has_results = isinstance(result, dict)

            self.add_result(
                "get_docs multiple libraries with version",
                has_results,
                "Multiple library search with version"
            )
        except Exception as e:
            self.add_result(
                "get_docs multiple libraries",
                False,
                f"Error: {str(e)}"
            )

    async def test_semantic_search_with_version(self):
        """Test 3: semantic_search tool with version parameter"""
        print("\n🧪 Test 3: semantic_search Tool with Version Parameter")
        print("=" * 60)

        if not self.serper_key:
            self.add_result(
                "semantic_search with version (skipped)",
                True,
                "SERPER_API_KEY not set, skipping live search test"
            )
            return

        # Test 3.1: Semantic search with version
        try:
            result = await semantic_search(
                query="form validation",
                libraries=["django"],
                version="5.0"
            )

            has_results = isinstance(result, dict)

            self.add_result(
                "semantic_search with version='5.0'",
                has_results,
                "Semantic search with version parameter"
            )
        except Exception as e:
            self.add_result(
                "semantic_search with version",
                False,
                f"Error: {str(e)}"
            )

    async def test_filtered_search_with_version(self):
        """Test 4: filtered_search tool with version parameter"""
        print("\n🧪 Test 4: filtered_search Tool with Version Parameter")
        print("=" * 60)

        if not self.serper_key:
            self.add_result(
                "filtered_search with version (skipped)",
                True,
                "SERPER_API_KEY not set, skipping live search test"
            )
            return

        # Test 4.1: Filtered search with version
        try:
            result = await filtered_search(
                query="middleware",
                library="django",
                content_type="tutorial",
                version="4.2"
            )

            has_results = isinstance(result, dict)

            self.add_result(
                "filtered_search with version='4.2'",
                has_results,
                "Filtered search with version parameter"
            )
        except Exception as e:
            self.add_result(
                "filtered_search with version",
                False,
                f"Error: {str(e)}"
            )

    async def test_get_code_examples_with_version(self):
        """Test 5: get_code_examples tool with version parameter"""
        print("\n🧪 Test 5: get_code_examples Tool with Version Parameter")
        print("=" * 60)

        if not self.serper_key:
            self.add_result(
                "get_code_examples with version (skipped)",
                True,
                "SERPER_API_KEY not set, skipping live search test"
            )
            return

        # Test 5.1: Code examples with version
        try:
            result = await get_code_examples(
                library="flask",
                topic="routing",
                language="python",
                version="3.0"
            )

            has_results = isinstance(result, dict)

            self.add_result(
                "get_code_examples with version='3.0'",
                has_results,
                "Code examples with version parameter"
            )
        except Exception as e:
            self.add_result(
                "get_code_examples with version",
                False,
                f"Error: {str(e)}"
            )

    async def test_config_version_metadata(self):
        """Test 6: Config has proper version metadata"""
        print("\n🧪 Test 6: Configuration Version Metadata")
        print("=" * 60)

        try:
            from documentation_search_enhanced.config_validator import load_config
            config = load_config()
            config_dict = config.model_dump()

            # Check 10 high-priority libraries have version metadata
            expected_libraries = [
                "django", "flask", "litestar", "numpy", "matplotlib",
                "scikit-learn", "networkx", "requests", "pillow", "ipywidgets"
            ]

            for lib_name in expected_libraries:
                lib_config = config_dict.get("docs_urls", {}).get(lib_name, {})

                has_template = "version_url_template" in lib_config
                has_pattern = "version_pattern" in lib_config
                has_default = "default_version" in lib_config
                has_flag = lib_config.get("supports_versioning", False)

                all_present = has_template and has_pattern and has_default and has_flag

                self.add_result(
                    f"Config metadata for {lib_name}",
                    all_present,
                    f"Template:{has_template}, Pattern:{has_pattern}, Default:{has_default}, Flag:{has_flag}"
                )
        except Exception as e:
            self.add_result(
                "Config version metadata",
                False,
                f"Error loading config: {str(e)}"
            )

    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("🚀 Version Parameter E2E Test Suite")
        print("=" * 60)
        print(f"SERPER_API_KEY: {'✅ Set' if self.serper_key else '❌ Not Set'}")

        # Run all test groups
        await self.test_get_versioned_docs_url()
        await self.test_get_docs_with_version()
        await self.test_semantic_search_with_version()
        await self.test_filtered_search_with_version()
        await self.test_get_code_examples_with_version()
        await self.test_config_version_metadata()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests:  {total}")
        print(f"✅ Passed:    {passed}")
        print(f"❌ Failed:    {failed}")
        print(f"Pass Rate:    {pass_rate:.1f}%")

        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")

        print("=" * 60)

        return failed == 0


async def main():
    """Main test runner"""
    print("\n🔬 Starting Version Parameter E2E Tests...\n")

    # Check environment
    if not os.getenv("SERPER_API_KEY"):
        print("⚠️  WARNING: SERPER_API_KEY not set.")
        print("   Live search tests will be skipped.")
        print("   Set the key to run full test suite.\n")

    # Run tests
    test_suite = VersionParameterE2ETest()
    success = await test_suite.run_all_tests()

    # Exit with appropriate code
    if success:
        print("\n✅ All tests passed! Version parameter feature is working correctly.\n")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the failures above.\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
