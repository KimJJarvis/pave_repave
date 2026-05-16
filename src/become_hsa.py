#!/usr/bin/env python3
"""
Script to become an HSA using NMS API.
Retrieves an integration token and calls the become-hsa endpoint.
"""

import argparse
import sys
import json
import logging

from node import Node
from make_single_api_request import make_single_api_request
from utilities import setup_logging

logger = logging.getLogger(__name__)


def become_hsa(node: Node, ip_cluster: str, integration_token: str) -> dict:
    """
    Call the become-hsa endpoint.
    
    Args:
        node: Node object with connection details
        ip_cluster: Cluster IP address (primary IP)
        integration_token: Integration token
        
    Returns:
        Response dictionary from the API
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/become-hsa"
    logger.info(f"Calling become-hsa on {url}...")
    
    data = {
        "primaryIp": ip_cluster,
        "secondaryIp": node.ip,
        "token": integration_token
    }
    
    response = make_single_api_request(url, node.token, method="POST", data=data)
    logger.info(f"✓ become-hsa completed: {response.get('status', 'unknown')}")
    return response


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Become an HSA using NMS API"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Log to file instead of console"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Bearer token for authentication"
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="Secondary IP address (dot format)"
    )
    parser.add_argument(
        "--port",
        required=True,
        type=int,
        help="Port number for host"
    )
    parser.add_argument(
        "--ip_cluster",
        required=True,
        help="Primary/Cluster IP address (dot format)"
    )
    parser.add_argument(
        "--integration_token",
        required=True,
        help="Integration token"
    )
    
    args = parser.parse_args()
    
    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)
    
    logger.debug("Starting become-hsa.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Token: {args.token[:20]}...")
    logger.debug(f"  IP: {args.ip}")
    logger.debug(f"  Port: {args.port}")
    logger.debug(f"  Cluster IP: {args.ip_cluster}")
    logger.debug(f"  Integration Token: {args.integration_token[:20]}...")
    
    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)
    
    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"
    
    logger.info("=" * 60)
    logger.info("Become HSA Workflow")
    logger.info("=" * 60)
    logger.info(f"Node: {base_url} (forwarded to {node.ip})")
    logger.info(f"Cluster IP: {args.ip_cluster}")
    logger.info("=" * 60)
    
    # Call become-hsa
    logger.info("Calling become-hsa...")
    become_hsa(node, args.ip_cluster, args.integration_token)
    
    logger.info("=" * 60)
    logger.info("✓ Operation completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

# Made with Bob