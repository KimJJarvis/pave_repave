#!/usr/bin/env python3
"""
Script to add an HSA to a cluster using NMS API.
Retrieves an integration token from the peer HSA and calls become-hsa on the spare node.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.get_integration_token import get_integration_token
from pave_repave.become_hsa import become_hsa
from pave_repave.utilities import setup_logging
from pave_repave.get_token import get_token

logger = logging.getLogger(__name__)


def add_hsa(peer: Node, spare: Node) -> None:
    """
    Add an HSA to the cluster by getting integration token from peer and calling become-hsa on spare.

    Args:
        peer: Node object for the existing HSA peer
        spare: Node object for the spare node to become HSA

    Raises:
        RuntimeError: If any API call fails
    """
    logger.info(f"add_hsa called with peer: {peer}, spare: {spare}")
    
    logger.info("Getting integration token")
    integration_token = get_integration_token(node=peer)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    
    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=peer.ip, integration_token=integration_token)
    
    logger.info("✓ add_hsa completed successfully")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Add an HSA to a cluster by retrieving integration token from peer and calling become-hsa on spare node."
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
        "--peer_ip", required=True, help="IP address of the peer HSA node (dot format)"
    )
    parser.add_argument(
        "--peer_port", required=True, type=int, help="Port number of the peer HSA node"
    )
    parser.add_argument(
        "--spare_ip", required=True, help="IP address of the spare node (dot format)"
    )
    parser.add_argument(
        "--spare_port", required=True, type=int, help="Port number of the spare node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token for peer node
        logger.info("Authenticating with peer node...")
        peer_token = get_token(username=args.username, password=args.password, port=args.peer_port)
        logger.info("✓ Peer authentication successful")

        # Get authentication token for spare node
        logger.info("Authenticating with spare node...")
        spare_token = get_token(username=args.username, password=args.password, port=args.spare_port)
        logger.info("✓ Spare authentication successful")

        # Create Node objects
        peer_node = Node(port=args.peer_port, token=peer_token, ip=args.peer_ip)
        spare_node = Node(port=args.spare_port, token=spare_token, ip=args.spare_ip)

        # Call add_hsa
        add_hsa(peer=peer_node, spare=spare_node)

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
