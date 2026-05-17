#!/usr/bin/env python3
"""
Script to become an HSA using NMS API.
Retrieves an integration token and calls the become-hsa endpoint.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.make_single_api_request import make_single_api_request
from pave_repave.utilities import setup_logging

logger = logging.getLogger(__name__)


def become_hsa(node: Node, ip_peer: str, integration_token: str) -> dict:
    """
    Call the become-hsa endpoint.

    Args:
        node: Node object with connection details
        ip_peer: Peer IP address (primary IP)
        integration_token: Integration token

    Returns:
        Response dictionary from the API
    
    Raises:
        SystemExit: If the API returns HTTP 400 or other error status
    """
    # Log parameters
    logger.info(f"become_hsa called with parameters:")
    logger.info(f"  node.ip: {node.ip}")
    logger.info(f"  node.port: {node.port}")
    logger.info(f"  ip_peer: {ip_peer}")
    logger.info(f"  integration_token: {integration_token[:20]}..." if len(integration_token) > 20 else f"  integration_token: {integration_token}")
    
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/become-hsa"
    logger.info(f"Calling become-hsa on {url}...")

    data = {"primaryIp": ip_peer, "secondaryIp": node.ip, "token": integration_token}

    response = make_single_api_request(url=url, bearer_token=node.token, method="POST", data=data)
    
    # Log response object
    logger.info(f"become_hsa response: {json.dumps(response, indent=2)}")
    
    # Check for HTTP error status codes
    if "_http_status_code" in response:
        status_code = response["_http_status_code"]
        if status_code == 400:
            logger.error(f"HTTP 400 Bad Request: {response.get('error', 'Unknown error')}")
            sys.exit(1)
        elif status_code >= 400:
            logger.error(f"HTTP {status_code} Error: {response.get('error', 'Unknown error')}")
            sys.exit(1)
    
    logger.info(f"✓ become-hsa completed: {response.get('status', 'unknown')}")
    return response


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Calls the gRPC endpoint api.v3.cluster-orchestrator.become-hsa on a spare node.")
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
        "--token_spare", required=True, help="Bearer token for authentication on spare node"
    )
    parser.add_argument("--ip_spare", required=True, help="IP address of the spare node (dot format)")
    parser.add_argument("--port_spare", required=True, type=int, help="Port number of the spare node")
    parser.add_argument(
        "--ip_peer", required=True, help="Primary/Peer IP address in the cluster (dot format)"
    )
    parser.add_argument("--integration_token", required=True, help="Integration token")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Create Node object
    node = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)

    # Call become-hsa
    response = become_hsa(node=node, ip_peer=args.ip_peer, integration_token=args.integration_token)

    print("✓ Operation completed successfully!")
