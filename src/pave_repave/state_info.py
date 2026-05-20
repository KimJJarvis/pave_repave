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
from pave_repave.get_token import get_token
from pave_repave.utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    setup_logging,
)

logger = logging.getLogger(__name__)


def state_description(state: int) -> str:
    """
    Return the description for a cluster state.
    """
    descriptions = {
        1: "Peer is active primary. HSA is passive secondary. Peer and HSA are synchronised. Spare is spare.",
        2: "Peer is passive primary. HSA is active secondary. Peer and HSA are synchronised. Spare is spare.",
        3: "HSA is active primary. Peer is passive secondary. Peer and HSA are synchronised. Spare is spare.",
        4: "HSA is active primary. Peer is retired. Spare is spare.",
        5: "HSA is active primary. Spare is passive secondary. HSA and Spare are synchronised. Peer is retired.",
        6: "HSA is passive primary. Spare is active secondary. HSA and Spare are synchronised. Peer is retired.",
        7: "Spare is active primary. HSA is passive secondary. HSA and Spare are synchronised. Peer is retired.",
    }
    return descriptions.get(state, "Unknown state")


def state_info(peer: Node, hsa: Node, spare: Node) -> int:
    """
    Determine the current state of the peer/HSA cluster.
    """

    peer_status_on_peer = peer_info(node=peer)
    hsa_status_on_hsa = peer_info(node=hsa)

    if (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 1
    ):
        logger.info(f"Peer is active primary") 
        if (
            hsa_status_on_hsa is not None
            and hsa_status_on_hsa.primary_ip == peer.ip
            and hsa_status_on_hsa.secondary_ip == hsa.ip
            and hsa_status_on_hsa.active_appliance == 1
        ):
            logger.info(f"HSA is passive secondary") 
            loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
            if (loopback_status_on_spare is not None):
                logger.info(f"Spare is spare") 
                return 1
            logger.info(f"Spare is not spare")             
        else:
            logger.info(f"HSA status does not match")
        return 0             
    elif (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 2
    ):
        logger.info(f"Peer is passive primary")
        if (
            hsa_status_on_hsa is not None
            and hsa_status_on_hsa.primary_ip == peer.ip
            and hsa_status_on_hsa.secondary_ip == hsa.ip
            and hsa_status_on_hsa.active_appliance == 2
        ):
            logger.info(f"HSA is active secondary") 
            loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
            if (loopback_status_on_spare is not None):
                logger.info(f"Spare is spare") 
                return 2
            logger.info(f"Spare is not spare")             
        else:
            logger.info(f"HSA status does not match")
        return 0             
    elif (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == hsa.ip
        and peer_status_on_peer.secondary_ip == peer.ip
        and peer_status_on_peer.active_appliance == 1
    ):
        logger.info(f"Peer is passive secondary") 
        if (
            hsa_status_on_hsa is not None
            and hsa_status_on_hsa.primary_ip == hsa.ip
            and hsa_status_on_hsa.secondary_ip == peer.ip
            and hsa_status_on_hsa.active_appliance == 1
        ):
            logger.info(f"HSA is active secondary") 
            loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
            if (loopback_status_on_spare is not None):
                logger.info(f"Spare is spare") 
                return 3
            logger.info(f"Spare is not spare")             
        else:
            logger.info(f"HSA status does not match")
        return 0             
    elif (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == ""
        and peer_status_on_peer.active_appliance == 1
    ):
        logger.info(f"Peer has no secondary") 
        return 0
    elif (peer_status_on_peer is None):
        logger.info(f"Peer is not in cluster")
        loopback_status_on_peer=peer_info(Node(port=peer.port, token=peer.token, ip="127.0.0.1")) 
        if (loopback_status_on_peer is not None):
            logger.info(f"Peer is spare") 
            if (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == hsa.ip
                and hsa_status_on_hsa.secondary_ip == ""
                and hsa_status_on_hsa.active_appliance == 1
            ):
                logger.info(f"HSA is active primary, stand alone")
                loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
                if (loopback_status_on_spare is not None):
                    logger.info(f"Spare is spare") 
                    return 4
            elif (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == hsa.ip
                and hsa_status_on_hsa.secondary_ip == spare.ip
                and hsa_status_on_hsa.active_appliance == 1
            ):
                logger.info(f"HSA is active primary, spare is passive secondary")
                spare_status_on_spare=peer_info(Node(port=spare.port, token=hsa.token, ip=spare.ip)) 
                if (
                    spare_status_on_spare is not None
                    and spare_status_on_spare.primary_ip == hsa.ip
                    and spare_status_on_spare.secondary_ip == spare.ip
                    and spare_status_on_spare.active_appliance == 1
                ):
                    logger.info(f"Spare is passive secondary")
                    return 5
                logger.info(f"Spare status does not match")
                return 0
            elif (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == hsa.ip
                and hsa_status_on_hsa.secondary_ip == spare.ip
                and hsa_status_on_hsa.active_appliance == 2
            ):
                logger.info(f"HSA is passive primary, spare is active secondary")
                spare_status_on_spare=peer_info(Node(port=spare.port, token=hsa.token, ip=spare.ip)) 
                if (
                    spare_status_on_spare is not None
                    and spare_status_on_spare.primary_ip == hsa.ip
                    and spare_status_on_spare.secondary_ip == spare.ip
                    and spare_status_on_spare.active_appliance == 2
                ):
                    logger.info(f"Spare is active secondary")
                    return 6
                logger.info(f"Spare status does not match")
                return 0
            elif (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == spare.ip
                and hsa_status_on_hsa.secondary_ip == hsa.ip
                and hsa_status_on_hsa.active_appliance == 1
            ):
                logger.info(f"HSA is passive secondary, spare is active primary")
                loopback_status_on_spare=peer_info(Node(port=spare.port, token=hsa.token, ip=spare.ip)) 
                if (
                    loopback_status_on_spare is not None
                    and loopback_status_on_spare.primary_ip == spare.ip
                    and loopback_status_on_spare.secondary_ip == hsa.ip
                    and loopback_status_on_spare.active_appliance == 1
                ):
                    logger.info(f"Spare is active primary")
                    return 7
                logger.info(f"Spare status does not match")
                return 0
            elif (
                hsa_status_on_hsa is None
            ):
                logger.info(f"HSA is spare") 
                return 4 # Special initial case
            else: 
                logger.info(f"Invalid state") 
                return 0
        logger.info(f"Peer is not spare")             
        return 0             
    else:
        logger.info(f"Unmatched state")
        return 0             
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
    time.sleep(10) # Wait for process to start

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
            time.sleep(30) # Wait for process
        else:
            current_state = state_info(peer=peer, hsa=hsa, spare=spare)
            raise RuntimeError(
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
        "--username", required=True, help="Username for authentication"
    )
    parser.add_argument(
        "--password", required=True, help="Password for authentication"
    )
    parser.add_argument("--ip_peer", required=True, help="IP address of the peer node (in dot format)")
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number for peer node"
    )
    parser.add_argument("--ip_hsa", required=True, help="IP address of the HSA node (in dot format)")
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="Port number for HSA node"
    )
    parser.add_argument("--ip_spare", required=True, help="IP address of the spare node")
    parser.add_argument(
        "--port_spare", required=True, type=int, help="Port number for spare node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Get authentication tokens for each node
    logger.info("Retrieving authentication token for peer node...")
    token_peer = get_token(username=args.username, password=args.password, port=args.port_peer)
    
    logger.info("Retrieving authentication token for HSA node...")
    token_hsa = get_token(username=args.username, password=args.password, port=args.port_hsa)
    
    logger.info("Retrieving authentication token for spare node...")
    token_spare = get_token(username=args.username, password=args.password, port=args.port_spare)

    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
    spare_node = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)

    # Determine and print the current state
    current_state = state_info(peer=peer_node, hsa=hsa_node, spare=spare_node)

    # Print state to console (stdout)
    print(current_state)
