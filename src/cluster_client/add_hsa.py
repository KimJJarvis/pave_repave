#!/usr/bin/env python3
"""
Script to add an HSA to a cluster using NMS API.
Retrieves an integration token from the peer HSA and calls become-hsa on the spare node.
"""

import argparse
import sys
import json
import logging

from cluster_client.node import Node
from cluster_client.get_integration_token import get_integration_token
from cluster_client.become_hsa import become_hsa
from cluster_client.peer_info import peer_info
from cluster_client.utilities import setup_logging
from cluster_client.get_token import get_token

logger = logging.getLogger(__name__)


def add_hsa(peer: Node, spare: Node) -> None:
    """
    Add an HSA to an existing cluster by getting integration token from peer and calling become-hsa on spare.

    Args:
        peer: Node object for the existing HSA peer (must be in cluster)
        spare: Node object for the spare node to become HSA

    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"add_hsa called with peer: {peer}, spare: {spare}")

    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=peer.ip, integration_token=integration_token)

    logger.debug("✓ add_hsa completed successfully")


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
    parser.add_argument("--username", required=True, help="Username for authentication")
    parser.add_argument("--password", required=True, help="Password for authentication")
    parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer HSA node (dot format)"
    )
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number of the peer HSA node"
    )
    parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node (dot format)"
    )
    parser.add_argument(
        "--port_spare", required=True, type=int, help="Port number of the spare node"
    )
    parser.add_argument(
        "--new_cluster",
        action="store_true",
        help="Create a new cluster (validates that both peer and spare are not in any cluster)",
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token for peer node
        logger.debug("Authenticating with peer node...")
        peer_token = get_token(
            username=args.username, password=args.password, port=args.port_peer
        )
        logger.debug("✓ Peer authentication successful")

        # Get authentication token for spare node
        logger.debug("Authenticating with spare node...")
        spare_token = get_token(
            username=args.username, password=args.password, port=args.port_spare
        )
        logger.debug("✓ Spare authentication successful")

        # Create Node objects
        peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
        spare_node = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)

        # Call appropriate function based on new_cluster parameter
        if args.new_cluster:
            add_new_hsa(peer=peer_node, spare=spare_node)
        else:
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
