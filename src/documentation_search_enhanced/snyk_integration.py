"""
Snyk integration for enhanced security scanning.
Provides comprehensive vulnerability analysis, license compliance, and security monitoring.
"""

import os
import json
import asyncio
import sys
import httpx
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .vulnerability_scanner import Vulnerability, SeverityLevel, SecurityReport
from .project_scanner import find_and_parse_dependencies

class SnykSeverity(Enum):
    """Snyk severity levels mapping"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class SnykVulnerability:
    """Snyk-specific vulnerability data"""
    id: str
    title: str
    description: str
    severity: SnykSeverity
    cvss_score: Optional[float]
    cve: List[str]
    cwe: List[str]
    exploit_maturity: Optional[str] 
    patches: List[str]
    upgrade_path: List[str]
    is_patchable: bool
    is_pinnable: bool
    published_date: str
    disclosure_time: Optional[str]
    
    def to_vulnerability(self) -> Vulnerability:
        """Convert to standard Vulnerability format"""
        severity_map = {
            SnykSeverity.CRITICAL: SeverityLevel.CRITICAL,
            SnykSeverity.HIGH: SeverityLevel.HIGH,
            SnykSeverity.MEDIUM: SeverityLevel.MEDIUM,
            SnykSeverity.LOW: SeverityLevel.LOW
        }
        
        return Vulnerability(
            id=self.id,
            title=self.title,
            description=self.description,
            severity=severity_map[self.severity],
            cvss_score=self.cvss_score,
            cve_id=self.cve[0] if self.cve else None,
            affected_versions=["various"],  # Snyk provides more complex version info
            fixed_version=self.upgrade_path[-1] if self.upgrade_path else None,
            published_date=self.published_date,
            source="snyk",
            references=[f"https://snyk.io/vuln/{self.id}"]
        )

@dataclass
class SnykLicense:
    """License information from Snyk"""
    id: str
    name: str
    spdx_id: Optional[str]
    type: str  # "copyleft", "permissive", "proprietary", etc.
    url: Optional[str]
    is_deprecated: bool
    instructions: str

@dataclass
class SnykPackageInfo:
    """Package information with security details"""
    name: str
    version: str
    ecosystem: str
    vulnerabilities: List[SnykVulnerability]
    licenses: List[SnykLicense]
    severity_counts: Dict[str, int]
    dependency_paths: List[List[str]]
    is_direct_dependency: bool

class SnykIntegration:
    """Snyk API integration for enterprise security scanning"""
    
    def __init__(self):
        self.api_key = os.getenv("SNYK_API_KEY")
        self.org_id = os.getenv("SNYK_ORG_ID") 
        self.base_url = "https://api.snyk.io"
        self.rest_api_url = "https://api.snyk.io/rest"
        self.timeout = httpx.Timeout(60.0)
        
        # Cache for API responses
        self.cache = {}
        self.cache_ttl = timedelta(hours=6)
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for Snyk API"""
        if not self.api_key:
            raise ValueError("SNYK_API_KEY environment variable is required")
            
        return {
            "Authorization": f"token {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "documentation-search-enhanced/1.3.0"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Snyk API connection and get organization info"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1/user/me",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    
                    # Get organizations
                    orgs_response = await client.get(
                        f"{self.base_url}/v1/user/me/orgs", 
                        headers=self._get_headers()
                    )
                    
                    orgs_data = orgs_response.json() if orgs_response.status_code == 200 else {"orgs": []}
                    
                    return {
                        "status": "connected",
                        "user": user_data.get("username"),
                        "organizations": [
                            {"id": org["id"], "name": org["name"]} 
                            for org in orgs_data.get("orgs", [])
                        ]
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"Authentication failed: {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Connection failed: {str(e)}"
            }
    
    async def scan_package(self, package_name: str, version: str, ecosystem: str = "pypi") -> SnykPackageInfo:
        """Scan a single package for vulnerabilities"""
        cache_key = f"package_{ecosystem}_{package_name}_{version}"
        
        if self._is_cached(cache_key):
            return self.cache[cache_key]["data"]
        
        ecosystem_map = {
            "pypi": "pip",
            "npm": "npm", 
            "maven": "maven",
            "gradle": "gradle",
            "nuget": "nuget"
        }
        
        snyk_ecosystem = ecosystem_map.get(ecosystem.lower(), "pip")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test endpoint for vulnerabilities
                test_payload = {
                    "encoding": "plain",
                    "files": {
                        f"requirements.txt" if snyk_ecosystem == "pip" else "package.json": {
                            "contents": f"{package_name}=={version}" if snyk_ecosystem == "pip" else json.dumps({
                                "dependencies": {package_name: version}
                            })
                        }
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/v1/test/{snyk_ecosystem}",
                    headers=self._get_headers(),
                    json=test_payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    package_info = self._parse_package_scan_result(data, package_name, version, ecosystem)
                    
                    # Cache the result
                    self._cache_result(cache_key, package_info)
                    
                    return package_info
                else:
                    # Return empty result for failed scans
                    return SnykPackageInfo(
                        name=package_name,
                        version=version,
                        ecosystem=ecosystem,
                        vulnerabilities=[],
                        licenses=[],
                        severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 0},
                        dependency_paths=[],
                        is_direct_dependency=True
                    )
                    
        except Exception as e:
            print(f"Snyk scan error for {package_name}: {e}", file=sys.stderr)
            return SnykPackageInfo(
                name=package_name,
                version=version, 
                ecosystem=ecosystem,
                vulnerabilities=[],
                licenses=[],
                severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 0},
                dependency_paths=[],
                is_direct_dependency=True
            )
    
    async def scan_project_manifest(self, manifest_path: str, ecosystem: str = None) -> Dict[str, Any]:
        """Scan project manifest file (requirements.txt, package.json, etc.)"""
        
        if not os.path.exists(manifest_path):
            return {"error": f"Manifest file not found: {manifest_path}"}
        
        # Auto-detect ecosystem if not provided
        if not ecosystem:
            if manifest_path.endswith(("requirements.txt", "pyproject.toml")):
                ecosystem = "pip"
            elif manifest_path.endswith("package.json"):
                ecosystem = "npm"
            else:
                ecosystem = "pip"  # Default
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                file_contents = f.read()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                test_payload = {
                    "encoding": "plain",
                    "files": {
                        os.path.basename(manifest_path): {
                            "contents": file_contents
                        }
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/v1/test/{ecosystem}",
                    headers=self._get_headers(),
                    json=test_payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_project_scan_result(data, manifest_path)
                else:
                    return {
                        "error": f"Snyk API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {"error": f"Failed to scan manifest: {str(e)}"}
    
    async def get_license_compliance(self, packages: List[Tuple[str, str]], ecosystem: str = "pypi") -> Dict[str, Any]:
        """Check license compliance for multiple packages"""
        compliance_results = {
            "total_packages": len(packages),
            "compliant_packages": 0,
            "non_compliant_packages": 0,
            "unknown_licenses": 0,
            "license_summary": {},
            "compliance_details": []
        }
        
        # Define license policies (configurable)
        allowed_licenses = {
            "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", 
            "ISC", "Unlicense", "WTFPL"
        }
        
        restricted_licenses = {
            "GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", 
            "AGPL-3.0", "SSPL-1.0"
        }
        
        for package_name, version in packages:
            try:
                package_info = await self.scan_package(package_name, version, ecosystem)
                
                package_compliance = {
                    "package": package_name,
                    "version": version,
                    "licenses": [license.name for license in package_info.licenses],
                    "compliance_status": "unknown",
                    "risk_level": "unknown"
                }
                
                if package_info.licenses:
                    license_names = {license.name for license in package_info.licenses}
                    
                    if license_names.intersection(restricted_licenses):
                        package_compliance["compliance_status"] = "non-compliant"
                        package_compliance["risk_level"] = "high"
                        compliance_results["non_compliant_packages"] += 1
                    elif license_names.intersection(allowed_licenses):
                        package_compliance["compliance_status"] = "compliant" 
                        package_compliance["risk_level"] = "low"
                        compliance_results["compliant_packages"] += 1
                    else:
                        package_compliance["compliance_status"] = "review_required"
                        package_compliance["risk_level"] = "medium"
                        compliance_results["unknown_licenses"] += 1
                else:
                    compliance_results["unknown_licenses"] += 1
                
                compliance_results["compliance_details"].append(package_compliance)
                
                # Update license summary
                for license in package_info.licenses:
                    if license.name not in compliance_results["license_summary"]:
                        compliance_results["license_summary"][license.name] = 0
                    compliance_results["license_summary"][license.name] += 1
                    
            except Exception as e:
                print(f"License check error for {package_name}: {e}", file=sys.stderr)
        
        return compliance_results
    
    async def monitor_project(self, project_path: str) -> Dict[str, Any]:
        """Set up continuous monitoring for a project"""
        
        # Find project dependencies
        dep_result = find_and_parse_dependencies(project_path)
        if not dep_result:
            return {"error": "No supported dependency files found"}
        
        filename, ecosystem, dependencies = dep_result
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Import project for monitoring
                import_payload = {
                    "target": {
                        "files": [
                            {
                                "path": filename,
                                "contents": self._generate_manifest_content(dependencies, ecosystem)
                            }
                        ]
                    }
                }
                
                if not self.org_id:
                    return {"error": "SNYK_ORG_ID environment variable is required for monitoring"}
                
                response = await client.post(
                    f"{self.rest_api_url}/orgs/{self.org_id}/projects",
                    headers=self._get_headers(),
                    json=import_payload
                )
                
                if response.status_code == 201:
                    project_data = response.json()
                    return {
                        "status": "monitoring_enabled",
                        "project_id": project_data.get("data", {}).get("id"),
                        "project_name": os.path.basename(project_path),
                        "dependencies_count": len(dependencies)
                    }
                else:
                    return {
                        "error": f"Failed to enable monitoring: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {"error": f"Monitoring setup failed: {str(e)}"}
    
    def _parse_package_scan_result(self, scan_data: Dict[str, Any], package_name: str, 
                                 version: str, ecosystem: str) -> SnykPackageInfo:
        """Parse Snyk scan result into SnykPackageInfo"""
        
        vulnerabilities = []
        licenses = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        # Parse vulnerabilities
        for issue in scan_data.get("issues", {}).get("vulnerabilities", []):
            vuln = self._parse_vulnerability(issue)
            vulnerabilities.append(vuln)
            
            severity_key = vuln.severity.value
            if severity_key in severity_counts:
                severity_counts[severity_key] += 1
        
        # Parse licenses
        for license_data in scan_data.get("issues", {}).get("licenses", []):
            license = self._parse_license(license_data)
            licenses.append(license)
        
        return SnykPackageInfo(
            name=package_name,
            version=version,
            ecosystem=ecosystem,
            vulnerabilities=vulnerabilities,
            licenses=licenses,
            severity_counts=severity_counts,
            dependency_paths=[],  # Would need more complex parsing
            is_direct_dependency=True
        )
    
    def _parse_project_scan_result(self, scan_data: Dict[str, Any], manifest_path: str) -> Dict[str, Any]:
        """Parse project-level scan results"""
        
        result = {
            "manifest_file": manifest_path,
            "scan_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_dependencies": scan_data.get("dependencyCount", 0),
                "vulnerability_count": len(scan_data.get("issues", {}).get("vulnerabilities", [])),
                "license_issues": len(scan_data.get("issues", {}).get("licenses", []))
            },
            "vulnerabilities": [],
            "license_issues": [],
            "remediation": scan_data.get("remediation", {})
        }
        
        # Process vulnerabilities
        for vuln_data in scan_data.get("issues", {}).get("vulnerabilities", []):
            vuln = self._parse_vulnerability(vuln_data)
            result["vulnerabilities"].append(vuln.to_vulnerability().to_dict())
        
        # Process license issues
        for license_data in scan_data.get("issues", {}).get("licenses", []):
            license = self._parse_license(license_data)
            result["license_issues"].append({
                "id": license.id,
                "name": license.name,
                "type": license.type,
                "is_deprecated": license.is_deprecated
            })
        
        return result
    
    def _parse_vulnerability(self, vuln_data: Dict[str, Any]) -> SnykVulnerability:
        """Parse vulnerability data from Snyk response"""
        
        severity_map = {
            "critical": SnykSeverity.CRITICAL,
            "high": SnykSeverity.HIGH,
            "medium": SnykSeverity.MEDIUM,
            "low": SnykSeverity.LOW
        }
        
        return SnykVulnerability(
            id=vuln_data.get("id", ""),
            title=vuln_data.get("title", ""),
            description=vuln_data.get("description", ""),
            severity=severity_map.get(vuln_data.get("severity", "medium"), SnykSeverity.MEDIUM),
            cvss_score=vuln_data.get("cvssScore"),
            cve=vuln_data.get("identifiers", {}).get("CVE", []),
            cwe=vuln_data.get("identifiers", {}).get("CWE", []),
            exploit_maturity=vuln_data.get("exploitMaturity"),
            patches=vuln_data.get("patches", []),
            upgrade_path=vuln_data.get("upgradePath", []),
            is_patchable=vuln_data.get("isPatchable", False),
            is_pinnable=vuln_data.get("isPinnable", False),
            published_date=vuln_data.get("publicationTime", ""),
            disclosure_time=vuln_data.get("disclosureTime")
        )
    
    def _parse_license(self, license_data: Dict[str, Any]) -> SnykLicense:
        """Parse license data from Snyk response"""
        
        return SnykLicense(
            id=license_data.get("id", ""),
            name=license_data.get("title", ""),
            spdx_id=license_data.get("license"),
            type=license_data.get("type", "unknown"),
            url=license_data.get("url"),
            is_deprecated=license_data.get("isDeprecated", False),
            instructions=license_data.get("instructions", "")
        )
    
    def _generate_manifest_content(self, dependencies: Dict[str, str], ecosystem: str) -> str:
        """Generate manifest file content for monitoring"""
        
        if ecosystem.lower() == "pypi":
            return "\n".join([f"{name}=={version}" for name, version in dependencies.items()])
        elif ecosystem.lower() == "npm":
            return json.dumps({"dependencies": dependencies}, indent=2)
        else:
            return str(dependencies)
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]["timestamp"]
        return datetime.now() - cached_time < self.cache_ttl
    
    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache scan result"""
        self.cache[cache_key] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        # Simple cache cleanup
        if len(self.cache) > 100:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]


# Global instance
snyk_integration = SnykIntegration()


async def get_snyk_security_report(library_name: str, version: str = "latest", 
                                 ecosystem: str = "pypi") -> SecurityReport:
    """Get security report using Snyk integration"""
    
    try:
        package_info = await snyk_integration.scan_package(library_name, version, ecosystem)
        
        # Convert Snyk vulnerabilities to standard format
        vulnerabilities = [vuln.to_vulnerability() for vuln in package_info.vulnerabilities]
        
        # Calculate security score based on Snyk data
        critical_count = package_info.severity_counts.get("critical", 0)
        high_count = package_info.severity_counts.get("high", 0)
        medium_count = package_info.severity_counts.get("medium", 0)
        low_count = package_info.severity_counts.get("low", 0)
        
        security_score = max(0.0, 100.0 - (critical_count * 25 + high_count * 15 + medium_count * 5 + low_count * 1))
        
        # Generate recommendations
        recommendations = []
        if critical_count > 0:
            recommendations.append("🚨 Critical vulnerabilities found - Update immediately")
        if package_info.vulnerabilities and any(vuln.upgrade_path for vuln in package_info.vulnerabilities):
            recommendations.append("📦 Security updates available - Consider upgrading")
        if security_score >= 80:
            recommendations.append("🛡️ Good security posture")
        elif security_score >= 60:
            recommendations.append("⚠️ Moderate risk - Monitor for updates")
        else:
            recommendations.append("🔴 High risk - Consider alternatives")
        
        return SecurityReport(
            library_name=library_name,
            ecosystem=ecosystem,
            scan_date=datetime.now().isoformat(),
            total_vulnerabilities=len(vulnerabilities),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            security_score=security_score,
            recommendations=recommendations,
            vulnerabilities=vulnerabilities,
            latest_secure_version=None  # Would need additional API call
        )
        
    except Exception as e:
        print(f"Snyk security report error: {e}", file=sys.stderr)
        # Return empty report on error
        return SecurityReport(
            library_name=library_name,
            ecosystem=ecosystem,
            scan_date=datetime.now().isoformat(),
            total_vulnerabilities=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            security_score=50.0,  # Neutral score
            recommendations=["Unable to fetch security data"],
            vulnerabilities=[],
            latest_secure_version=None
        )
