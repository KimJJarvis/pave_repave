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
    validate_unique_ips,
    setup_logging,
)
from pave_repave.state_info import (
    state_info,
    verify_state,
    wait_state,
    state_description,
)
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.get_integration_token import get_integration_token
from pave_repave.peer_info import peer_info
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.become_hsa import become_hsa
from pave_repave.get_token import get_token

logger = logging.getLogger(__name__)


def precondition(state: int, peer: Node, hsa: Node, spare: Node) -> None:
    """
    Verify that the system is in the expected state.

    Args:
        state: Expected state number
        peer: Peer node
        hsa: HSA node
        spare: Spare node

    Raises:
        ValueError: If system is not in the expected state
    """
    target_state = state
    description = state_description(state=target_state)
    if not verify_state(state=target_state, peer=peer, hsa=hsa, spare=spare):
        raise ValueError(f"System is not in state {target_state}. {description}")
    logger.info(f"✓ System verified to be in state {target_state}. {description}")


def postcondition(state: int, peer: Node, hsa: Node, spare: Node) -> None:
    """
    Wait for the system to reach the expected state and verify.

    Args:
        state: Expected state number
        peer: Peer node
        hsa: HSA node
        spare: Spare node
    """
    target_state = state
    description = state_description(state=target_state)
    logger.info(f"Waiting for system to reach state {target_state}. {description}")
    wait_state(state=target_state, peer=peer, hsa=hsa, spare=spare)
    logger.info(f"✓ System verified to be in state {target_state}. {description}")


def pave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=1, peer=peer, hsa=hsa, spare=spare)
    logger.info("Calling fail_over on peer...")
    fail_over(node=peer)
    logger.info("✓ fail_over initiated successfully")
    postcondition(state=2, peer=peer, hsa=hsa, spare=spare)
    time.sleep(30)


def pave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=2, peer=peer, hsa=hsa, spare=spare)

    logger.info("Getting peer info to obtain peer ID...")
    peer_status = peer_info(node=peer)

    if peer_status is None:
        raise RuntimeError("Could not find peer information")

    id = peer_status.id
    logger.info(f"✓ Peer ID obtained: {id}")

    logger.info("Calling switch_primary_secondary on peer...")
    switch_primary_secondary(node=peer, id=id)

    postcondition(state=3, peer=peer, hsa=hsa, spare=spare)
    time.sleep(30)


def pave_leave_cluster_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=3, peer=peer, hsa=hsa, spare=spare)

    logger.info("Get integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling leave_cluster_hsa on HSA...")
    leave_cluster_hsa(node=peer, integration_token=integration_token)

    postcondition(state=4, peer=peer, hsa=hsa, spare=spare)
    time.sleep(30)


def repave_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=4, peer=peer, hsa=hsa, spare=spare)

    logger.info("Getting integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=hsa.ip, integration_token=integration_token)

    postcondition(state=5, peer=peer, hsa=hsa, spare=spare)
    time.sleep(30)


def repave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=5, peer=peer, hsa=hsa, spare=spare)

    spare.token = hsa.token

    logger.info("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.info("✓ fail_over initiated successfully")

    postcondition(state=6, peer=peer, hsa=hsa, spare=spare)
    time.sleep(30)


def repave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=6, peer=peer, hsa=hsa, spare=spare)

    spare.token = hsa.token

    logger.info("Getting peer info to obtain peer ID...")
    peer_status = peer_info(node=hsa)

    if peer_status is None:
        raise RuntimeError("Could not find peer information")

    id = peer_status.id
    logger.info(f"✓ Peer ID obtained: {id}")

    logger.info("Calling switch_primary_secondary on hsa...")
    switch_primary_secondary(node=hsa, id=id)

    postcondition(state=7, peer=peer, hsa=hsa, spare=spare)


def paverepave(peer: Node, hsa: Node, spare: Node) -> None:
    """
    Perform pave/repave operation on the cluster.

    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node

    Raises:
        ValueError: If IP addresses are not unique or system is not in state 1
        RuntimeError: If peer information cannot be obtained
    """
    # Verify that all IP addresses are unique
    validate_unique_ips(peer.ip, hsa.ip, spare.ip)

    s = state_info(peer, hsa, spare)

    funcs = [
        pave_fail_over,
        pave_switch_primary_secondary,
        pave_leave_cluster_hsa,
        repave_become_hsa,
        repave_fail_over,
        repave_switch_primary_secondary,
    ]

    for f in funcs[s - 1 :] if 1 <= s <= 6 else []:
        f(peer=peer, hsa=hsa, spare=spare)


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
    parser.add_argument("--username", required=True, help="Username for authentication")
    parser.add_argument("--password", required=True, help="Password for authentication")
    parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (in dot format)"
    )
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number for peer node"
    )
    parser.add_argument(
        "--ip_hsa", required=True, help="IP address of the HSA node (in dot format)"
    )
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="Port number for HSA node"
    )
    parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node"
    )
    parser.add_argument(
        "--port_spare", required=True, type=int, help="Port number for spare node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Construct Node objects
    try:
        # Get authentication tokens for each node
        token_peer = get_token(
            username=args.username, password=args.password, port=args.port_peer
        )

        token_hsa = get_token(
            username=args.username, password=args.password, port=args.port_hsa
        )

        token_spare = get_token(
            username=args.username, password=args.password, port=args.port_spare
        )

        peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
        hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
        spare = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)

        paverepave(peer=peer, hsa=hsa, spare=spare)

        print("✓ Pave/Repave completed successfully!")
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"✗ Pave/Repave failed: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Pave/Repave failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Pave/Repave failed with unexpected error: {e}")
        sys.exit(1)
