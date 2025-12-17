#!/usr/bin/env python3
"""
Test script for the new project-aware security scanner.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

from documentation_search_enhanced.main import scan_project_dependencies
from documentation_search_enhanced.vulnerability_scanner import (
    SecurityReport,
    SeverityLevel,
    Vulnerability,
)


def setup_test_project(base: Path, name: str, files: dict) -> Path:
    """Create a temporary test project directory and files."""
    project_dir = base / name
    project_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        (project_dir / filename).write_text(content)
    print(f"📁 Created test project: '{project_dir}'")
    return project_dir


def _fake_security_report(
    *, library_name: str, ecosystem: str, vulnerabilities: list[Vulnerability]
) -> SecurityReport:
    critical = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.CRITICAL)
    high = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.HIGH)
    medium = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.MEDIUM)
    low = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.LOW)

    score = 100.0
    score -= critical * 25
    score -= high * 15
    score -= medium * 5
    score -= low
    score = max(0.0, score)

    return SecurityReport(
        library_name=library_name,
        ecosystem=ecosystem,
        scan_date="2025-01-01T00:00:00Z",
        total_vulnerabilities=len(vulnerabilities),
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low,
        security_score=score,
        recommendations=["Update to the latest version."],
        vulnerabilities=vulnerabilities,
        latest_secure_version=None,
    )


async def _fake_scan_library(library_name: str, ecosystem: str = "PyPI") -> SecurityReport:
    if library_name.lower() == "requests":
        vulnerability = Vulnerability(
            id="TEST-REQUESTS-001",
            title="Test vulnerability for requests",
            description="Simulated vulnerability used for offline unit tests.",
            severity=SeverityLevel.HIGH,
            cvss_score=7.5,
            cve_id="CVE-2099-0001",
            affected_versions=["<=2.25.0"],
            fixed_version="2.25.1",
            published_date="2025-01-01T00:00:00Z",
            source="osv",
            references=["https://example.com/advisory"],
        )
        return _fake_security_report(
            library_name=library_name,
            ecosystem=ecosystem,
            vulnerabilities=[vulnerability],
        )

    return _fake_security_report(
        library_name=library_name, ecosystem=ecosystem, vulnerabilities=[]
    )


async def _run_scanner_tests(base_dir: Path):
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
    project1 = setup_test_project(base_dir, "test-project-1", {"pyproject.toml": pyproject_content})
    report1 = await scan_project_dependencies(str(project1))
    
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
    project2 = setup_test_project(base_dir, "test-project-2", {"requirements.txt": requirements_content})
    report2 = await scan_project_dependencies(str(project2))

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
    project3 = setup_test_project(base_dir, "test-project-3", {"package.json": package_json_content})
    report3 = await scan_project_dependencies(str(project3))

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
    project_clean = setup_test_project(base_dir, "test-project-clean", {"pyproject.toml": clean_pyproject})
    report4 = await scan_project_dependencies(str(project_clean))
    assert report4['summary']['total_dependencies'] == 0
    print("✅ Correctly handled project with no dependencies.")
    
    # 5. Test with no dependency file
    print("\n5. Testing with no dependency file...")
    empty_project = setup_test_project(base_dir, "test-project-empty", {})
    report5 = await scan_project_dependencies(str(empty_project))
    assert "error" in report5
    print("✅ Correctly handled project with no dependency file.")

    print("\n🧹 Cleaned up test directories.")


def test_scanner():
    import documentation_search_enhanced.vulnerability_scanner as scanner_module

    scanner_module.vulnerability_scanner.scan_library = _fake_scan_library
    base_dir = Path(tempfile.mkdtemp(prefix="project_scanner_"))
    try:
        asyncio.run(_run_scanner_tests(base_dir))
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
        print("✅ Temporary project directories removed.")


if __name__ == "__main__":
    test_scanner()
