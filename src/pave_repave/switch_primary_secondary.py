#!/usr/bin/env python3
"""
Script to perform switch-primary-secondary operation using NMS API.
Determines the peer ID and calls the switch-primary-secondary endpoint on porta.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.response import Response
from pave_repave.make_single_api_request import make_single_api_request
from pave_repave.utilities import setup_logging

logger = logging.getLogger(__name__)


def switch_primary_secondary(node: Node, id: int) -> Response:
    """
    Call the switch-primary-secondary endpoint.

    Args:
        node: Node object with connection details
        id: Peer ID

    Returns:
        Response object with message and status code
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/switch-primary-secondary"
    logger.info(f"Calling switch-primary-secondary on {url}...")

    data = {"peerId": str(id)}

    api_response = make_single_api_request(url=url, bearer_token=node.token, method="POST", data=data)

    # Get HTTP status code if present (added by make_single_api_request for error responses)
    http_status = api_response.get("_http_status_code", 200)

    # Parse the response - check statusMessage, message, and error fields
    status_message = api_response.get("statusMessage", "")
    message_field = api_response.get("message", "")
    error_field = api_response.get("error", "")

    # Determine message and code based on response
    if (
        message_field
        == "The primary / secondary appliance roles on this peer have been switched."
    ):
        message = (
            "The primary / secondary appliance roles on this peer have been switched"
        )
        code = 200
    elif "LeaderFollower Job Active, cannot switch-primary-secondary" in (
        status_message or error_field
    ):
        message = "LeaderFollower Job Active, cannot switch-primary-secondary"
        code = http_status  # Use actual HTTP status code (likely 400)
    else:
        # For all other responses, copy the message and use the HTTP status code
        # Prefer statusMessage, then error, then message field
        message = (
            (status_message or error_field or message_field).strip()
            if (status_message or error_field or message_field)
            else "Unknown response"
        )
        code = http_status

    response = Response(message=message, code=code)
    logger.info(
        f"✓ switch-primary-secondary completed: {response.message} (code: {response.code})"
    )

    return response


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Perform switch-primary-secondary operation using NMS API"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Log to file instead of console"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Bearer token for authentication",
    )
    parser.add_argument("--ip", required=True, help="IP address")
    parser.add_argument("--port", required=True, type=int, help="Port number for host")
    parser.add_argument("--id", required=True, type=int, help="Peer ID")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    logger.debug("Starting switch-primary-secondary.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Token: {args.token[:20]}...")
    logger.debug(f"  IP: {args.ip}")
    logger.debug(f"  Port: {args.port}")
    logger.debug(f"  ID: {args.id}")

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"

    logger.info("=" * 60)
    logger.info("Switch Primary-Secondary Operation")
    logger.info("=" * 60)
    logger.info(f"Target: {base_url} (forwarded to {node.ip})")
    logger.info(f"Peer ID: {args.id}")
    logger.info("=" * 60)

    # Call switch-primary-secondary
    logger.info("Calling switch-primary-secondary...")
    response = switch_primary_secondary(node=node, id=args.id)

    # Log the response as an info message
    logger.info("\nResponse:")
    logger.info(json.dumps({"message": response.message, "code": response.code}, indent=2))

    logger.info("=" * 60)
    if response.code == 200:
        logger.info("✓ Operation completed successfully!")
        print("✓ Operation completed successfully!")
    else:
        logger.warning(f"⚠ Operation completed with code {response.code}")
        print(f"⚠ Operation completed with code {response.code}")
    logger.info("=" * 60)
