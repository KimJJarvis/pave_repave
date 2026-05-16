#!/usr/bin/env python3
"""
Fused workflow script that orchestrates fail-over, switch-primary-secondary,
get-integration-token, and leave-cluster-hsa operations.
"""

import argparse
import sys
import time
import logging

from pave_repave.node import Node
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.get_integration_token import get_integration_token
from pave_repave.peer_info import peer_info
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.get_state import verify_state, wait_state
from pave_repave.utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    exit_with_error,
    setup_logging,
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the fused workflow script."""
    parser = argparse.ArgumentParser(
        description="Fused workflow for fail-over and cluster operations"
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
    parser.add_argument("--ip_peer", required=True, help="IP address of the peer node")
    parser.add_argument(
        "--token_peer", required=True, help="Bearer token for peer authentication"
    )
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number for peer node"
    )
    parser.add_argument("--ip_hsa", required=True, help="IP address of the HSA node")
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="Port number for HSA node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    logger.debug("Starting pave.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Peer IP: {args.ip_peer}")
    logger.debug(f"  Peer Token: {args.token_peer[:20]}...")
    logger.debug(f"  Peer Port: {args.port_peer}")
    logger.debug(f"  HSA IP: {args.ip_hsa}")
    logger.debug(f"  HSA Port: {args.port_hsa}")

    logger.info("Verifying parameters...")

    # Validate IP addresses
    if not validate_ip_address(args.ip_peer):
        exit_with_error(f"Invalid peer IP address: {args.ip_peer}")

    if not validate_ip_address(args.ip_hsa):
        exit_with_error(f"Invalid HSA IP address: {args.ip_hsa}")

    # Verify IPs are distinct
    if args.ip_peer == args.ip_hsa:
        exit_with_error(f"Peer and HSA IP addresses must be distinct: {args.ip_peer}")

    # Validate port numbers
    if not validate_port(args.port_peer):
        exit_with_error(f"Invalid peer port number: {args.port_peer} (must be 0-65535)")

    if not validate_port(args.port_hsa):
        exit_with_error(f"Invalid HSA port number: {args.port_hsa} (must be 0-65535)")

    # Verify ports are distinct
    if args.port_peer == args.port_hsa:
        exit_with_error(f"Peer and HSA port numbers must be distinct: {args.port_peer}")

    # Validate token length
    if not validate_token_length(args.token_peer, 361):
        exit_with_error(
            f"Invalid peer token length: {len(args.token_peer)} (expected 361)"
        )

    logger.info("✓ All validations passed")

    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=args.token_peer, ip=args.ip_hsa)

    logger.info("=" * 60)
    logger.info("Pave Workflow")
    logger.info("=" * 60)
    logger.info(
        f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})"
    )
    logger.info(
        f"HSA Node: https://localhost:{hsa_node.port} (forwarded to {hsa_node.ip})"
    )
    logger.info("=" * 60)

    logger.info("Verifying system is in state 1...")
    if not verify_state(state=1, peer=peer_node, other=hsa_node):
        exit_with_error(
            "System is not in state 1 (peer primary, hsa secondary, activeAppliance=PRIMARY)"
        )
    logger.info("✓ System verified to be in state 1")

    logger.info("Calling fail_over on peer...")
    fail_over_response = fail_over(node=peer_node)

    if fail_over_response.code == 400:
        exit_with_error(f"fail_over returned 400: {fail_over_response.message}")

    if "LeaderFollower Job Active, cannot Fail-Over" in fail_over_response.message:
        exit_with_error(f"fail_over error: {fail_over_response.message}")

    if "Failover successfully started" not in fail_over_response.message:
        exit_with_error(f"Unexpected fail_over response: {fail_over_response.message}")

    logger.info("✓ fail_over completed successfully")

    logger.info("Waiting for system to reach state 2...")
    wait_state(state=2, peer=peer_node, other=hsa_node)
    logger.info("✓ System verified to be in state 2")

    logger.info("Getting peer info to obtain peer ID...")
    peer_status, _ = peer_info(node=peer_node)

    if not peer_status.found:
        exit_with_error("Could not find peer information")

    peer_id = peer_status.id
    logger.info(f"✓ Peer ID obtained: {peer_id}")

    logger.info("Calling switch_primary_secondary on peer...")
    while True:
        switch_response = switch_primary_secondary(node=peer_node, id=peer_id)

        # Check for LeaderFollower Job Active
        if (
            "LeaderFollower Job Active, cannot switch-primary-secondary"
            in switch_response.message
        ):
            logger.warning(
                "⚠ LeaderFollower Job Active, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Check for fail over not yet complete
        if (
            "A secondary-leader appliance was not found on this peer"
            in switch_response.message
        ):
            logger.warning(
                "⚠ Fail over not yet complete, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Now check for other 400 errors
        if switch_response.code == 400:
            exit_with_error(
                f"switch_primary_secondary returned 400: {switch_response.message}"
            )

        # Check for success
        if (
            "The primary / secondary appliance roles on this peer have been switched"
            in switch_response.message
        ):
            logger.info("✓ switch_primary_secondary completed successfully")
            break

        # Any other response is an error
        exit_with_error(
            f"Unexpected switch_primary_secondary response: {switch_response.message}"
        )

    logger.info("Waiting for system to reach state 3...")
    wait_state(state=3, peer=peer_node, other=hsa_node)
    logger.info("✓ System verified to be in state 3")

    logger.info("Get integration token from peer...")
    integration_token = get_integration_token(node=hsa_node)

    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling leave_cluster_hsa on HSA...")
    try:
        leave_cluster_hsa(node=peer_node, integration_token=integration_token)
        logger.info("✓ leave_cluster_hsa completed successfully")
    except Exception as e:
        exit_with_error(f"leave_cluster_hsa failed: {str(e)}")

    logger.info("Waiting for system to reach state 4...")
    wait_state(state=4, peer=peer_node, other=hsa_node)
    logger.info("✓ System verified to be in state 4")

    logger.info("=" * 60)
    logger.info("✓ Pave workflow completed successfully!")
    logger.info("=" * 60)
