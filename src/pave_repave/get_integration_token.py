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
from pave_repave.get_token import get_token

logger = logging.getLogger(__name__)


def get_integration_token(node: Node) -> str:
    """
    Retrieve integration token from the NMS API.

    Args:
        node: Node object with connection details

    Returns:
        The integration token string
    
    Raises:
        RuntimeError: If token field is not found in response or HTTP error occurs
    """
    logger.info(f"get_integration_token called with node: ip={node.ip}, port={node.port}")
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/integration-token"

    response = make_single_api_request(url=url, bearer_token=node.token, method="GET")

    # Check for HTTP error status codes
    if "_http_status_code" in response:
        status_code = response["_http_status_code"]
        if status_code == 400:
            error_msg = response.get('error', 'Unknown error')
            logger.error(f"HTTP 400 Bad Request: {error_msg}")
            raise RuntimeError(f"get_integration_token returned HTTP 400: {response}")
        elif status_code >= 400:
            error_msg = response.get('error', 'Unknown error')
            logger.error(f"HTTP {status_code} Error: {error_msg}")
            raise RuntimeError(f"get_integration_token returned HTTP {status_code}: {response}")

    if "token" not in response:
        logger.error(f"'token' field not found in response: {response}")
        raise RuntimeError(f"get_integration_token: 'token' field not found in response")

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
        "--username", required=True, help="Username for authentication"
    )
    parser.add_argument(
        "--password", required=True, help="Password for authentication"
    )
    parser.add_argument("--ip", required=True, help="IP address of peer (dot format)")
    parser.add_argument("--port", required=True, type=int, help="Port number for peer")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token
        token = get_token(username=args.username, password=args.password, port=args.port)

        # Create Node object
        node = Node(port=args.port, token=token, ip=args.ip)

        # Get integration token
        integration_token = get_integration_token(node=node)

        # Output the integration token to stdout
        print(integration_token)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Operation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Operation failed with unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
