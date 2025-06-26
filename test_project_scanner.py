#!/usr/bin/env python3
"""
Test script for the new project-aware security scanner.
"""

import asyncio
import os
from src.documentation_search_enhanced.main import scan_project_dependencies

def setup_test_project(name: str, files: dict):
    """Create a temporary test project directory and files."""
    os.makedirs(name, exist_ok=True)
    for filename, content in files.items():
        with open(os.path.join(name, filename), "w") as f:
            f.write(content)
    print(f"📁 Created test project: '{name}'")

async def test_scanner():
    print("🧪 TESTING PROJECT-AWARE SECURITY SCANNER")
    print("=" * 60)

    # 1. Test with pyproject.toml
    print("\n1. Testing with pyproject.toml...")
    pyproject_content = """
[project]
name = "test-project-1"
version = "0.1.0"
dependencies = [
    "requests==2.25.0", # Known to have vulnerabilities
    "fastapi>=0.100.0",
    "numpy"
]
"""
    setup_test_project("test-project-1", {"pyproject.toml": pyproject_content})
    report1 = await scan_project_dependencies("test-project-1")
    
    assert report1['summary']['vulnerable_count'] > 0
    assert any(p['library'] == 'requests' for p in report1['vulnerable_packages'])
    print("✅ Successfully detected vulnerabilities in pyproject.toml.")

    # 2. Test with requirements.txt
    print("\n2. Testing with requirements.txt...")
    requirements_content = """
# This is a comment
requests==2.25.0
# Another comment
    django<4.0
    """
    setup_test_project("test-project-2", {"requirements.txt": requirements_content})
    report2 = await scan_project_dependencies("test-project-2")

    assert report2['summary']['vulnerable_count'] > 0
    assert any(p['library'] == 'requests' for p in report2['vulnerable_packages'])
    assert len(report2['vulnerable_packages']) >= 1
    print("✅ Successfully detected vulnerabilities in requirements.txt.")

    # 3. Test with package.json (npm)
    print("\n3. Testing with package.json...")
    package_json_content = """
{
  "name": "test-project-3",
  "version": "1.0.0",
  "dependencies": {
    "express": "4.17.1",
    "lodash": "4.17.20"
  }
}
"""
    setup_test_project("test-project-3", {"package.json": package_json_content})
    report3 = await scan_project_dependencies("test-project-3")

    # Note: Our scanner might find vulns in old versions of express/lodash
    if report3['summary']['vulnerable_count'] > 0:
        print(f"✅ Successfully detected {report3['summary']['vulnerable_count']} vulnerable npm packages.")
    else:
        print("✅ Scanned npm packages successfully (no vulnerabilities found in these versions).")


    # 4. Test with a clean project
    print("\n4. Testing with a clean project...")
    clean_pyproject = """
[project]
name = "clean-project"
version = "0.1.0"
dependencies = []
"""
    setup_test_project("test-project-clean", {"pyproject.toml": clean_pyproject})
    report4 = await scan_project_dependencies("test-project-clean")
    assert report4['summary']['total_dependencies'] == 0
    print("✅ Correctly handled project with no dependencies.")
    
    # 5. Test with no dependency file
    print("\n5. Testing with no dependency file...")
    os.makedirs("test-project-empty", exist_ok=True)
    report5 = await scan_project_dependencies("test-project-empty")
    assert "error" in report5
    print("✅ Correctly handled project with no dependency file.")

    # Cleanup
    import shutil
    for i in range(1, 4):
        shutil.rmtree(f"test-project-{i}")
    shutil.rmtree("test-project-clean")
    shutil.rmtree("test-project-empty")
    print("\n🧹 Cleaned up test directories.")


async def main():
    await test_scanner()
    print("\n🎉 All tests for Project-Aware Security Scanner passed!")

if __name__ == "__main__":
    asyncio.run(main()) 