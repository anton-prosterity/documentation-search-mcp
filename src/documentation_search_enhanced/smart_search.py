"""
Smart search features for documentation-search-enhanced MCP server.
Adds semantic search, relevance ranking, and contextual filtering.
"""

import re
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Enhanced search result with relevance scoring"""

    source_library: str
    url: str
    title: str
    snippet: str
    relevance_score: float
    content_type: str  # "tutorial", "reference", "example", "guide"
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    code_snippets_count: int
    estimated_read_time: int  # in minutes


class SmartSearch:
    """Enhanced search with semantic understanding and ranking"""

    def __init__(self):
        self.search_history = []
        self.user_preferences = {}
        self._docs_url_map: Dict[str, str] = {}
        self._search_fn: Optional[Callable[[str, int], Awaitable[Dict[str, Any]]]] = (
            None
        )
        self._results_limit = 5

    def configure(
        self,
        docs_url_map: Dict[str, str],
        search_fn: Callable[[str, int], Awaitable[Dict[str, Any]]],
        results_limit: int = 5,
    ) -> None:
        """Attach configuration provided by the runtime server."""

        self._docs_url_map = docs_url_map
        self._search_fn = search_fn
        self._results_limit = results_limit

    async def semantic_search(
        self, query: str, library: str, context: Optional[str] = None
    ) -> List[SearchResult]:
        """Perform semantic search with context awareness"""

        # Expand query with semantic understanding
        expanded_query = self.expand_query_semantically(query, library, context)

        # Search with expanded query
        base_query = f"site:{self.get_docs_url(library)} {expanded_query}"

        # Perform the actual search (using existing search infrastructure)
        raw_results = await self.perform_search(base_query)

        # Enhance and rank results
        enhanced_results = []
        for result in raw_results:
            enhanced_result = await self.enhance_search_result(result, query, library)
            enhanced_results.append(enhanced_result)

        # Sort by relevance score
        enhanced_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return enhanced_results

    def expand_query_semantically(
        self, query: str, library: str, context: Optional[str] = None
    ) -> str:
        """Expand query with semantically related terms"""
        expanded_terms = [query]

        # Library-specific semantic expansions
        semantic_expansions = {
            "fastapi": {
                "auth": ["authentication", "security", "JWT", "OAuth", "middleware"],
                "database": ["SQLAlchemy", "ORM", "models", "async database"],
                "api": ["endpoints", "routes", "REST", "OpenAPI", "swagger"],
                "middleware": ["CORS", "authentication", "logging", "request"],
                "async": ["asyncio", "concurrent", "await", "asynchronous"],
            },
            "react": {
                "state": ["useState", "setState", "hooks", "context"],
                "component": ["JSX", "props", "lifecycle", "functional"],
                "routing": ["React Router", "navigation", "link"],
                "forms": ["controlled", "uncontrolled", "validation"],
                "hooks": ["useEffect", "useState", "useContext", "custom hooks"],
            },
            "django": {
                "auth": ["authentication", "permissions", "user model", "login"],
                "database": ["models", "ORM", "migrations", "queries"],
                "views": ["class-based", "function-based", "generic views"],
                "forms": ["ModelForm", "validation", "widgets"],
                "admin": ["admin interface", "ModelAdmin", "customization"],
            },
            "langchain": {
                "chains": ["LLMChain", "sequential", "pipeline", "workflow"],
                "agents": ["tools", "ReAct", "planning", "execution"],
                "memory": ["conversation", "buffer", "summary", "retrieval"],
                "embeddings": ["vector", "similarity", "semantic search"],
                "retrieval": ["RAG", "documents", "vector store", "similarity"],
            },
        }

        # Add semantic expansions for the library
        if library in semantic_expansions:
            for key_term, expansions in semantic_expansions[library].items():
                if key_term.lower() in query.lower():
                    expanded_terms.extend(expansions)

        # Add context-based expansions
        if context:
            context_terms = self.extract_context_terms(context, library)
            expanded_terms.extend(context_terms)

        # Common technical term expansions
        common_expansions = {
            "error": ["exception", "troubleshooting", "debugging", "fix"],
            "performance": ["optimization", "speed", "efficient", "benchmark"],
            "security": ["authentication", "authorization", "encryption", "safety"],
            "testing": ["unit test", "pytest", "mock", "coverage"],
            "deployment": ["production", "docker", "hosting", "cloud"],
        }

        for term, expansions in common_expansions.items():
            if term in query.lower():
                expanded_terms.extend(expansions)

        # Limit expansion to avoid over-broad results
        unique_terms = list(set(expanded_terms))[:8]
        return " ".join(unique_terms)

    def extract_context_terms(self, context: str, library: str) -> List[str]:
        """Extract relevant terms from user context"""
        context_terms = []

        # Extract mentioned technologies
        tech_patterns = [
            r"\b(react|vue|angular|svelte)\b",
            r"\b(fastapi|django|flask|express)\b",
            r"\b(python|javascript|typescript|node)\b",
            r"\b(docker|kubernetes|aws|azure)\b",
            r"\b(postgresql|mysql|mongodb|redis)\b",
        ]

        for pattern in tech_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            context_terms.extend([match.group(1).lower() for match in matches])

        # Extract use case indicators
        use_case_patterns = {
            r"\b(api|rest|graphql)\b": ["endpoint", "server", "client"],
            r"\b(frontend|ui|interface)\b": ["component", "styling", "interaction"],
            r"\b(database|data|storage)\b": ["model", "query", "migration"],
            r"\b(auth|login|user)\b": ["permission", "session", "token"],
        }

        for pattern, related_terms in use_case_patterns.items():
            if re.search(pattern, context, re.IGNORECASE):
                context_terms.extend(related_terms)

        return context_terms[:5]  # Limit context expansion

    async def enhance_search_result(
        self, raw_result: Dict[str, Any], query: str, library: str
    ) -> SearchResult:
        """Enhance a raw search result with additional metadata"""

        # Calculate relevance score
        relevance_score = self.calculate_relevance_score(raw_result, query, library)

        # Determine content type
        content_type = self.classify_content_type(
            raw_result.get("title", ""), raw_result.get("snippet", "")
        )

        # Assess difficulty level
        difficulty_level = self.assess_difficulty_level(raw_result.get("snippet", ""))

        # Count code snippets (estimate from snippet)
        code_snippets_count = self.estimate_code_snippets(raw_result.get("snippet", ""))

        # Estimate reading time
        estimated_read_time = self.estimate_reading_time(raw_result.get("snippet", ""))

        return SearchResult(
            source_library=library,
            url=raw_result.get("link", ""),
            title=raw_result.get("title", ""),
            snippet=raw_result.get("snippet", ""),
            relevance_score=relevance_score,
            content_type=content_type,
            difficulty_level=difficulty_level,
            code_snippets_count=code_snippets_count,
            estimated_read_time=estimated_read_time,
        )

    def calculate_relevance_score(
        self, result: Dict[str, Any], query: str, library: str
    ) -> float:
        """Calculate relevance score for a search result"""
        score = 0.0

        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Title relevance (high weight)
        title_words = set(title.split())
        title_match_ratio = (
            len(query_words.intersection(title_words)) / len(query_words)
            if query_words
            else 0
        )
        score += title_match_ratio * 40

        # Snippet relevance (medium weight)
        snippet_words = set(snippet.split())
        snippet_match_ratio = (
            len(query_words.intersection(snippet_words)) / len(query_words)
            if query_words
            else 0
        )
        score += snippet_match_ratio * 30

        # Exact phrase matches (high bonus)
        if query_lower in title:
            score += 20
        elif query_lower in snippet:
            score += 15

        # Library-specific bonuses
        library_keywords = {
            "fastapi": ["endpoint", "pydantic", "async", "uvicorn", "api"],
            "react": ["component", "jsx", "hooks", "state", "props"],
            "django": ["model", "view", "template", "admin", "orm"],
        }

        if library in library_keywords:
            for keyword in library_keywords[library]:
                if keyword in snippet:
                    score += 5

        # Content type bonuses
        if "example" in title or "tutorial" in title:
            score += 10
        elif "guide" in title or "documentation" in title:
            score += 5

        # Code presence bonus
        if "```" in snippet or "<code>" in snippet or "def " in snippet:
            score += 8

        return min(score, 100.0)  # Cap at 100

    def classify_content_type(self, title: str, snippet: str) -> str:
        """Classify the type of documentation content"""
        title_lower = title.lower()
        snippet_lower = snippet.lower()

        # Tutorial indicators
        if any(
            word in title_lower
            for word in ["tutorial", "guide", "walkthrough", "step-by-step"]
        ):
            return "tutorial"

        # Example indicators
        if any(
            word in title_lower for word in ["example", "demo", "sample", "cookbook"]
        ):
            return "example"

        # Reference indicators
        if any(
            word in title_lower
            for word in ["api", "reference", "documentation", "docs"]
        ):
            return "reference"

        # Check snippet for patterns
        if any(
            phrase in snippet_lower
            for phrase in ["let's", "first", "getting started", "how to"]
        ):
            return "tutorial"
        elif (
            "class " in snippet_lower
            or "function " in snippet_lower
            or "method " in snippet_lower
        ):
            return "reference"
        elif "example" in snippet_lower or "demo" in snippet_lower:
            return "example"

        return "guide"  # Default

    def assess_difficulty_level(self, snippet: str) -> str:
        """Assess the difficulty level of content"""
        snippet_lower = snippet.lower()
        difficulty_score = 0

        # Beginner indicators
        beginner_terms = [
            "basic",
            "simple",
            "introduction",
            "getting started",
            "quick start",
            "hello world",
        ]
        difficulty_score -= sum(2 for term in beginner_terms if term in snippet_lower)

        # Advanced indicators
        advanced_terms = [
            "advanced",
            "complex",
            "optimization",
            "performance",
            "architecture",
            "async",
            "concurrent",
            "decorator",
            "metaclass",
            "inheritance",
        ]
        difficulty_score += sum(1 for term in advanced_terms if term in snippet_lower)

        # Code complexity indicators
        complex_patterns = [r"\bclass\s+\w+", r"\bdef\s+\w+", r"\basync\s+def", r"@\w+"]
        difficulty_score += sum(
            1 for pattern in complex_patterns if re.search(pattern, snippet_lower)
        )

        if difficulty_score >= 3:
            return "advanced"
        elif difficulty_score >= 1:
            return "intermediate"
        else:
            return "beginner"

    def estimate_code_snippets(self, snippet: str) -> int:
        """Estimate number of code snippets in content"""
        code_indicators = [
            "```",
            "<code>",
            "<pre>",
            "def ",
            "class ",
            "function ",
            "const ",
            "let ",
            "var ",
        ]

        count = 0
        for indicator in code_indicators:
            count += snippet.count(indicator)

        # Rough estimate: assume each indicator represents part of a snippet
        return min(count // 2, 10)  # Cap at 10

    def estimate_reading_time(self, snippet: str) -> int:
        """Estimate reading time in minutes"""
        words = len(snippet.split())

        # Average reading speed: 200-250 words per minute
        # Factor in code reading (slower)
        code_ratio = (snippet.count("```") + snippet.count("<code>")) / max(
            len(snippet), 1
        )
        effective_wpm = 200 - (code_ratio * 100)  # Slower for code-heavy content

        # Estimate full content is 5-10x longer than snippet
        estimated_full_words = words * 7
        reading_time = max(1, estimated_full_words / effective_wpm)

        return int(reading_time)

    async def perform_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform the actual search (placeholder - integrate with existing search)"""
        if not self._search_fn:
            raise RuntimeError("SmartSearch search function not configured")

        search_response = await self._search_fn(query, self._results_limit)
        organic_results = (
            search_response.get("organic", [])
            if isinstance(search_response, dict)
            else []
        )
        return organic_results[: self._results_limit]

    def get_docs_url(self, library: str) -> str:
        """Get documentation URL for a library"""
        if self._docs_url_map:
            return self._docs_url_map.get(library, "docs.example.com")
        return "docs.example.com"


@dataclass
class SearchFilters:
    """Filters for refining search results"""

    content_type: Optional[str] = None  # "tutorial", "reference", "example"
    difficulty_level: Optional[str] = None  # "beginner", "intermediate", "advanced"
    has_code_examples: Optional[bool] = None
    max_reading_time: Optional[int] = None  # in minutes
    language: Optional[str] = None  # programming language


class FilteredSearch:
    """Search with advanced filtering capabilities"""

    def __init__(self, smart_search: SmartSearch):
        self.smart_search = smart_search

    async def search_with_filters(
        self, query: str, library: str, filters: SearchFilters
    ) -> List[SearchResult]:
        """Perform search with applied filters"""

        # Get base search results
        results = await self.smart_search.semantic_search(query, library)

        # Apply filters
        filtered_results = []
        for result in results:
            if self.passes_filters(result, filters):
                filtered_results.append(result)

        return filtered_results

    def passes_filters(self, result: SearchResult, filters: SearchFilters) -> bool:
        """Check if a result passes all filters"""

        if filters.content_type and result.content_type != filters.content_type:
            return False

        if (
            filters.difficulty_level
            and result.difficulty_level != filters.difficulty_level
        ):
            return False

        if filters.has_code_examples is not None:
            has_code = result.code_snippets_count > 0
            if filters.has_code_examples != has_code:
                return False

        if (
            filters.max_reading_time
            and result.estimated_read_time > filters.max_reading_time
        ):
            return False

        # Language filter would need more sophisticated detection
        # For now, skip language filtering

        return True


# Global instances
smart_search = SmartSearch()
filtered_search = FilteredSearch(smart_search)
