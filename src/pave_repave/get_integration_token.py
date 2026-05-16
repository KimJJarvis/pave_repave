#!/usr/bin/env python3
"""
Script to retrieve an integration token from NMS API.
Simplified version that only gets and prints the integration token from porta.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.make_single_api_request import make_single_api_request
from pave_repave.utilities import setup_logging

logger = logging.getLogger(__name__)


def get_integration_token(node: Node) -> str:
    """
    Retrieve integration token from the NMS API.

    Args:
        node: Node object with connection details

    Returns:
        The integration token string
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/integration-token"
    logger.info(f"Getting integration token from {url}...")

    response = make_single_api_request(url=url, bearer_token=node.token, method="GET")

    if "token" not in response:
        logger.error(f"'token' field not found in response: {response}")
        sys.exit(1)

    token = response["token"]
    logger.info("✓ Integration token retrieved")
    return token


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Get integration token from NMS API")
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
        "--token", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip", required=True, help="IP address")
    parser.add_argument("--port", required=True, type=int, help="Port number for host")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    logger.debug("Starting get-integration-token.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Token: {args.token[:20]}...")
    logger.debug(f"  IP: {args.ip}")
    logger.debug(f"  Port: {args.port}")

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    # Construct base URL - request goes to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"

    logger.info("=" * 60)
    logger.info("Get Integration Token")
    logger.info("=" * 60)
    logger.info(f"Node: {base_url} (forwarded to {node.ip})")
    logger.info("=" * 60)

    # Get integration token
    logger.info("Getting integration token...")
    integration_token = get_integration_token(node=node)

    logger.info("=" * 60)
    logger.info("✓ Operation completed successfully!")
    logger.info("=" * 60)

    # Output the integration token to stdout
    print("\nIntegration Token:")
    print(json.dumps({"token": integration_token}, indent=2))
