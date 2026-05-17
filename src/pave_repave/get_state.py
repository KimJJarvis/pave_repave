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


def which_state(peer: Node, other: Node) -> int:
    """
    Determine the current state of the peer/HSA cluster.

    Returns:
        State number (0-4):
        - State 1: Both nodes show peer as primary, hsa as secondary, activeAppliance=PRIMARY
        - State 2: Both nodes show peer as primary, hsa as secondary, activeAppliance=SECONDARY
        - State 3: Both nodes show peer as secondary, hsa as primary, activeAppliance=PRIMARY
        - State 4: Peer standalone (peer primary, no secondary), HSA standalone (127.0.0.1)
        - State 0: Any other condition

    Args:
        peer: Peer Node object
        other: Other Node object
    """
    # Get peer info from peer node
    peer_check_peer = Node(port=peer.port, token=peer.token, ip=peer.ip)
    peer_status_on_peer = peer_info(node=peer_check_peer)

    other_check_peer = Node(port=peer.port, token=peer.token, ip=other.ip)
    other_status_on_peer = peer_info(node=other_check_peer)

    # Get peer info from other node
    peer_check_other = Node(port=other.port, token=other.token, ip=peer.ip)
    peer_status_on_other = peer_info(node=peer_check_other)

    other_check_other = Node(port=other.port, token=other.token, ip=other.ip)
    other_status_on_other = peer_info(node=other_check_other)

    logger.debug(f"peer_status_on_peer: {peer_status_on_peer}")
    logger.debug(f"other_status_on_peer: {other_status_on_peer}")
    logger.debug(f"peer_status_on_other: {peer_status_on_other}")
    logger.debug(f"other_status_on_other: {other_status_on_other}")


    # Check for State 5: Peer standalone, Other Initialised
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == ""
        and peer_status_on_peer.active_appliance == 1
        and other_status_on_peer is None
        and other_status_on_other is None
    ):
        return 4


    # Check for State 4: Peer standalone, Other Separated
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == ""
        and peer_status_on_peer.active_appliance == 1
        and other_status_on_peer is None
        and other_status_on_other is not None
    ):
        return 4

    # Check for State 3: peer is secondary, other is primary, activeAppliance=PRIMARY on both
    # Peer: primary_ip is other, secondary_ip is peer, activeAppliance=PRIMARY
    # Other: primary_ip is other, secondary_ip is peer, activeAppliance=PRIMARY
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.secondary_ip == peer.ip
        and peer_status_on_peer.primary_ip == other.ip
        and peer_status_on_peer.active_appliance == 1
        and other_status_on_peer is not None
        and other_status_on_peer.secondary_ip == peer.ip
        and other_status_on_peer.primary_ip == other.ip
        and other_status_on_peer.active_appliance == 1
        and peer_status_on_other is not None
        and peer_status_on_other.secondary_ip == peer.ip
        and peer_status_on_other.primary_ip == other.ip
        and peer_status_on_other.active_appliance == 1
        and other_status_on_other is not None
        and other_status_on_other.secondary_ip == peer.ip
        and other_status_on_other.primary_ip == other.ip
        and other_status_on_other.active_appliance == 1
        and peer_status_on_peer.id == peer_status_on_other.id
        and peer_status_on_peer.id == other_status_on_peer.id
        and peer_status_on_peer.id == other_status_on_other.id
        and peer_status_on_peer.id > 0
    ):
        return 3

    # Check for State 2: peer is primary, other is secondary, activeAppliance=SECONDARY on both
    # Peer: primary_ip is peer, secondary_ip is other, activeAppliance=SECONDARY
    # Other: primary_ip is peer, secondary_ip is other, activeAppliance=SECONDARY
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == other.ip
        and peer_status_on_peer.active_appliance == 2
        and other_status_on_peer is not None
        and other_status_on_peer.primary_ip == peer.ip
        and other_status_on_peer.secondary_ip == other.ip
        and other_status_on_peer.active_appliance == 2
        and peer_status_on_other is not None
        and peer_status_on_other.primary_ip == peer.ip
        and peer_status_on_other.secondary_ip == other.ip
        and peer_status_on_other.active_appliance == 2
        and other_status_on_other is not None
        and other_status_on_other.primary_ip == peer.ip
        and other_status_on_other.secondary_ip == other.ip
        and other_status_on_other.active_appliance == 2
        and peer_status_on_peer.id == peer_status_on_other.id
        and peer_status_on_peer.id == other_status_on_peer.id
        and peer_status_on_peer.id == other_status_on_other.id
        and peer_status_on_peer.id > 0
    ):
        return 2

    # Check for State 1: peer is primary, other is secondary, activeAppliance=PRIMARY on both
    # Peer: primary_ip is peer, secondary_ip is other, activeAppliance=PRIMARY
    # Other: primary_ip is peer, secondary_ip is other, activeAppliance=PRIMARY
    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == other.ip
        and peer_status_on_peer.active_appliance == 1
        and other_status_on_peer is not None
        and other_status_on_peer.primary_ip == peer.ip
        and other_status_on_peer.secondary_ip == other.ip
        and other_status_on_peer.active_appliance == 1
        and peer_status_on_other is not None
        and peer_status_on_other.primary_ip == peer.ip
        and peer_status_on_other.secondary_ip == other.ip
        and peer_status_on_other.active_appliance == 1
        and other_status_on_other is not None
        and other_status_on_other.primary_ip == peer.ip
        and other_status_on_other.secondary_ip == other.ip
        and other_status_on_other.active_appliance == 1
        and peer_status_on_peer.id == peer_status_on_other.id
        and peer_status_on_peer.id == other_status_on_peer.id
        and peer_status_on_peer.id == other_status_on_other.id
        and peer_status_on_peer.id > 0
    ):
        return 1

    # All other conditions are state 0
    return 0


def verify_state(state: int, peer: Node, other: Node) -> bool:
    """
    Verify that the system is in the specified state.

    Args:
        state: Expected state number (0-4)
        peer: Peer Node object
        other: Other Node object

    Returns:
        True if system is in the specified state, False otherwise
    """
    current_state = which_state(peer=peer, other=other)
    return current_state == state


def wait_state(state: int, peer: Node, other: Node) -> None:
    """
    Wait for the system to reach the specified state.
    Calls verify_state() repeatedly until the desired state is reached.
    Similar to Step 5 in repave.py with retry loop.

    Args:
        state: Desired state number (0-4)
        peer: Peer Node object
        other: Other Node object
    """
    max_retries = 10  # Maximum number of retries
    retry_count = 0

    logger.info(f"Waiting for state {state}...")

    while retry_count < max_retries:
        if retry_count > 0:
            logger.info(f"Retry attempt {retry_count}/{max_retries}...")

        # Check if we're in the desired state
        if verify_state(state=state, peer=peer, other=other):
            logger.info(f"✓ State {state} reached successfully")
            return

        # If not in desired state, wait and retry
        retry_count += 1
        if retry_count < max_retries:
            current_state = which_state(peer=peer, other=other)
            logger.warning(
                f"Current state is {current_state}, not {state}. Waiting 30 seconds before retry..."
            )
            time.sleep(30)
        else:
            current_state = which_state(peer=peer, other=other)
            exit_with_error(
                f"wait_state failed: State {state} not reached after maximum retries (current state: {current_state})"
            )


def main():
    """Main entry point for the get_state script."""
    parser = argparse.ArgumentParser(
        description="Get state of peer and Other configuration"
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
        "--token_peer", required=True, help="Bearer token for peer authentication"
    )
    parser.add_argument("--ip_peer", required=True, help="IP address of the peer node")
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number for peer node"
    )
    parser.add_argument(
        "--token_other", required=True, help="Bearer token for Other authentication"
    )
    parser.add_argument("--ip_other", required=True, help="IP address of the Other node")
    parser.add_argument(
        "--port_other", required=True, type=int, help="Port number for Other node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    logger.debug("Starting get_state.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Peer Token: {args.token_peer[:20]}...")
    logger.debug(f"  Peer IP: {args.ip_peer}")
    logger.debug(f"  Peer Port: {args.port_peer}")
    logger.debug(f"  Other Token: {args.token_other[:20]}...")
    logger.debug(f"  Other IP: {args.ip_other}")
    logger.debug(f"  Other Port: {args.port_other}")

    # Step 0: Verify parameters (same as repave.py)
    logger.info("[STEP 0] Verifying parameters...")

    # Validate IP addresses
    if not validate_ip_address(args.ip_peer):
        exit_with_error(f"Invalid peer IP address: {args.ip_peer}")

    if not validate_ip_address(args.ip_other):
        exit_with_error(f"Invalid Other IP address: {args.ip_other}")

    # Verify IPs are distinct
    if args.ip_peer == args.ip_other:
        exit_with_error(f"Peer and Other IP addresses must be distinct: {args.ip_peer}")

    logger.info("✓ IP addresses validated and are distinct")

    # Validate port numbers
    if not validate_port(args.port_peer):
        exit_with_error(f"Invalid peer port number: {args.port_peer} (must be 0-65535)")

    if not validate_port(args.port_other):
        exit_with_error(f"Invalid Other port number: {args.port_other} (must be 0-65535)")

    # Verify ports are distinct
    if args.port_peer == args.port_other:
        exit_with_error(f"Peer and Other port numbers must be distinct: {args.port_peer}")

    logger.info("✓ Port numbers validated and are distinct")

    # Validate token lengths (361 characters)
    if not validate_token_length(args.token_peer, 361):
        exit_with_error(
            f"Invalid peer token length: {len(args.token_peer)} (expected 361)"
        )

    if not validate_token_length(args.token_other, 361):
        exit_with_error(
            f"Invalid Other token length: {len(args.token_other)} (expected 361)"
        )

    logger.info("✓ Token lengths validated (361 characters)")
    logger.info("✓ All parameter validations passed")

    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    other_node = Node(port=args.port_other, token=args.token_other, ip=args.ip_other)

    logger.info("=" * 60)
    logger.info("Get State")
    logger.info("=" * 60)
    logger.info(
        f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})"
    )
    logger.info(
        f"Other Node: https://localhost:{other_node.port} (forwarded to {other_node.ip})"
    )
    logger.info("=" * 60)

    # Determine and print the current state
    logger.info("Determining current state...")
    current_state = which_state(peer=peer_node, other=other_node)

    logger.info("=" * 60)
    logger.info(f"Current State: {current_state}")
    logger.info("=" * 60)

    # Print state to console (stdout)
    print(current_state)
