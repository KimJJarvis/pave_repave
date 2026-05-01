#!/usr/bin/env python3
"""
Status dataclass for representing peer information status.
"""

from dataclasses import dataclass


@dataclass
class Status:
    """Represents the status of a peer in the cluster."""
    found: bool
    active_appliance: int
    primary_ip: str
    secondary_ip: str
    id: int

# Made with Bob
