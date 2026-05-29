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
from pave_repave.peer_info import peer_info
from pave_repave.utilities import setup_logging
from pave_repave.get_token import get_token

logger = logging.getLogger(__name__)


def add_new_hsa(peer: Node, spare: Node) -> None:
    """
    Create a new HSA cluster by getting integration token from peer and calling become-hsa on spare.
    Validates that both peer and spare are not in any cluster.

    Args:
        peer: Node object for the peer node (will become primary in new cluster)
        spare: Node object for the spare node to become HSA (will become secondary)

    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"add_new_hsa called with peer: {peer}, spare: {spare}")
    
    # Validate peer node - should not be in any cluster
    logger.debug("Validating peer node...")
    peer_status = peer_info(node=peer)
    
    if peer_status is not None:
        raise RuntimeError(
            f"Peer node {peer.ip} is already in a cluster (primary_ip={peer_status.primary_ip}, secondary_ip={peer_status.secondary_ip}). Cannot create new cluster."
        )
    logger.debug("✓ Peer node validation passed (not found in any cluster)")
    
    # Validate spare node
    logger.debug("Validating spare node...")
    spare_status = peer_info(node=spare)
    if spare_status is not None:
        raise RuntimeError(
            f"Spare node {spare.ip} is already in a cluster (primary_ip={spare_status.primary_ip}, secondary_ip={spare_status.secondary_ip})"
        )
    
    logger.debug("✓ Spare node validation passed (not found in cluster)")
    
    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    
    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=peer.ip, integration_token=integration_token)
    
    logger.debug("✓ add_new_hsa completed successfully")


def add_hsa(peer: Node, spare: Node) -> None:
    """
    Add an HSA to an existing cluster by getting integration token from peer and calling become-hsa on spare.
    Validates that peer is in cluster with no secondary, and spare is not in any cluster.

    Args:
        peer: Node object for the existing HSA peer (must be in cluster)
        spare: Node object for the spare node to become HSA

    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"add_hsa called with peer: {peer}, spare: {spare}")
    
    # Validate peer node - should be in cluster with no secondary
    logger.debug("Validating peer node...")
    peer_status = peer_info(node=peer)
    
    if peer_status is None:
        raise RuntimeError(f"Peer node {peer.ip} is not found in cluster")
    
    logger.debug(f"Peer status: primary_ip={peer_status.primary_ip}, secondary_ip={peer_status.secondary_ip}")
    
    # Check that primary_ip of peer matches peer.ip
    if peer_status.primary_ip != peer.ip:
        raise RuntimeError(
            f"Peer node primary_ip ({peer_status.primary_ip}) does not match peer.ip ({peer.ip})"
        )
    
    # Check that secondary_ip of peer is empty
    if peer_status.secondary_ip != "":
        raise RuntimeError(
            f"Peer node already has a secondary_ip ({peer_status.secondary_ip}). Cannot add HSA."
        )
    
    logger.debug("✓ Peer node validation passed")
    
    # Validate spare node
    logger.debug("Validating spare node...")
    spare_status = peer_info(node=spare)
    if spare_status is not None:
        raise RuntimeError(
            f"Spare node {spare.ip} is already in a cluster (primary_ip={spare_status.primary_ip}, secondary_ip={spare_status.secondary_ip})"
        )
    
    logger.debug("✓ Spare node validation passed (not found in cluster)")
    
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
    parser.add_argument(
        "--username", required=True, help="Username for authentication"
    )
    parser.add_argument(
        "--password", required=True, help="Password for authentication"
    )
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
        help="Create a new cluster (validates that both peer and spare are not in any cluster)"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token for peer node
        logger.debug("Authenticating with peer node...")
        peer_token = get_token(username=args.username, password=args.password, port=args.port_peer)
        logger.debug("✓ Peer authentication successful")

        # Get authentication token for spare node
        logger.debug("Authenticating with spare node...")
        spare_token = get_token(username=args.username, password=args.password, port=args.port_spare)
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
