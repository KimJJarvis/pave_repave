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
from pave_repave.get_token import get_token

logger = logging.getLogger(__name__)


def switch_primary_secondary(node: Node, id: int) -> None:
    """
    Call the switch-primary-secondary endpoint with retry logic.

    Args:
        node: Node object with connection details
        id: Peer ID

    Raises:
        RuntimeError: If the API returns HTTP 400 or unexpected response
    """
    import time
    
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/switch-primary-secondary"
    logger.info(f"Calling switch-primary-secondary on {url}...")

    data = {"peerId": str(id)}

    while True:
        api_response = make_single_api_request(url=url, bearer_token=node.token, method="POST", data=data)

        # Get HTTP status code if present (added by make_single_api_request for error responses)
        http_status = api_response.get("_http_status_code", 200)

        # Parse the response - check statusMessage, message, and error fields
        status_message = api_response.get("statusMessage", "")
        message_field = api_response.get("message", "")
        error_field = api_response.get("error", "")

        # Check for LeaderFollower Job Active - retry after delay
        if "LeaderFollower Job Active, cannot switch-primary-secondary" in (
            status_message or error_field
        ):
            logger.warning(
                "⚠ LeaderFollower Job Active, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Check for fail over not yet complete - retry after delay
        if "A secondary-leader appliance was not found on this peer" in (
            status_message or error_field or message_field
        ):
            logger.warning(
                "⚠ Fail over not yet complete, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Check for other 400 errors
        if http_status == 400:
            message = (
                (status_message or error_field or message_field).strip()
                if (status_message or error_field or message_field)
                else "Unknown error"
            )
            logger.error(f"HTTP 400 Bad Request: {message}")
            raise RuntimeError(f"switch_primary_secondary returned 400: {message}")

        # Check for success message
        if (
            message_field
            == "The primary / secondary appliance roles on this peer have been switched."
        ):
            logger.info("✓ switch-primary-secondary completed successfully")
            return

        # Any other response is unexpected
        message = (
            (status_message or error_field or message_field).strip()
            if (status_message or error_field or message_field)
            else "Unknown response"
        )
        logger.error(f"Unexpected switch_primary_secondary response: {message}")
        raise RuntimeError(f"Unexpected switch_primary_secondary response: {message}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Calls the gRPC endpoint api.v3.cluster-manager.switch-primary-secondary on a peer node."
    )
    parser.add_argument(
        "--log-level",
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Log to file instead of console"
    )
    parser.add_argument(
        "--username", required=True, help="Username for authentication"
    )
    parser.add_argument(
        "--password", required=True, help="Password for authentication"
    )
    parser.add_argument("--ip_peer", required=True, help="IP address of the peer (dot format)")
    parser.add_argument("--port_peer", required=True, type=int, help="Port number of the peer")
    parser.add_argument("--id", required=True, type=int, help="ID of the peer in the peers table")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token
        token = get_token(username=args.username, password=args.password, port=args.port_peer)

        # Create Node object
        node = Node(port=args.port_peer, token=token, ip=args.ip_peer)

        # Call switch-primary-secondary
        switch_primary_secondary(node=node, id=args.id)

        print("✓ Operation completed successfully!")
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Operation failed with unexpected error: {e}")
        sys.exit(1)
