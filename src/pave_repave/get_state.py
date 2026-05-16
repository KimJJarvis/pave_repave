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


def which_state(peer: Node, hsa: Node) -> int:
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
        hsa: HSA Node object
    """
    # Get peer info from peer node
    peer_check_peer = Node(port=peer.port, token=peer.token, ip=peer.ip)
    peer_status_on_peer, _ = peer_info(peer_check_peer)

    hsa_check_peer = Node(port=peer.port, token=peer.token, ip=hsa.ip)
    hsa_status_on_peer, _ = peer_info(hsa_check_peer)

    # Get peer info from hsa node
    peer_check_hsa = Node(port=hsa.port, token=hsa.token, ip=peer.ip)
    peer_status_on_hsa, _ = peer_info(peer_check_hsa)

    hsa_check_hsa = Node(port=hsa.port, token=hsa.token, ip=hsa.ip)
    hsa_status_on_hsa, _ = peer_info(hsa_check_hsa)

    # Also check localhost on both nodes for state 4
    localhost_check_peer = Node(port=peer.port, token=peer.token, ip="127.0.0.1")
    localhost_status_on_peer, _ = peer_info(localhost_check_peer)

    localhost_check_hsa = Node(port=hsa.port, token=hsa.token, ip="127.0.0.1")
    localhost_status_on_hsa, _ = peer_info(localhost_check_hsa)

    logger.debug(f"peer_status_on_peer: {peer_status_on_peer}")
    logger.debug(f"hsa_status_on_peer: {hsa_status_on_peer}")
    logger.debug(f"hsa_status_on_hsa: {hsa_status_on_hsa}")
    logger.debug(f"localhost_status_on_peer: {localhost_status_on_peer}")
    logger.debug(f"localhost_status_on_hsa: {localhost_status_on_hsa}")

    # Check for State 4: Peer standalone, HSA standalone
    # Both nodes are standalone with 127.0.0.1 as primary, no secondary, activeAppliance=PRIMARY
    # Neither node knows about the other's external IP (hsa_ip not found on peer, peer_ip not found on hsa)
    if (
        peer_status_on_peer.found
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == ""
        and peer_status_on_peer.active_appliance == 1
        and not hsa_status_on_peer.found
        and not peer_status_on_hsa.found
        and localhost_status_on_hsa.found
        and localhost_status_on_hsa.primary_ip == "127.0.0.1"
        and localhost_status_on_hsa.secondary_ip == ""
        and localhost_status_on_hsa.active_appliance == 1
    ):
        return 4

    # Print reasons why system is not in state 4
    reasons = []
    if not peer_status_on_peer.found:
        reasons.append(f"peer_status_on_peer.found is False (expected True)")
    if peer_status_on_peer.found and peer_status_on_peer.primary_ip != peer.ip:
        reasons.append(
            f"peer_status_on_peer.primary_ip is '{peer_status_on_peer.primary_ip}' (expected '{peer.ip}')"
        )
    if peer_status_on_peer.found and peer_status_on_peer.secondary_ip != "":
        reasons.append(
            f"peer_status_on_peer.secondary_ip is '{peer_status_on_peer.secondary_ip}' (expected '')"
        )
    if peer_status_on_peer.found and peer_status_on_peer.active_appliance != 1:
        reasons.append(
            f"peer_status_on_peer.active_appliance is {peer_status_on_peer.active_appliance} (expected 1)"
        )
    if hsa_status_on_peer.found:
        reasons.append(f"hsa_status_on_peer.found is True (expected False)")
    if peer_status_on_hsa.found:
        reasons.append(f"peer_status_on_hsa.found is True (expected False)")
    if not localhost_status_on_hsa.found:
        reasons.append(f"localhost_status_on_hsa.found is False (expected True)")
    if (
        localhost_status_on_hsa.found
        and localhost_status_on_hsa.primary_ip != "127.0.0.1"
    ):
        reasons.append(
            f"localhost_status_on_hsa.primary_ip is '{localhost_status_on_hsa.primary_ip}' (expected '127.0.0.1')"
        )
    if localhost_status_on_hsa.found and localhost_status_on_hsa.secondary_ip != "":
        reasons.append(
            f"localhost_status_on_hsa.secondary_ip is '{localhost_status_on_hsa.secondary_ip}' (expected '')"
        )
    if localhost_status_on_hsa.found and localhost_status_on_hsa.active_appliance != 1:
        reasons.append(
            f"localhost_status_on_hsa.active_appliance is {localhost_status_on_hsa.active_appliance} (expected 1)"
        )

    if reasons:
        logger.debug("System is NOT in state 4. Reasons:")
        for reason in reasons:
            logger.debug(f"  - {reason}")

    # Check for State 3: peer is secondary, hsa is primary, activeAppliance=PRIMARY on both
    # Peer: peer_ip is secondary, hsa_ip is primary, activeAppliance=PRIMARY
    # HSA: peer_ip is secondary, hsa_ip is primary, activeAppliance=PRIMARY
    if (
        peer_status_on_peer.found
        and peer_status_on_peer.secondary_ip == peer.ip
        and peer_status_on_peer.primary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 1
        and hsa_status_on_peer.found
        and hsa_status_on_peer.secondary_ip == peer.ip
        and hsa_status_on_peer.primary_ip == hsa.ip
        and hsa_status_on_peer.active_appliance == 1
        and peer_status_on_hsa.found
        and peer_status_on_hsa.secondary_ip == peer.ip
        and peer_status_on_hsa.primary_ip == hsa.ip
        and peer_status_on_hsa.active_appliance == 1
        and hsa_status_on_hsa.found
        and hsa_status_on_hsa.secondary_ip == peer.ip
        and hsa_status_on_hsa.primary_ip == hsa.ip
        and hsa_status_on_hsa.active_appliance == 1
    ):
        return 3

    # Check for State 2: peer is primary, hsa is secondary, activeAppliance=SECONDARY on both
    # Peer: peer_ip is primary, hsa_ip is secondary, activeAppliance=SECONDARY
    # HSA: peer_ip is primary, hsa_ip is secondary, activeAppliance=SECONDARY
    if (
        peer_status_on_peer.found
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 2
        and hsa_status_on_peer.found
        and hsa_status_on_peer.primary_ip == peer.ip
        and hsa_status_on_peer.secondary_ip == hsa.ip
        and hsa_status_on_peer.active_appliance == 2
        and peer_status_on_hsa.found
        and peer_status_on_hsa.primary_ip == peer.ip
        and peer_status_on_hsa.secondary_ip == hsa.ip
        and peer_status_on_hsa.active_appliance == 2
        and hsa_status_on_hsa.found
        and hsa_status_on_hsa.primary_ip == peer.ip
        and hsa_status_on_hsa.secondary_ip == hsa.ip
        and hsa_status_on_hsa.active_appliance == 2
    ):
        return 2

    # Check for State 1: peer is primary, hsa is secondary, activeAppliance=PRIMARY on both
    # Peer: peer_ip is primary, hsa_ip is secondary, activeAppliance=PRIMARY
    # HSA: peer_ip is primary, hsa_ip is secondary, activeAppliance=PRIMARY
    if (
        peer_status_on_peer.found
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 1
        and hsa_status_on_peer.found
        and hsa_status_on_peer.primary_ip == peer.ip
        and hsa_status_on_peer.secondary_ip == hsa.ip
        and hsa_status_on_peer.active_appliance == 1
        and peer_status_on_hsa.found
        and peer_status_on_hsa.primary_ip == peer.ip
        and peer_status_on_hsa.secondary_ip == hsa.ip
        and peer_status_on_hsa.active_appliance == 1
        and hsa_status_on_hsa.found
        and hsa_status_on_hsa.primary_ip == peer.ip
        and hsa_status_on_hsa.secondary_ip == hsa.ip
        and hsa_status_on_hsa.active_appliance == 1
    ):
        return 1

    # All other conditions are state 0
    return 0


def verify_state(state: int, peer: Node, hsa: Node) -> bool:
    """
    Verify that the system is in the specified state.

    Args:
        state: Expected state number (0-4)
        peer: Peer Node object
        hsa: HSA Node object

    Returns:
        True if system is in the specified state, False otherwise
    """
    current_state = which_state(peer, hsa)
    return current_state == state


def wait_state(state: int, peer: Node, hsa: Node) -> None:
    """
    Wait for the system to reach the specified state.
    Calls verify_state() repeatedly until the desired state is reached.
    Similar to Step 5 in repave.py with retry loop.

    Args:
        state: Desired state number (0-4)
        peer: Peer Node object
        hsa: HSA Node object
    """
    max_retries = 10  # Maximum number of retries
    retry_count = 0

    logger.info(f"Waiting for state {state}...")

    while retry_count < max_retries:
        if retry_count > 0:
            logger.info(f"Retry attempt {retry_count}/{max_retries}...")

        # Check if we're in the desired state
        if verify_state(state, peer, hsa):
            logger.info(f"✓ State {state} reached successfully")
            return

        # If not in desired state, wait and retry
        retry_count += 1
        if retry_count < max_retries:
            current_state = which_state(peer, hsa)
            logger.warning(
                f"Current state is {current_state}, not {state}. Waiting 30 seconds before retry..."
            )
            time.sleep(30)
        else:
            current_state = which_state(peer, hsa)
            exit_with_error(
                f"wait_state failed: State {state} not reached after maximum retries (current state: {current_state})"
            )


def main():
    """Main entry point for the get_state script."""
    parser = argparse.ArgumentParser(
        description="Get state of peer and HSA configuration"
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
        "--token_hsa", required=True, help="Bearer token for HSA authentication"
    )
    parser.add_argument("--ip_hsa", required=True, help="IP address of the HSA node")
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="Port number for HSA node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    logger.debug("Starting get_state.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Peer Token: {args.token_peer[:20]}...")
    logger.debug(f"  Peer IP: {args.ip_peer}")
    logger.debug(f"  Peer Port: {args.port_peer}")
    logger.debug(f"  HSA Token: {args.token_hsa[:20]}...")
    logger.debug(f"  HSA IP: {args.ip_hsa}")
    logger.debug(f"  HSA Port: {args.port_hsa}")

    # Step 0: Verify parameters (same as repave.py)
    logger.info("[STEP 0] Verifying parameters...")

    # Validate IP addresses
    if not validate_ip_address(args.ip_peer):
        exit_with_error(f"Invalid peer IP address: {args.ip_peer}")

    if not validate_ip_address(args.ip_hsa):
        exit_with_error(f"Invalid HSA IP address: {args.ip_hsa}")

    # Verify IPs are distinct
    if args.ip_peer == args.ip_hsa:
        exit_with_error(f"Peer and HSA IP addresses must be distinct: {args.ip_peer}")

    logger.info("✓ IP addresses validated and are distinct")

    # Validate port numbers
    if not validate_port(args.port_peer):
        exit_with_error(f"Invalid peer port number: {args.port_peer} (must be 0-65535)")

    if not validate_port(args.port_hsa):
        exit_with_error(f"Invalid HSA port number: {args.port_hsa} (must be 0-65535)")

    # Verify ports are distinct
    if args.port_peer == args.port_hsa:
        exit_with_error(f"Peer and HSA port numbers must be distinct: {args.port_peer}")

    logger.info("✓ Port numbers validated and are distinct")

    # Validate token lengths (361 characters)
    if not validate_token_length(args.token_peer, 361):
        exit_with_error(
            f"Invalid peer token length: {len(args.token_peer)} (expected 361)"
        )

    if not validate_token_length(args.token_hsa, 361):
        exit_with_error(
            f"Invalid HSA token length: {len(args.token_hsa)} (expected 361)"
        )

    logger.info("✓ Token lengths validated (361 characters)")
    logger.info("✓ All parameter validations passed")

    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)

    logger.info("=" * 60)
    logger.info("Get State")
    logger.info("=" * 60)
    logger.info(
        f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})"
    )
    logger.info(
        f"HSA Node: https://localhost:{hsa_node.port} (forwarded to {hsa_node.ip})"
    )
    logger.info("=" * 60)

    # Determine and print the current state
    logger.info("Determining current state...")
    current_state = which_state(peer_node, hsa_node)

    logger.info("=" * 60)
    logger.info(f"Current State: {current_state}")
    logger.info("=" * 60)

    # Print state to console (stdout)
    print(current_state)
