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
from pave_repave.peer_info import peer_info
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
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"remove_hsa called with peer: {peer}, hsa: {hsa}")
    
    # Validate peer node
    logger.debug("Validating peer node...")
    peer_status = peer_info(node=peer)
    if peer_status is None:
        raise RuntimeError(f"Peer node {peer.ip} is not found in cluster")
    
    logger.debug(f"Peer status: primary_ip={peer_status.primary_ip}, secondary_ip={peer_status.secondary_ip}, id={peer_status.id}")
    
    # Check that primary_ip of peer matches peer.ip
    if peer_status.primary_ip != peer.ip:
        raise RuntimeError(
            f"Peer node primary_ip ({peer_status.primary_ip}) does not match peer.ip ({peer.ip})"
        )
    
    # Check that secondary_ip of peer matches hsa.ip
    if peer_status.secondary_ip != hsa.ip:
        raise RuntimeError(
            f"Peer node secondary_ip ({peer_status.secondary_ip}) does not match hsa.ip ({hsa.ip})"
        )
    
    logger.debug("✓ Peer node validation passed")
    
    # Validate HSA node
    logger.debug("Validating HSA node...")
    hsa_status = peer_info(node=hsa)
    if hsa_status is None:
        raise RuntimeError(f"HSA node {hsa.ip} is not found in cluster")
    
    logger.debug(f"HSA status: primary_ip={hsa_status.primary_ip}, secondary_ip={hsa_status.secondary_ip}, id={hsa_status.id}")
    
    # Check that primary_ip of hsa matches peer.ip
    if hsa_status.primary_ip != peer.ip:
        raise RuntimeError(
            f"HSA node primary_ip ({hsa_status.primary_ip}) does not match peer.ip ({peer.ip})"
        )
    
    # Check that secondary_ip of hsa matches hsa.ip
    if hsa_status.secondary_ip != hsa.ip:
        raise RuntimeError(
            f"HSA node secondary_ip ({hsa_status.secondary_ip}) does not match hsa.ip ({hsa.ip})"
        )
    
    # Check that peer's active_appliance is 1 (PRIMARY)
    if peer_status.active_appliance != 1:
        raise RuntimeError(
            f"Peer node active_appliance ({peer_status.active_appliance}) is not 1 (PRIMARY)"
        )
    
    # Check that hsa's active_appliance is 1 (PRIMARY)
    if hsa_status.active_appliance != 1:
        raise RuntimeError(
            f"HSA node active_appliance ({hsa_status.active_appliance}) is not 1 (PRIMARY)"
        )
    
    # Check that peer.id == hsa.id (both nodes should have the same cluster ID)
    if peer_status.id != hsa_status.id:
        raise RuntimeError(
            f"Peer node id ({peer_status.id}) does not match HSA node id ({hsa_status.id})"
        )
    
    logger.debug("✓ HSA node validation passed")
    
    logger.debug("Get integration token")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling leave_cluster_hsa on HSA...")
    leave_cluster_hsa(node=hsa, integration_token=integration_token)
    
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
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number of the peer node"
    )
    parser.add_argument(
        "--ip_hsa", required=True, help="IP address of the HSA to be removed (dot format)"
    )
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="Port number of the HSA to be removed"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token for peer node
        logger.debug("Authenticating with peer node...")
        peer_token = get_token(username=args.username, password=args.password, port=args.port_peer)
        logger.debug("✓ Peer authentication successful")

        # Get authentication token for HSA node
        logger.debug("Authenticating with HSA node...")
        hsa_token = get_token(username=args.username, password=args.password, port=args.port_hsa)
        logger.debug("✓ HSA authentication successful")

        # Create Node objects
        peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
        hsa_node = Node(port=args.port_hsa, token=hsa_token, ip=args.ip_hsa)

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
