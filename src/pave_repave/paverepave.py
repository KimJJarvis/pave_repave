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

from pave_repave.config import config
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
    get_state3,
    verify_state3,
    wait_state3,
    wait_valid_state3,
    precondition3,
    postcondition3,
)
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.get_integration_token import get_integration_token
from pave_repave.peer_info import peer_info
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.become_hsa import become_hsa
from pave_repave.get_token import get_token
from pave_repave.state_info import state3_table
from pave_repave.state_info import get_state3, state3_table, get_state2, state2_table, precondition2, postcondition2, wait_valid_state2

logger = logging.getLogger(__name__)


def get_id(node: Node) -> int:
    """
    Get the peer ID from a node.

    Args:
        node: Node to get the peer ID from

    Returns:
        The peer ID

    Raises:
        RuntimeError: If peer information cannot be obtained
    """
    logger.debug("Getting peer info to obtain peer ID...")
    peer_status = peer_info(node=node)
    if peer_status is None:
        raise RuntimeError("Could not find peer information")
    id = peer_status.id
    logger.debug(f"✓ Peer ID obtained: {id}")
    return id


def pave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    precondition3(state=2, peer=peer, hsa=hsa, spare=spare)
    logger.info("Calling fail_over on peer...")
    fail_over(node=peer)
    logger.info("✓ fail_over initiated successfully")
    postcondition3(state=3, peer=peer, hsa=hsa, spare=spare)
    
def pave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition3(state=3, peer=peer, hsa=hsa, spare=spare)
    id = get_id(node=peer)
    logger.info("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=peer, id=id)
    logger.info("✓ switch_primary_secondary initiated successfully")
    postcondition3(state=4, peer=peer, hsa=hsa, spare=spare)

def pave_leave_cluster_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition3(state=4, peer=peer, hsa=hsa, spare=spare)
    logger.info("Get integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.info("Calling leave_cluster_hsa on HSA...")
    leave_cluster_hsa(node=peer, integration_token=integration_token)
    logger.info("✓ leave_cluster_hsa initiated successfully")
    postcondition3(state=5, peer=peer, hsa=hsa, spare=spare)

def repaveswitch_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition3(state=5, peer=peer, hsa=hsa, spare=spare)
    logger.info("Getting integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=hsa.ip, integration_token=integration_token)
    logger.info("✓ become_hsa initiated successfully")
    postcondition3(state=6, peer=peer, hsa=hsa, spare=spare)

def repave_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition3(state=5, peer=peer, hsa=hsa, spare=spare)
    logger.info("Getting integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=hsa.ip, integration_token=integration_token)
    logger.info("✓ become_hsa initiated successfully")

def repave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    precondition3(state=6, peer=peer, hsa=hsa, spare=spare)
    spare.token = hsa.token
    logger.info("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.info("✓ fail_over initiated successfully")
    postcondition3(state=7, peer=peer, hsa=hsa, spare=spare)

def repave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition3(state=7, peer=peer, hsa=hsa, spare=spare)
    spare.token = hsa.token
    id = get_id(node=hsa)
    logger.info("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=hsa, id=id)
    logger.info("✓ switch_primary_secondary initiated successfully")
    postcondition3(state=8, peer=peer, hsa=hsa, spare=spare)

def switch_fail_over(peer: Node, hsa: Node) -> None:
    logger.debug("switch_fail_over called")
    precondition2(state=2, peer=peer, hsa=hsa)
    logger.info("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.info("✓ fail_over initiated successfully")
    postcondition2(state=3, peer=peer, hsa=hsa)

def switch_switch_primary_secondary(peer: Node, hsa: Node) -> None:
    precondition2(state=3, peer=peer, hsa=hsa)
    id = get_id(node=peer)
    logger.info("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=hsa, id=id)
    logger.info("✓ switch_primary_secondary initiated successfully")
    postcondition2(state=4, peer=peer, hsa=hsa)

def repave(peer: Node, hsa: Node, spare: Node) -> None:
    """
    Perform repave operation on the cluster (states 2-6).

    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node

    Raises:
        ValueError: If IP addresses are not unique or system is not in state 2-6
        RuntimeError: If peer information cannot be obtained or validation checks fail
    """
    # Verify that all IP addresses are unique
    validate_unique_ips(peer.ip, hsa.ip, spare.ip)

    # Wait for a valid (non-zero) state
    s = wait_valid_state3(peer=peer, hsa=hsa, spare=spare)
    print(state3_table(peer=peer, hsa=hsa, spare=spare, state=s))

    funcs = [
        pave_fail_over,
        pave_switch_primary_secondary,
        pave_leave_cluster_hsa,
        repave_become_hsa,
    ]

    for f in funcs[s - 2:] if 2 <= s <= len(funcs) + 1 else []:
        f(peer=peer, hsa=hsa, spare=spare)


def repaveswitch(peer: Node, hsa: Node, spare: Node) -> None:
    """
    Perform pave/repave operation on the cluster (states 2-8).

    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node

    Raises:
        ValueError: If IP addresses are not unique or system is not in state 2-8
        RuntimeError: If peer information cannot be obtained or validation checks fail
    """
    # Verify that all IP addresses are unique
    validate_unique_ips(peer.ip, hsa.ip, spare.ip)

    # Wait for a valid (non-zero) state
    s = wait_valid_state3(peer=peer, hsa=hsa, spare=spare)
    print(state3_table(peer=peer, hsa=hsa, spare=spare, state=s))

    funcs = [
        pave_fail_over,
        pave_switch_primary_secondary,
        pave_leave_cluster_hsa,
        repaveswitch_become_hsa,
        repave_fail_over,
        repave_switch_primary_secondary,
    ]

    for f in funcs[s - 2:] if 2 <= s <= len(funcs) + 1 else []:
        f(peer=peer, hsa=hsa, spare=spare)


def switch(peer: Node, hsa: Node) -> None:
    """
    Perform switch operation on the cluster (states 2-4).

    Args:
        peer: Peer node
        hsa: HSA node

    Raises:
        ValueError: If IP addresses are not unique or system is not in state 2-4
        RuntimeError: If peer information cannot be obtained or validation checks fail
    """
    # Verify that all IP addresses are unique
    validate_unique_ips(peer.ip, hsa.ip)

    # Wait for a valid (non-zero) state
    s = wait_valid_state2(peer=peer, hsa=hsa)
    print(state2_table(peer=peer, hsa=hsa, state=s))

    funcs = [
        switch_fail_over,
        switch_switch_primary_secondary,
    ]

    for f in funcs[s - 2:] if 2 <= s <= len(funcs) + 1 else []:
        f(peer=peer, hsa=hsa)


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

        repaveswitch(peer=peer, hsa=hsa, spare=spare)

        print("✓ SUCCESS: Pave/Repave completed successfully!")
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
