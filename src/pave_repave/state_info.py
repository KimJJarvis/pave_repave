#!/usr/bin/env python3
"""
Get state script that determines the current state of the peer/HSA cluster.
This script performs the same verification as repave.py prior to step 1,
then determines and prints the current state (0-4).
"""

import argparse
import sys
import time
import logging

from pave_repave.node import Node
from pave_repave.peer_info import peer_info
from pave_repave.utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    exit_with_error,
    setup_logging,
)

logger = logging.getLogger(__name__)


def state_info(peer: Node, hsa: Node, spare: Node) -> int:
    """
    Determine the current state of the peer/HSA cluster.

    Args:
        peer: Peer Node object
        other: Other Node object
    """
    # Get peer info from peer node
    peer_check_peer = Node(port=peer.port, token=peer.token, ip=peer.ip)
    peer_status_on_peer = peer_info(node=peer_check_peer)

    other_check_peer = Node(port=peer.port, token=peer.token, ip=hsa.ip)
    other_status_on_peer = peer_info(node=other_check_peer)

    # Get peer info from other node
    peer_check_other = Node(port=hsa.port, token=hsa.token, ip=peer.ip)
    peer_status_on_other = peer_info(node=peer_check_other)

    other_check_other = Node(port=hsa.port, token=hsa.token, ip=hsa.ip)
    other_status_on_other = peer_info(node=other_check_other)

    other_check_spare = Node(port=hsa.port, token=hsa.token, ip="127.0.0.1")
    other_spare_status = peer_info(node=other_check_spare)

    logger.info(f"peer_status_on_peer: {peer_status_on_peer}")
    logger.info(f"other_status_on_peer: {other_status_on_peer}")
    logger.info(f"peer_status_on_other: {peer_status_on_other}")
    logger.info(f"other_status_on_other: {other_status_on_other}")
    logger.info(f"other_spare_status: {other_spare_status}")

    # Check for State 5: Peer standalone, Other Spare
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == ""
        and peer_status_on_peer.active_appliance == 1
        and other_status_on_peer is None
        and peer_status_on_other is None
        and other_status_on_other is None
        and other_spare_status is not None
    ):
        return 5

    # Check for State 4: Peer standalone, Other Separated
    if (
        peer_status_on_peer is None
        and other_status_on_peer is None
        and peer_status_on_other is None
        and other_status_on_other is not None
        and other_status_on_other.primary_ip == hsa.ip
        and other_status_on_other.secondary_ip == ""
        and other_status_on_other.active_appliance == 1
    ):
        return 4

    # Check for State 2: other is active primary, peer is the passive secondary
    # After switch primary secondary
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.secondary_ip == peer.ip
        and peer_status_on_peer.primary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 1
        and other_status_on_peer is not None
        and other_status_on_peer.secondary_ip == peer.ip
        and other_status_on_peer.primary_ip == hsa.ip
        and other_status_on_peer.active_appliance == 1
        and peer_status_on_other is not None
        and peer_status_on_other.secondary_ip == peer.ip
        and peer_status_on_other.primary_ip == hsa.ip
        and peer_status_on_other.active_appliance == 1
        and other_status_on_other is not None
        and other_status_on_other.secondary_ip == peer.ip
        and other_status_on_other.primary_ip == hsa.ip
        and other_status_on_other.active_appliance == 1
        and peer_status_on_peer.id == peer_status_on_other.id
        and peer_status_on_peer.id == other_status_on_peer.id
        and peer_status_on_peer.id == other_status_on_other.id
        and peer_status_on_peer.id > 0
    ):
        return 3


    # Check for State 2: peer is passive primary, other is active secondary
    # After fail over
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 2
        and other_status_on_peer is not None
        and other_status_on_peer.primary_ip == peer.ip
        and other_status_on_peer.secondary_ip == hsa.ip
        and other_status_on_peer.active_appliance == 2
        and peer_status_on_other is not None
        and peer_status_on_other.primary_ip == peer.ip
        and peer_status_on_other.secondary_ip == hsa.ip
        and peer_status_on_other.active_appliance == 2
        and other_status_on_other is not None
        and other_status_on_other.primary_ip == peer.ip
        and other_status_on_other.secondary_ip == hsa.ip
        and other_status_on_other.active_appliance == 2
        and peer_status_on_peer.id == peer_status_on_other.id
        and peer_status_on_peer.id == other_status_on_peer.id
        and peer_status_on_peer.id == other_status_on_other.id
        and peer_status_on_peer.id > 0
    ):
        return 2

    # Check for State 1: peer is active primary, other is passive secondary
    # Initial state for pave
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 1
        and other_status_on_peer is not None
        and other_status_on_peer.primary_ip == peer.ip
        and other_status_on_peer.secondary_ip == hsa.ip
        and other_status_on_peer.active_appliance == 1
        and peer_status_on_other is not None
        and peer_status_on_other.primary_ip == peer.ip
        and peer_status_on_other.secondary_ip == hsa.ip
        and peer_status_on_other.active_appliance == 1
        and other_status_on_other is not None
        and other_status_on_other.primary_ip == peer.ip
        and other_status_on_other.secondary_ip == hsa.ip
        and other_status_on_other.active_appliance == 1
        and peer_status_on_peer.id == peer_status_on_other.id
        and peer_status_on_peer.id == other_status_on_peer.id
        and peer_status_on_peer.id == other_status_on_other.id
        and peer_status_on_peer.id > 0
    ):
        return 1

    # All other conditions are state 0
    return 0


def verify_state(state: int, peer: Node, hsa: Node, spare: Node) -> bool:
    """
    Verify that the system is in the specified state.

    Returns:
        True if system is in the specified state, False otherwise
    """
    current_state = state_info(peer=peer, hsa=hsa, spare=spare)
    return current_state == state


def wait_state(state: int, peer: Node, hsa: Node, spare: Node) -> None:
    """
    Wait for the system to reach the specified state.
    Calls verify_state() repeatedly until the desired state is reached.
    """
    max_retries = 10  # Maximum number of retries
    retry_count = 0

    logger.info(f"Waiting for state {state}...")

    while retry_count < max_retries:
        if retry_count > 0:
            logger.info(f"Retry attempt {retry_count}/{max_retries}...")

        # Check if we're in the desired state
        if verify_state(state=state, peer=peer, hsa=hsa, spare=spare):
            logger.info(f"✓ State {state} reached successfully")
            return

        # If not in desired state, wait and retry
        retry_count += 1
        if retry_count < max_retries:
            current_state = state_info(peer=peer, hsa=hsa, spare=spare)
            logger.warning(
                f"Current state is {current_state}, not {state}. Waiting 30 seconds before retry..."
            )
            time.sleep(30)
        else:
            current_state = state_info(peer=peer, hsa=hsa, spare=spare)
            exit_with_error(
                f"wait_state failed: State {state} not reached after maximum retries (current state: {current_state})"
            )


def main():
    """Main entry point for the state_info script."""
    parser = argparse.ArgumentParser(
        description="Calls the gRPC endpoint api.v3.peers on the peer node and another node."
    )
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
        "--token_cluster", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip_peer", required=True, help="IP address of the peer node (in dot format)")
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number for peer node"
    )
    parser.add_argument(
        "--token_hsa", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip_hsa", required=True, help="IP address of the HSA node (in dot format)")
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="Port number for HSA node"
    )
    parser.add_argument(
        "--token_spare", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip_spare", required=True, help="IP address of the spare node")
    parser.add_argument(
        "--port_spare", required=True, type=int, help="Port number for spare node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)
    spare_node = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)

    # Determine and print the current state
    current_state = state_info(peer=peer_node, hsa=hsa_node, spare=spare_node)

    # Print state to console (stdout)
    print(current_state)
