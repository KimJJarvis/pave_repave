#!/usr/bin/env python3
"""
Utility functions for validation and common operations.
"""

import re
import sys
import logging

logger = logging.getLogger(__name__)


def setup_logging(level: str, log_file: str | None = None) -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to log to (in addition to console)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Route to console, file, or both
    handlers = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def validate_ip_format(ip: str) -> bool:
    """
    Validate that the IP address is in valid dot format (IPv4).

    Args:
        ip: IP address string to validate

    Returns:
        True if valid format, False otherwise
    """
    # IPv4 pattern: four octets (0-255) separated by dots
    pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    match = re.match(pattern, ip)

    if not match:
        return False

    octets = [int(octet) for octet in match.groups()]

    # Check that each octet is in range 0-255
    if any(octet > 255 for octet in octets):
        return False

    return True


def validate_ip_address(ip: str) -> bool:
    """
    Validate that the IP address is in valid dot format (IPv4) and not a loopback address.

    Args:
        ip: IP address string to validate

    Returns:
        True if valid and not loopback, False otherwise
    """
    # First validate the format
    if not validate_ip_format(ip):
        return False

    # Extract octets to check for loopback
    octets = [int(octet) for octet in ip.split(".")]

    # Loopback addresses are not valid for this application
    if octets[0] == 127:
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


def validate_unique_ips(*ips: str) -> None:
    """
    Validate that all provided IP addresses are unique.

    Args:
        *ips: Variable number of IP address strings to validate

    Raises:
        ValueError: If any IP addresses are duplicated
    """
    ip_list = list(ips)
    if len(ip_list) != len(set(ip_list)):
        # Find duplicates for better error message
        seen = set()
        duplicates = set()
        for ip in ip_list:
            if ip in seen:
                duplicates.add(ip)
            seen.add(ip)
        raise ValueError(
            f"IP addresses must be unique. Duplicate IP(s) found: {', '.join(sorted(duplicates))}"
        )


def exit_with_error(message: str) -> None:
    """
    Log an error message and exit with code 1.

    Args:
        message: Error message to display
    """
    logger.error(message)
    sys.exit(1)

