#!/usr/bin/env python3
"""
Node model for representing a cluster node.
"""

from pydantic import BaseModel, field_validator

from pave_repave.utilities import validate_ip_format, validate_port, validate_token_length


class Node(BaseModel):
    """Represents a cluster node with connection details."""

    port: int
    token: str
    ip: str

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        """Validate node IP address."""
        if not validate_ip_format(value):
            msg = f"Invalid IP address: {value}"
            raise ValueError(msg)
        return value

    @field_validator("port")
    @classmethod
    def validate_node_port(cls, value: int) -> int:
        """Validate node port."""
        if not validate_port(value):
            msg = f"Invalid port: {value}"
            raise ValueError(msg)
        return value

    @field_validator("token")
    @classmethod
    def validate_node_token(cls, value: str) -> str:
        """Validate node token length."""
        if not validate_token_length(value, 361):
            msg = f"Invalid token length: expected 361 characters, got {len(value)}"
            raise ValueError(msg)
        return value
