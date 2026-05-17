#!/usr/bin/env python3
"""
Script to leave an HSA cluster using NMS API.
Retrieves an integration token and calls the leave-cluster-hsa endpoint.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.make_single_api_request import make_single_api_request
from pave_repave.utilities import setup_logging

logger = logging.getLogger(__name__)


def leave_cluster_hsa(node: Node, integration_token: str) -> dict:
    """
    Call the leave-cluster-hsa endpoint.

    Args:
        node: Node object with connection details
        integration_token: Integration token
    
    Returns:
        Response dictionary from the API
    
    Raises:
        SystemExit: If the API returns HTTP 400 or other error status
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster-hsa"
    
    # Log parameters
    logger.info(f"leave_cluster_hsa called with parameters:")
    logger.info(f"  node.ip: {node.ip}")
    logger.info(f"  node.port: {node.port}")
    logger.info(f"  integration_token: {integration_token[:20]}...")
    
    logger.info(f"Calling leave-cluster-hsa on {url}...")
    data = {"force": True, "ip": node.ip, "token": integration_token}

    response = make_single_api_request(url=url, bearer_token=node.token, method="POST", data=data)
    
    # Check for HTTP error status codes
    if "_http_status_code" in response:
        status_code = response["_http_status_code"]
        if status_code == 400:
            logger.error(f"HTTP 400 Bad Request: {response.get('error', 'Unknown error')}")
            sys.exit(1)
        elif status_code >= 400:
            logger.error(f"HTTP {status_code} Error: {response.get('error', 'Unknown error')}")
            sys.exit(1)
    
    # Log response
    logger.info(f"leave_cluster_hsa response:")
    logger.info(json.dumps(response, indent=2))
    
    logger.info(f"✓ leave-cluster-hsa completed: {response.get('status', 'unknown')}")
    return response


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Calls the gRPC endpoint api.v3.cluster-orchestrator.leave-cluster-hsa on a HSA node.")
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
        "--token_hsa", required=True, help="Bearer token for authentication on HSA"
    )
    parser.add_argument("--ip_hsa", required=True, help="IP address of the HSA (dot format)")
    parser.add_argument("--port_hsa", required=True, type=int, help="Port number of the HSA")
    parser.add_argument("--integration_token", required=True, help="Integration token")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Create Node object
    node = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)

    # Call leave-cluster-hsa
    response = leave_cluster_hsa(node=node, integration_token=args.integration_token)

    print("✓ Operation completed successfully!")
