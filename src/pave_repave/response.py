#!/usr/bin/env python3
"""
Response dataclass for representing API response information.
"""

from dataclasses import dataclass


@dataclass
class Response:
    """Represents an API response with message and status code."""

    message: str
    code: int

    def __str__(self) -> str:
        """Return string representation of the response."""
        return f"HTTP {self.code} {self.message}"
