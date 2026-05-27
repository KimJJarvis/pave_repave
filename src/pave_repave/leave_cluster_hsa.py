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
from pave_repave.get_token import get_token

logger = logging.getLogger(__name__)


def leave_cluster_hsa(node: Node, integration_token: str) -> None:
    """
    Call the leave-cluster-hsa endpoint.

    Args:
        node: Node object with connection details
        integration_token: Integration token
    
    Raises:
        RuntimeError: If the API returns HTTP 400 or other error status
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
    
    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)
    
    if http_status == 400:
        error_msg = response.get('error', 'Unknown error')
        logger.error(f"HTTP 400 Bad Request: {error_msg}")
        raise RuntimeError(f"leave_cluster_hsa returned HTTP 400: {response}")
    
    if http_status != 200:
        error_msg = response.get('error', 'Unknown error')
        logger.error(f"HTTP {http_status} Error: {error_msg}")
        raise RuntimeError(f"leave_cluster_hsa returned unexpected HTTP status {http_status}: {response}")
    
    # Log response
    logger.info(f"leave_cluster_hsa response:")
    logger.info(json.dumps(response, indent=2))
    
    status_msg = response.get('status', 'unknown')
    logger.info(f"✓ leave-cluster-hsa completed: {status_msg}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Calls the gRPC endpoint api.v3.cluster-orchestrator.leave-cluster-hsa on a HSA node.")
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
    parser.add_argument("--ip", required=True, help="IP address of the HSA (dot format)")
    parser.add_argument("--port", required=True, type=int, help="Port number of the HSA")
    parser.add_argument("--integration_token", required=True, help="Integration token")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token
        token = get_token(username=args.username, password=args.password, port=args.port)

        # Create Node object
        node = Node(port=args.port, token=token, ip=args.ip)

        # Call leave-cluster-hsa
        leave_cluster_hsa(node=node, integration_token=args.integration_token)

        print("✓ Operation completed successfully!")
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Operation failed with unexpected error: {e}")
        sys.exit(1)
