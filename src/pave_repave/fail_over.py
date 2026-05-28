#!/usr/bin/env python3
"""
Script to perform fail-over operation using NMS API.
Calls the fail-over endpoint on porta with ipa as the peer IP.
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


def fail_over(node: Node) -> None:
    """
    Call the fail-over endpoint.

    Args:
        node: Node object with connection details

    Raises:
        RuntimeError: If the API returns HTTP 400, LeaderFollower Job Active error, or unexpected response
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/fail-over"
    logger.info(f"fail_over called - Node(port={node.port}, ip={node.ip})")

    data = {"peerIp": node.ip}

    api_response = make_single_api_request(url=url, bearer_token=node.token, method="POST", data=data)

    # Get HTTP status code if present (added by make_single_api_request for error responses)
    http_status = api_response.get("_http_status_code", 200)

    # Parse the response - check statusMessage and error fields
    status_message = api_response.get("statusMessage", "")
    error_field = api_response.get("error", "")

    # Check for HTTP 400 error
    if http_status == 400:
        message = (status_message or error_field or "Unknown error").strip()
        logger.error(f"HTTP 400 Bad Request: {message}")
        raise RuntimeError(f"fail_over returned 400: {message}")

    # Check for LeaderFollower Job Active error
    if "LeaderFollower Job Active, cannot Fail-Over" in (status_message or error_field):
        logger.error("LeaderFollower Job Active, cannot Fail-Over")
        raise RuntimeError("fail_over error: LeaderFollower Job Active, cannot Fail-Over")

    # Check for success message
    if status_message != "OKAY: Failover successfully started.":
        # Any other response is unexpected
        message = (
            (status_message or error_field).strip()
            if (status_message or error_field)
            else "Unknown response"
        )
        logger.error(f"Unexpected fail_over response: {message}")
        raise RuntimeError(f"Unexpected fail_over response: {message}")

    logger.info("✓ Failover successfully started")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Calls the gRPC endpoint api.v3.cluster-manager.fail-over a peer."
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
    parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer to fail-over (dot format)"
    )
    parser.add_argument("--port_peer", required=True, type=int, help="Port number of the peer")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token
        token = get_token(username=args.username, password=args.password, port=args.port_peer)

        # Create Node object
        node = Node(port=args.port_peer, token=token, ip=args.ip_peer)

        # Call fail-over
        fail_over(node=node)

        print("✓ Operation completed successfully!")
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Operation failed with unexpected error: {e}")
        sys.exit(1)
