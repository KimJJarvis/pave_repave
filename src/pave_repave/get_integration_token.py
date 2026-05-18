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
    logger.info(f"get_integration_token called with node: ip={node.ip}, port={node.port}")
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/integration-token"

    response = make_single_api_request(url=url, bearer_token=node.token, method="GET")

    if "token" not in response:
        logger.error(f"'token' field not found in response: {response}")
        sys.exit(1)

    token = response["token"]
    logger.info("✓ Integration token retrieved")
    return token


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Calls the gRPC endpoint api.v3.cluster-orchestrator.integration-token on a  node.")
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
    parser.add_argument("--ip", required=True, help="IP address of peer (dot format)")
    parser.add_argument("--port", required=True, type=int, help="Port number for peer")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    # Get integration token
    integration_token = get_integration_token(node=node)

    # Output the integration token to stdout
    print(integration_token)
