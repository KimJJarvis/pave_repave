#!/usr/bin/env python3
"""
Repave workflow script that verifies peer and spare configuration.
This script validates parameters, verifies initial state, joins spare to cluster,
performs fail-over and switch operations, and verifies the final state.
"""

import argparse
import sys
import time
import logging

from pave_repave.node import Node
from pave_repave.peer_info import peer_info
from pave_repave.get_integration_token import get_integration_token
from pave_repave.become_hsa import become_hsa
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.get_state import verify_state, wait_state
from pave_repave.utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    exit_with_error,
    setup_logging,
)

logger = logging.getLogger(__name__)


def repave(peer_node: Node, spare_node: Node, ip_peer: str) -> None:
    """
    Execute the repave workflow.

    Args:
        peer_node: Node object for the peer
        spare_node: Node object for the spare
        ip_peer: IP address of the peer node (used for cluster integration)
    """

    logger.info("=" * 60)
    logger.info("Repave Workflow")
    logger.info("=" * 60)
    logger.info(
        f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})"
    )
    logger.info(
        f"Spare Node: https://localhost:{spare_node.port} (forwarded to {spare_node.ip})"
    )
    logger.info("=" * 60)

    logger.info("Verifying system is in state 5...")
    if not verify_state(state=5, peer=peer_node, other=spare_node):
        exit_with_error(
            "System is not in state 5 (peer primary, spare secondary, activeAppliance=PRIMARY)"
        )
    logger.info("✓ System verified to be in state 5")

    logger.info("Getting integration token from peer...")
    integration_token: str = ""
    try:
        integration_token = get_integration_token(node=peer_node)
        logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    except SystemExit:
        exit_with_error("Failed to get integration token from peer")
    except Exception as e:
        # Check if the response contains HTTP 400 error
        if hasattr(e, "args") and len(e.args) > 0:
            error_msg = str(e.args[0])
            if "400" in error_msg or "HTTP" in error_msg:
                exit_with_error(
                    f"get_integration_token returned 400 error: {error_msg}"
                )
        exit_with_error(f"get_integration_token failed: {str(e)}")

    logger.info("Calling become_hsa on spare...")
    try:
        response = become_hsa(
            node=spare_node, ip_peer=ip_peer, integration_token=integration_token
        )

        # Check for HTTP status code 200
        http_status = response.get(
            "_http_status_code", 200
        )  # Default to 200 if not present
        if http_status == 400:
            exit_with_error(f"become_hsa returned HTTP 400: {response}")

        if http_status != 200:
            exit_with_error(
                f"become_hsa returned unexpected HTTP status {http_status}: {response}"
            )

        # Check for success message
        status_msg = response.get("status", "")
        if "HSA add successfully initiated" not in status_msg:
            exit_with_error(
                f"become_hsa did not return expected success message. Got: {status_msg}"
            )

        logger.info(f"✓ become_hsa completed successfully: {status_msg}")
        logger.info("✓ Step 4 completed successfully")
    except SystemExit:
        raise  # Re-raise SystemExit to preserve exit_with_error behavior
    except Exception as e:
        exit_with_error(f"become_hsa failed: {str(e)}")

    spare_node.token = peer_node.token

    logger.info("Waiting for system to reach state 1...")
    wait_state(state=1, peer=peer_node, other=spare_node)
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
    wait_state(state=2, peer=peer_node, other=spare_node)
    logger.info("✓ System verified to be in state 2")

    logger.info("[STEP 7] Getting peer info to obtain peer ID...")
    peer_status = peer_info(node=spare_node)

    if peer_status is None:
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

    logger.info("✓ Step 8 completed successfully")

    # Wait for system to reach state 3
    logger.info("Waiting for system to reach state 3...")
    wait_state(state=3, peer=peer_node, other=spare_node)
    logger.info("✓ System verified to be in state 3")


def main():
    """Main entry point for the repave workflow script."""
    parser = argparse.ArgumentParser(
        description="The Repave Procedure ensures high availability for a peer in a NMS cluster."
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
    parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number for peer node"
    )
    parser.add_argument(
        "--token_spare", required=True, help="Bearer token for spare authentication"
    )
    parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node (dot format)"
    )
    parser.add_argument(
        "--port_spare", required=True, type=int, help="Port number for spare node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    spare_node = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)

    # Verify IPs are distinct
    if args.ip_peer == args.ip_spare:
        exit_with_error(f"Peer and spare IP addresses must be distinct: {args.ip_peer}")

    # Verify ports are distinct
    if args.port_peer == args.port_spare:
        exit_with_error(
            f"Peer and spare port numbers must be distinct: {args.port_peer}"
        )

    # Execute the repave workflow
    repave(peer_node=peer_node, spare_node=spare_node, ip_peer=args.ip_peer)

    print("✓ Repave workflow completed successfully!")
