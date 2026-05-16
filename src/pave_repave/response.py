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
