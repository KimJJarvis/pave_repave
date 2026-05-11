#!/usr/bin/env python3
"""
Utility functions for validation and common operations.
"""

import re
import sys


def validate_ip_address(ip: str) -> bool:
    """
    Validate that the IP address is in valid dot format (IPv4).
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid, False otherwise
    """
    # IPv4 pattern: four octets (0-255) separated by dots
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    match = re.match(pattern, ip)
    
    if not match:
        return False
    
    # Check that each octet is in range 0-255
    for octet in match.groups():
        if int(octet) > 255:
            return False
    
    return True


def validate_port(port: int) -> bool:
    """
    Validate that the port number is in valid range (0-65535).
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= port <= 65535


def validate_token_length(token: str, expected_length: int) -> bool:
    """
    Validate that a token has the expected length.
    
    Args:
        token: Token string to validate
        expected_length: Expected length of the token
        
    Returns:
        True if valid, False otherwise
    """
    return len(token) == expected_length


def exit_with_error(message: str) -> None:
    """
    Print an error message to stderr and exit with code 1.
    
    Args:
        message: Error message to display
    """
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(1)

# Made with Bob