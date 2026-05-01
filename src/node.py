#!/usr/bin/env python3
"""
Node dataclass for representing a cluster node.
"""

from dataclasses import dataclass


@dataclass
class Node:
    """Represents a cluster node with connection details."""
    port: int
    token: str
    ip: str

# Made with Bob
