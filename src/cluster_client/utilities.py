#!/usr/bin/env python3
"""
Utility functions for validation and common operations.
"""

import logging
import re
from collections.abc import Sequence

logger = logging.getLogger(__name__)


def setup_logging(level: str, log_file: str | None = None) -> None:
    """
    Configure logging for the application.
    Logs to both console and file (if file is specified) using multiple handlers.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to log to (in addition to console)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Setup handlers: always log to console, optionally log to file
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),  # console
    ]
    if log_file:
        handlers.append(logging.FileHandler(log_file))  # file

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


def _find_duplicates(values: Sequence[str | int]) -> list[str]:
    """Return duplicate values as sorted strings for error reporting."""
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(str(value) for value in duplicates)


def validate_unique_ips(*ips: str) -> None:
    """
    Validate that all provided IP addresses are valid and unique.

    Args:
        *ips: Variable number of IP address strings to validate

    Raises:
        ValueError: If any IP address is invalid or duplicated
    """
    invalid_ips = [ip for ip in ips if not validate_ip_address(ip)]
    if invalid_ips:
        raise ValueError(
            f"Invalid IP address(es) found: {', '.join(sorted(invalid_ips))}"
        )

    ip_list = list(ips)
    if len(ip_list) != len(set(ip_list)):
        duplicates = _find_duplicates(ip_list)
        raise ValueError(
            f"IP addresses must be unique. Duplicate IP(s) found: {', '.join(duplicates)}"
        )


def validate_unique_ports(*ports: int) -> None:
    """
    Validate that all provided port numbers are valid and unique.

    Args:
        *ports: Variable number of port numbers to validate

    Raises:
        ValueError: If any port number is invalid or duplicated
    """
    invalid_ports = [str(port) for port in ports if not validate_port(port)]
    if invalid_ports:
        raise ValueError(
            f"Invalid port number(s) found: {', '.join(sorted(invalid_ports, key=int))}"
        )

    port_list = list(ports)
    if len(port_list) != len(set(port_list)):
        duplicates = _find_duplicates(port_list)
        raise ValueError(
            f"Port numbers must be unique when port forwarding is enabled. Duplicate port(s) found: {', '.join(duplicates)}"
        )
