#!/usr/bin/env python3
"""
Script to remove an HSA from a cluster using NMS API.
Retrieves an integration token from the HSA and calls leave-cluster-hsa on the peer node.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.get_integration_token import get_integration_token
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.utilities import setup_logging
from pave_repave.get_token import get_token

logger = logging.getLogger(__name__)


def remove_hsa(peer: Node, hsa: Node) -> None:
    """
    Remove an HSA from the cluster by getting integration token from HSA and calling leave-cluster-hsa on peer.

    Args:
        peer: Node object for the peer node that will execute the leave-cluster-hsa command
        hsa: Node object for the HSA to be removed

    Raises:
        RuntimeError: If any API call fails
    """
    logger.info(f"remove_hsa called with peer: {peer}, hsa: {hsa}")
    
    logger.info("Get integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling leave_cluster_hsa on HSA...")
    leave_cluster_hsa(node=peer, integration_token=integration_token)
    
    logger.info("✓ remove_hsa completed successfully")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Remove an HSA from a cluster by retrieving integration token from HSA and calling leave-cluster-hsa on peer node."
    )
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
    parser.add_argument(
        "--peer_ip", required=True, help="IP address of the peer node (dot format)"
    )
    parser.add_argument(
        "--peer_port", required=True, type=int, help="Port number of the peer node"
    )
    parser.add_argument(
        "--hsa_ip", required=True, help="IP address of the HSA to be removed (dot format)"
    )
    parser.add_argument(
        "--hsa_port", required=True, type=int, help="Port number of the HSA to be removed"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token for peer node
        logger.info("Authenticating with peer node...")
        peer_token = get_token(username=args.username, password=args.password, port=args.peer_port)
        logger.info("✓ Peer authentication successful")

        # Get authentication token for HSA node
        logger.info("Authenticating with HSA node...")
        hsa_token = get_token(username=args.username, password=args.password, port=args.hsa_port)
        logger.info("✓ HSA authentication successful")

        # Create Node objects
        peer_node = Node(port=args.peer_port, token=peer_token, ip=args.peer_ip)
        hsa_node = Node(port=args.hsa_port, token=hsa_token, ip=args.hsa_ip)

        # Call remove_hsa
        remove_hsa(peer=peer_node, hsa=hsa_node)

        print("✓ Operation completed successfully!")
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Operation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
