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


def leave_cluster_hsa(node: Node, integration_token: str) -> None:
    """
    Call the leave-cluster-hsa endpoint.

    Args:
        node: Node object with connection details
        integration_token: Integration token
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster-hsa"
    logger.info(f"Calling leave-cluster-hsa on {url}...")
    data = {"force": True, "ip": node.ip, "token": integration_token}

    response = make_single_api_request(url, node.token, method="POST", data=data)
    logger.info(f"✓ leave-cluster-hsa completed: {response.get('status', 'unknown')}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Leave an HSA cluster using NMS API")
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
    parser.add_argument("--ip", required=True, help="IP address (dot format)")
    parser.add_argument("--port", required=True, type=int, help="Port number for host")
    parser.add_argument("--integration_token", required=True, help="Integration token")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    logger.debug("Starting leave-cluster-hsa.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Token: {args.token[:20]}...")
    logger.debug(f"  IP: {args.ip}")
    logger.debug(f"  Port: {args.port}")
    logger.debug(f"  Integration Token: {args.integration_token[:20]}...")

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"

    logger.info("=" * 60)
    logger.info("Leave Cluster HSA Workflow")
    logger.info("=" * 60)
    logger.info(f"Node: {base_url} (forwarded to {node.ip})")
    logger.info("=" * 60)

    # Call leave-cluster-hsa
    logger.info("Calling leave-cluster-hsa...")
    leave_cluster_hsa(node, args.integration_token)

    logger.info("=" * 60)
    logger.info("✓ Operation completed successfully!")
    logger.info("=" * 60)
