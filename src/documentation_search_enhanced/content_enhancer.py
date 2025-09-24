"""
Content enhancement features for documentation-search-enhanced MCP server.
Adds smart parsing, code extraction, version awareness, and contextual recommendations.
"""

import re
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import httpx
from datetime import datetime, timedelta


@dataclass
class CodeSnippet:
    """Represents an extracted code snippet"""

    language: str
    code: str
    description: str
    line_number: Optional[int] = None
    is_complete: bool = False
    imports: List[str] = None

    def __post_init__(self):
        if self.imports is None:
            self.imports = []


@dataclass
class DocumentationSection:
    """Represents a section of documentation"""

    title: str
    content: str
    code_snippets: List[CodeSnippet]
    cross_references: List[str]
    section_type: str  # "tutorial", "reference", "example", "guide"
    difficulty_level: str  # "beginner", "intermediate", "advanced"


SUMMARIZER_ENDPOINT = os.getenv("SUMMARY_API_URL")
SUMMARIZER_KEY = os.getenv("SUMMARY_API_KEY")


class ContentEnhancer:
    """Enhances documentation content with smart parsing and features"""

    def __init__(self):
        self.version_cache = {}
        self.cross_ref_cache = {}

    async def enhance_content(
        self, content: str, library: str, query: str
    ) -> Dict[str, Any]:
        """Main content enhancement pipeline"""
        enhanced = {
            "original_content": content,
            "library": library,
            "query": query,
            "enhanced_at": datetime.utcnow().isoformat(),
            "enhancements": {},
        }

        # Extract and enhance code snippets
        code_snippets = self.extract_code_snippets(content)
        enhanced["enhancements"]["code_snippets"] = [
            {
                "language": snippet.language,
                "code": snippet.code,
                "description": snippet.description,
                "is_complete": snippet.is_complete,
                "imports": snippet.imports,
            }
            for snippet in code_snippets
        ]

        # Parse into structured sections
        sections = self.parse_sections(content)
        enhanced["enhancements"]["sections"] = [
            {
                "title": section.title,
                "content": (
                    section.content[:500] + "..."
                    if len(section.content) > 500
                    else section.content
                ),
                "section_type": section.section_type,
                "difficulty_level": section.difficulty_level,
                "code_count": len(section.code_snippets),
            }
            for section in sections
        ]

        # Add contextual recommendations
        enhanced["enhancements"]["recommendations"] = (
            await self.get_contextual_recommendations(library, query)
        )

        # Extract and resolve cross-references
        enhanced["enhancements"]["cross_references"] = self.extract_cross_references(
            content, library
        )

        # Add version information
        enhanced["enhancements"]["version_info"] = await self.get_version_info(library)

        # Generate quick summary
        enhanced["enhancements"]["summary"] = self.generate_summary(content, query)

        return enhanced

    def extract_code_snippets(self, content: str) -> List[CodeSnippet]:
        """Extract and analyze code snippets from content"""
        snippets = []

        # Patterns for different code block formats
        patterns = [
            r"```(\w+)?\n(.*?)```",  # Markdown code blocks
            r"<code[^>]*>(.*?)</code>",  # HTML code tags
            r"<pre[^>]*><code[^>]*>(.*?)</code></pre>",  # HTML pre+code
            r".. code-block:: (\w+)\n\n(.*?)(?=\n\S|\Z)",  # reStructuredText
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    language = match.group(1) or "text"
                    code = match.group(2).strip()
                else:
                    language = "text"
                    code = match.group(1).strip()

                if len(code) > 10:  # Filter out very short snippets
                    snippet = self.analyze_code_snippet(code, language)
                    snippets.append(snippet)

        return snippets

    def analyze_code_snippet(self, code: str, language: str) -> CodeSnippet:
        """Analyze a code snippet for completeness and imports"""
        description = self.generate_code_description(code, language)
        imports = self.extract_imports(code, language)
        is_complete = self.is_code_complete(code, language)

        return CodeSnippet(
            language=language.lower(),
            code=code,
            description=description,
            is_complete=is_complete,
            imports=imports,
        )

    def generate_code_description(self, code: str, language: str) -> str:
        """Generate a description for a code snippet"""
        # Common patterns and descriptions
        patterns = {
            # Python patterns
            r"def\s+(\w+)": "Function definition: {}",
            r"class\s+(\w+)": "Class definition: {}",
            r"import\s+(\w+)": "Import: {}",
            r"from\s+(\w+)\s+import": "Import from: {}",
            r"@\w+": "Decorator usage",
            r"async\s+def": "Async function definition",
            r'if\s+__name__\s*==\s*["\']__main__["\']': "Main execution block",
            # JavaScript patterns
            r"function\s+(\w+)": "Function: {}",
            r"const\s+(\w+)": "Constant: {}",
            r"let\s+(\w+)": "Variable: {}",
            r"export\s+": "Export statement",
            r"import\s+.*from": "Import statement",
            # FastAPI/web patterns
            r"@app\.(get|post|put|delete)": "API endpoint definition",
            r"FastAPI\(\)": "FastAPI application initialization",
            r"app\s*=\s*FastAPI": "FastAPI app creation",
        }

        descriptions = []
        for pattern, desc in patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                if "{}" in desc and len(match.groups()) > 0:
                    descriptions.append(desc.format(match.group(1)))
                else:
                    descriptions.append(desc)

        if descriptions:
            return "; ".join(descriptions[:3])  # Limit to first 3 descriptions
        else:
            return f"{language.title()} code snippet"

    def extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements from code"""
        imports = []

        if language.lower() in ["python", "py"]:
            # Python imports
            import_patterns = [r"import\s+([^\s,\n]+)", r"from\s+([^\s,\n]+)\s+import"]
            for pattern in import_patterns:
                matches = re.finditer(pattern, code, re.MULTILINE)
                imports.extend([match.group(1) for match in matches])

        elif language.lower() in ["javascript", "js", "typescript", "ts"]:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import\s+.*from\s+["\']([^"\']+)["\']',
                r'require\(["\']([^"\']+)["\']\)',
            ]
            for pattern in import_patterns:
                matches = re.finditer(pattern, code)
                imports.extend([match.group(1) for match in matches])

        return list(set(imports))  # Remove duplicates

    def is_code_complete(self, code: str, language: str) -> bool:
        """Determine if a code snippet is complete/runnable"""
        code = code.strip()

        # Check for common completeness indicators
        completeness_indicators = {
            "python": [
                r'if\s+__name__\s*==\s*["\']__main__["\']',  # Main block
                r"def\s+\w+.*:\s*\n.*return",  # Function with return
                r"class\s+\w+.*:\s*\n.*def\s+__init__",  # Class with constructor
            ],
            "javascript": [
                r"function\s+\w+.*{.*}",  # Complete function
                r".*\.exports\s*=",  # Module export
                r"export\s+default",  # ES6 export
            ],
        }

        lang_key = language.lower()
        if lang_key in completeness_indicators:
            for pattern in completeness_indicators[lang_key]:
                if re.search(pattern, code, re.DOTALL):
                    return True

        # Basic completeness checks
        if language.lower() in ["python", "py"]:
            # Check for balanced brackets and basic structure
            return (
                code.count("(") == code.count(")")
                and code.count("[") == code.count("]")
                and code.count("{") == code.count("}")
                and len(code.split("\n")) >= 3
            )

        return len(code) > 50  # Fallback: assume longer snippets are more complete

    def parse_sections(self, content: str) -> List[DocumentationSection]:
        """Parse content into structured sections"""
        sections = []

        # Split by headers (markdown and HTML)
        header_patterns = [
            r"^#{1,6}\s+(.+)$",  # Markdown headers
            r"<h[1-6][^>]*>(.*?)</h[1-6]>",  # HTML headers
        ]

        current_section = ""
        current_title = "Introduction"

        lines = content.split("\n")
        for line in lines:
            is_header = False
            for pattern in header_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous section if it has content
                    if current_section.strip():
                        section = self.create_section(current_title, current_section)
                        sections.append(section)

                    # Start new section
                    current_title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                    current_section = ""
                    is_header = True
                    break

            if not is_header:
                current_section += line + "\n"

        # Add final section
        if current_section.strip():
            section = self.create_section(current_title, current_section)
            sections.append(section)

        return sections

    def create_section(self, title: str, content: str) -> DocumentationSection:
        """Create a DocumentationSection with analysis"""
        code_snippets = self.extract_code_snippets(content)
        cross_refs = self.extract_cross_references(content, "")
        section_type = self.classify_section_type(title, content)
        difficulty = self.assess_difficulty(title, content, code_snippets)

        return DocumentationSection(
            title=title,
            content=content,
            code_snippets=code_snippets,
            cross_references=cross_refs,
            section_type=section_type,
            difficulty_level=difficulty,
        )

    def classify_section_type(self, title: str, content: str) -> str:
        """Classify the type of documentation section"""
        title_lower = title.lower()
        content_lower = content.lower()

        # Classification patterns
        if any(
            word in title_lower for word in ["tutorial", "guide", "walkthrough", "step"]
        ):
            return "tutorial"
        elif any(word in title_lower for word in ["example", "demo", "sample"]):
            return "example"
        elif any(word in title_lower for word in ["api", "reference", "documentation"]):
            return "reference"
        elif any(
            word in content_lower
            for word in ["first", "getting started", "quickstart", "introduction"]
        ):
            return "guide"
        else:
            return "guide"  # Default

    def assess_difficulty(
        self, title: str, content: str, code_snippets: List[CodeSnippet]
    ) -> str:
        """Assess the difficulty level of a section"""
        difficulty_score = 0

        # Title indicators
        title_lower = title.lower()
        if any(
            word in title_lower for word in ["advanced", "expert", "deep", "complex"]
        ):
            difficulty_score += 3
        elif any(word in title_lower for word in ["intermediate", "moderate"]):
            difficulty_score += 2
        elif any(word in title_lower for word in ["basic", "simple", "intro", "quick"]):
            difficulty_score += 1

        # Content complexity indicators
        content_lower = content.lower()

        # Advanced concepts
        advanced_terms = [
            "async",
            "concurrent",
            "threading",
            "multiprocessing",
            "decorator",
            "metaclass",
            "inheritance",
            "polymorphism",
            "dependency injection",
        ]
        difficulty_score += (
            sum(1 for term in advanced_terms if term in content_lower) * 0.5
        )

        # Code complexity
        if code_snippets:
            avg_code_length = sum(len(snippet.code) for snippet in code_snippets) / len(
                code_snippets
            )
            if avg_code_length > 200:
                difficulty_score += 2
            elif avg_code_length > 100:
                difficulty_score += 1

        # Return difficulty level
        if difficulty_score >= 4:
            return "advanced"
        elif difficulty_score >= 2:
            return "intermediate"
        else:
            return "beginner"

    def extract_cross_references(self, content: str, library: str) -> List[str]:
        """Extract cross-references to other libraries or concepts"""
        cross_refs = []

        # Common library mentions
        library_patterns = [
            r"\b(fastapi|django|flask|express|react|vue|angular)\b",
            r"\b(numpy|pandas|matplotlib|scikit-learn)\b",
            r"\b(tensorflow|pytorch|keras)\b",
            r"\b(docker|kubernetes|aws|azure|gcp)\b",
        ]

        for pattern in library_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            cross_refs.extend([match.group(1).lower() for match in matches])

        # Remove the current library from cross-references
        cross_refs = [ref for ref in cross_refs if ref != library.lower()]

        return list(set(cross_refs))  # Remove duplicates

    async def get_contextual_recommendations(
        self, library: str, query: str
    ) -> List[Dict[str, str]]:
        """Get contextual recommendations based on library and query"""
        recommendations = []

        # Library-specific recommendations
        lib_recommendations = {
            "fastapi": [
                {
                    "type": "related_library",
                    "name": "pydantic",
                    "reason": "Data validation and settings",
                },
                {
                    "type": "related_library",
                    "name": "uvicorn",
                    "reason": "ASGI server for FastAPI",
                },
                {
                    "type": "concept",
                    "name": "async/await",
                    "reason": "Essential for FastAPI performance",
                },
            ],
            "react": [
                {
                    "type": "related_library",
                    "name": "typescript",
                    "reason": "Type safety for React applications",
                },
                {
                    "type": "related_library",
                    "name": "tailwind",
                    "reason": "Utility-first CSS framework",
                },
                {"type": "concept", "name": "hooks", "reason": "Modern React pattern"},
            ],
            "django": [
                {
                    "type": "related_library",
                    "name": "django-rest-framework",
                    "reason": "API development",
                },
                {
                    "type": "related_library",
                    "name": "celery",
                    "reason": "Background tasks",
                },
                {"type": "concept", "name": "orm", "reason": "Database abstraction"},
            ],
        }

        if library.lower() in lib_recommendations:
            recommendations.extend(lib_recommendations[library.lower()])

        # Query-specific recommendations
        query_lower = query.lower()
        if "auth" in query_lower:
            recommendations.append(
                {
                    "type": "security",
                    "name": "JWT tokens",
                    "reason": "Secure authentication method",
                }
            )
        elif "database" in query_lower:
            recommendations.append(
                {
                    "type": "related_library",
                    "name": "sqlalchemy",
                    "reason": "Python SQL toolkit and ORM",
                }
            )
        elif "api" in query_lower:
            recommendations.append(
                {
                    "type": "concept",
                    "name": "REST principles",
                    "reason": "API design best practices",
                }
            )

        return recommendations[:5]  # Limit to 5 recommendations

    async def get_version_info(self, library: str) -> Dict[str, Any]:
        """Get version information for a library"""
        if library in self.version_cache:
            cached_time, version_info = self.version_cache[library]
            if datetime.now() - cached_time < timedelta(hours=24):
                return version_info

        version_info = {
            "current_version": "unknown",
            "release_date": "unknown",
            "is_latest": True,
            "changelog_url": None,
        }

        try:
            # Try to get version info from PyPI for Python packages
            if library in ["fastapi", "django", "flask", "pandas", "numpy"]:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://pypi.org/pypi/{library}/json", timeout=5.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        version_info.update(
                            {
                                "current_version": data["info"]["version"],
                                "release_date": data["releases"][
                                    data["info"]["version"]
                                ][0]["upload_time"][:10],
                                "changelog_url": data["info"]
                                .get("project_urls", {})
                                .get("Changelog"),
                            }
                        )
        except Exception:
            pass  # Fallback to unknown version

        # Cache the result
        self.version_cache[library] = (datetime.now(), version_info)
        return version_info

    def generate_summary(self, content: str, query: str) -> str:
        """Generate a concise summary of the content"""
        if SUMMARIZER_ENDPOINT and SUMMARIZER_KEY:
            try:
                payload = {"query": query, "context": content[:4000]}
                headers = {
                    "Authorization": f"Bearer {SUMMARIZER_KEY}",
                    "Content-Type": "application/json",
                }
                response = httpx.post(
                    SUMMARIZER_ENDPOINT, json=payload, headers=headers, timeout=15
                )
                response.raise_for_status()
                data = response.json()
                summary = data.get("summary") or data.get("result")
                if summary:
                    return summary
            except Exception as exc:
                print(f"⚠️ LLM summarization failed: {exc}", file=sys.stderr)

        sentences = re.split(r"[.!?]+", content)
        query_words = set(query.lower().split())
        scored_sentences: List[tuple[int, str]] = []

        for sentence in sentences[:10]:
            sentence = sentence.strip()
            if len(sentence) > 20:
                words = set(sentence.lower().split())
                score = len(query_words.intersection(words))
                scored_sentences.append((score, sentence))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [sent for score, sent in scored_sentences[:3] if score > 0]

        if top_sentences:
            return ". ".join(top_sentences)[:300] + "..."

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                return sentence[:300] + "..."

        return "Documentation content for " + query


# Global content enhancer instance
content_enhancer = ContentEnhancer()
