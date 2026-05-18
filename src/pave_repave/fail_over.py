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

logger = logging.getLogger(__name__)


def fail_over(node: Node) -> Response:
    """
    Call the fail-over endpoint.

    Args:
        node: Node object with connection details

    Returns:
        Response object with message and status code
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

    # Determine message and code based on response
    if "LeaderFollower Job Active, cannot Fail-Over" in (status_message or error_field):
        message = "LeaderFollower Job Active, cannot Fail-Over"
        code = http_status
    elif status_message == "OKAY: Failover successfully started.":
        message = "Failover successfully started"
        code = 200
    else:
        # For all other responses, copy the message and use HTTP status code
        message = (
            (status_message or error_field).strip()
            if (status_message or error_field)
            else "Unknown response"
        )
        code = http_status

    response = Response(message=message, code=code)
    logger.info(f"Response: {response.message} (code: {response.code})")

    return response


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
        "--token", required=True, help="Bearer token for authentication"
    )
    parser.add_argument(
        "--ip", required=True, help="IP address of the peer to fail-over (dot format)"
    )
    parser.add_argument("--port", required=True, type=int, help="Port number of the peer")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"

    # Call fail-over
    response = fail_over(node=node)

    if response.code == 200:
        print("✓ Operation completed successfully!")
    else:
        print(f"⚠ Operation completed with code {response.code}")
