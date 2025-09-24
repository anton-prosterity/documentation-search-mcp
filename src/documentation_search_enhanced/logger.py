"""
Enhanced logging module for documentation-search-enhanced MCP server.
Inspired by AWS MCP logging patterns.
"""

import logging
import os
import sys
import json
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Logging levels matching AWS MCP patterns"""

    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"


class StructuredLogger:
    """Structured logger with AWS MCP-style formatting"""

    def __init__(self, name: str = "documentation-search-enhanced"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Setup logger with environment-based configuration"""
        log_level = os.getenv("FASTMCP_LOG_LEVEL", "INFO").upper()

        # Map string levels to logging constants
        level_map = {
            "ERROR": logging.ERROR,
            "WARN": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
        }

        self.logger.setLevel(level_map.get(log_level, logging.INFO))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Create console handler
        handler = logging.StreamHandler(sys.stderr)

        # Create structured formatter
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def error(self, message: str, **kwargs):
        """Log error with structured data"""
        self._log(logging.ERROR, message, **kwargs)

    def warn(self, message: str, **kwargs):
        """Log warning with structured data"""
        self._log(logging.WARNING, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info with structured data"""
        self._log(logging.INFO, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug with structured data"""
        self._log(logging.DEBUG, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured data"""
        # Filter out None values and convert to strings
        filtered_kwargs = {
            k: str(v) if v is not None else "unknown" for k, v in kwargs.items()
        }

        extra = {
            "structured_data": filtered_kwargs,
            "server_name": self.name,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.logger.log(level, message, extra=extra)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""

    def format(self, record):
        """Format log record with structured data"""
        log_obj = {
            "timestamp": getattr(record, "timestamp", datetime.utcnow().isoformat()),
            "level": record.levelname,
            "server": getattr(record, "server_name", "documentation-search-enhanced"),
            "message": record.getMessage(),
        }

        # Add structured data if present
        structured_data = getattr(record, "structured_data", {})
        if structured_data:
            log_obj.update(structured_data)

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


class PerformanceTracker:
    """Track performance metrics like AWS MCP servers"""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.start_time = datetime.utcnow()

    def track_request(self, tool_name: str, library: str = None, query: str = None):
        """Track request metrics"""
        return RequestContext(self.logger, tool_name, library, query)


class RequestContext:
    """Context manager for tracking individual requests"""

    def __init__(
        self,
        logger: StructuredLogger,
        tool_name: str,
        library: str = None,
        query: str = None,
    ):
        self.logger = logger
        self.tool_name = tool_name
        self.library = library
        self.query = query
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(
            f"Starting {self.tool_name} request",
            tool_name=self.tool_name,
            library=self.library or "unknown",
            query_length=len(self.query) if self.query else 0,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return

        duration = (datetime.utcnow() - self.start_time).total_seconds()

        if exc_type:
            self.logger.error(
                f"Failed {self.tool_name} request",
                tool_name=self.tool_name,
                library=self.library or "unknown",
                duration_seconds=duration,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
            )
        else:
            self.logger.info(
                f"Completed {self.tool_name} request",
                tool_name=self.tool_name,
                library=self.library or "unknown",
                duration_seconds=duration,
            )


# Global logger instance
logger = StructuredLogger()
performance_tracker = PerformanceTracker(logger)
