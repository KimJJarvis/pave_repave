#!/usr/bin/env python3
"""
Get state script that determines the current state of the peer/HSA cluster.
This script performs the same verification as repave.py prior to step 1,
then determines and prints the current state (0-4).
"""

import argparse
from math import e
import sys
import time
import logging

from pave_repave.config import config
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


def str_state(peer: Node, hsa: Node, spare: Node, state: int) -> str:
    """
    Print the status of three nodes in a four-column table format.
    
    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node
        state: Current state number (0-7)
    
    Returns:
        Formatted string with status information in table format
    """
    from pave_repave.peer_info import peer_info
    
    # Get status for each node
    peer_status = peer_info(peer)
    hsa_status = peer_info(hsa)
    spare_status = peer_info(spare)
    
    # Define column headers
    fields = ["active_appliance", "primary_ip", "secondary_ip", "id"]
    
    # Define column widths
    col1_width = 20
    col2_width = 20
    col3_width = 20
    col4_width = 20
    
    # Build the table
    lines = []
    
    # Header row
    header = f"{'Field':<{col1_width}} {'Peer':<{col2_width}} {'HSA':<{col3_width}} {'Spare':<{col4_width}}"
    lines.append(header)
    lines.append("-" * (col1_width + col2_width + col3_width + col4_width + 3))
    
    # Add ip row (first row)
    ip_row = f"{'ip':<{col1_width}} {str(peer.ip):<{col2_width}} {str(hsa.ip):<{col3_width}} {str(spare.ip):<{col4_width}}"
    lines.append(ip_row)
    
    # Add port row (second row)
    port_row = f"{'port':<{col1_width}} {str(peer.port):<{col2_width}} {str(hsa.port):<{col3_width}} {str(spare.port):<{col4_width}}"
    lines.append(port_row)
    
    # Data rows
    for field in fields:
        peer_value = getattr(peer_status, field, "N/A") if peer_status else "N/A"
        hsa_value = getattr(hsa_status, field, "N/A") if hsa_status else "N/A"
        spare_value = getattr(spare_status, field, "N/A") if spare_status else "N/A"
        
        row = f"{field:<{col1_width}} {str(peer_value):<{col2_width}} {str(hsa_value):<{col3_width}} {str(spare_value):<{col4_width}}"
        lines.append(row)
    
    # Add status row with state information
    state_tuple = get_state(state)
    status_row = f"{'status':<{col1_width}} {state_tuple[0]:<{col2_width}} {state_tuple[1]:<{col3_width}} {state_tuple[2]:<{col4_width}}"
    lines.append(status_row)
    
    return "\n".join(lines)

def get_state(state: int) -> tuple[str, str, str]:
    if state == 1:
        return ("active primary","passive secondary","spare")
    elif state == 2:
        return ("passive primary","active secondary","spare")       
    elif state == 3:
        return ("passive secondary", "active primary", "spare")
    elif state == 4:
        return ("retired", "active primary", "spare")
    elif state == 5:
        return ("retired", "active primary", "passive secondary")
    elif state == 6:
        return ("retired", "passive primary", "active secondary")
    elif state == 7:
        return ("retired", "passive secondary", "active primary")
    else: 
        return ("unkown", "unknown", "unknown")

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
        logger.debug(f"Peer is active primary") 
        if (
            hsa_status_on_hsa is not None
            and hsa_status_on_hsa.primary_ip == peer.ip
            and hsa_status_on_hsa.secondary_ip == hsa.ip
            and hsa_status_on_hsa.active_appliance == 1
        ):
            logger.debug(f"HSA is passive secondary") 
            loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
            if (loopback_status_on_spare is not None):
                logger.debug(f"Spare is spare") 
                return 1
            logger.debug(f"Spare is not spare")             
        else:
            logger.debug(f"HSA status does not match")
        return 0             
    elif (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == hsa.ip
        and peer_status_on_peer.active_appliance == 2
    ):
        logger.debug(f"Peer is passive primary")
        if (
            hsa_status_on_hsa is not None
            and hsa_status_on_hsa.primary_ip == peer.ip
            and hsa_status_on_hsa.secondary_ip == hsa.ip
            and hsa_status_on_hsa.active_appliance == 2
        ):
            logger.debug(f"HSA is active secondary") 
            loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
            if (loopback_status_on_spare is not None):
                logger.debug(f"Spare is spare") 
                return 2
            logger.debug(f"Spare is not spare")             
        else:
            logger.debug(f"HSA status does not match")
        return 0             
    elif (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == hsa.ip
        and peer_status_on_peer.secondary_ip == peer.ip
        and peer_status_on_peer.active_appliance == 1
    ):
        logger.debug(f"Peer is passive secondary") 
        if (
            hsa_status_on_hsa is not None
            and hsa_status_on_hsa.primary_ip == hsa.ip
            and hsa_status_on_hsa.secondary_ip == peer.ip
            and hsa_status_on_hsa.active_appliance == 1
        ):
            logger.debug(f"HSA is active secondary") 
            loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
            if (loopback_status_on_spare is not None):
                logger.debug(f"Spare is spare") 
                return 3
            logger.debug(f"Spare is not spare")             
        else:
            logger.debug(f"HSA status does not match")
        return 0             
    elif (
        peer_status_on_peer is not None
        and peer_status_on_peer.primary_ip == peer.ip
        and peer_status_on_peer.secondary_ip == ""
        and peer_status_on_peer.active_appliance == 1
    ):
        logger.debug(f"Peer has no secondary") 
        return 0
    elif (peer_status_on_peer is None):
        logger.debug(f"Peer is not in cluster")
        loopback_status_on_peer=peer_info(Node(port=peer.port, token=peer.token, ip="127.0.0.1")) 
        if (loopback_status_on_peer is not None):
            logger.debug(f"Peer is spare") 
            if (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == hsa.ip
                and hsa_status_on_hsa.secondary_ip == ""
                and hsa_status_on_hsa.active_appliance == 1
            ):
                logger.debug(f"HSA is active primary, stand alone")
                loopback_status_on_spare=peer_info(Node(port=spare.port, token=spare.token, ip="127.0.0.1"))
                if (loopback_status_on_spare is not None):
                    logger.debug(f"Spare is spare") 
                    return 4
            elif (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == hsa.ip
                and hsa_status_on_hsa.secondary_ip == spare.ip
                and hsa_status_on_hsa.active_appliance == 1
            ):
                logger.debug(f"HSA is active primary, spare is passive secondary")
                spare_status_on_spare=peer_info(Node(port=spare.port, token=hsa.token, ip=spare.ip)) 
                if (
                    spare_status_on_spare is not None
                    and spare_status_on_spare.primary_ip == hsa.ip
                    and spare_status_on_spare.secondary_ip == spare.ip
                    and spare_status_on_spare.active_appliance == 1
                ):
                    logger.debug(f"Spare is passive secondary")
                    return 5
                logger.debug(f"Spare status does not match")
                return 0
            elif (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == hsa.ip
                and hsa_status_on_hsa.secondary_ip == spare.ip
                and hsa_status_on_hsa.active_appliance == 2
            ):
                logger.debug(f"HSA is passive primary, spare is active secondary")
                spare_status_on_spare=peer_info(Node(port=spare.port, token=hsa.token, ip=spare.ip)) 
                if (
                    spare_status_on_spare is not None
                    and spare_status_on_spare.primary_ip == hsa.ip
                    and spare_status_on_spare.secondary_ip == spare.ip
                    and spare_status_on_spare.active_appliance == 2
                ):
                    logger.debug(f"Spare is active secondary")
                    return 6
                logger.debug(f"Spare status does not match")
                return 0
            elif (
                hsa_status_on_hsa is not None
                and hsa_status_on_hsa.primary_ip == spare.ip
                and hsa_status_on_hsa.secondary_ip == hsa.ip
                and hsa_status_on_hsa.active_appliance == 1
            ):
                logger.debug(f"HSA is passive secondary, spare is active primary")
                loopback_status_on_spare=peer_info(Node(port=spare.port, token=hsa.token, ip=spare.ip)) 
                if (
                    loopback_status_on_spare is not None
                    and loopback_status_on_spare.primary_ip == spare.ip
                    and loopback_status_on_spare.secondary_ip == hsa.ip
                    and loopback_status_on_spare.active_appliance == 1
                ):
                    logger.debug(f"Spare is active primary")
                    return 7
                logger.debug(f"Spare status does not match")
                return 0
            elif (
                hsa_status_on_hsa is None
            ):
                logger.debug(f"HSA is spare") 
            else: 
                logger.debug(f"Invalid state") 
                return 0
        logger.debug(f"Peer is not spare")             
        return 0             
    else:
        logger.debug(f"Unmatched state")
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
    max_retries = config.wait_state_max_retries
    retry_count = 0

    logger.debug(f"Waiting for state {state}...")

    time.sleep(config.wait_state_initial_delay)
    while retry_count < max_retries:
        if retry_count > 0:
            logger.debug(f"Retry attempt {retry_count}/{max_retries}...")

        # Check if we're in the desired state
        if verify_state(state=state, peer=peer, hsa=hsa, spare=spare):
            logger.debug(f"✓ State {state} reached successfully")
            return

        # If not in desired state, wait and retry
        retry_count += 1
        if retry_count < max_retries:
            current_state = state_info(peer=peer, hsa=hsa, spare=spare)
            logger.warning(
                f"Current state is {current_state}, not {state}. Waiting {config.wait_state_retry_delay} seconds before retry..."
            )
            time.sleep(config.wait_state_retry_delay)
        else:
            current_state = state_info(peer=peer, hsa=hsa, spare=spare)
            raise RuntimeError(
                f"wait_state failed: State {state} not reached after maximum retries (current state: {current_state})"
            )
    time.sleep(config.wait_state_settle_delay)


def wait_valid_state(peer: Node, hsa: Node, spare: Node) -> int:
    """
    Wait for the system to reach a valid (non-zero) state.
    Retries up to 10 times with 30 second waits between attempts.
    
    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node
    
    Returns:
        The valid state number (1-7) when reached
        
    Raises:
        RuntimeError: If a valid state is not reached after maximum retries
    """
    max_retries = config.wait_state_max_retries
    retry_count = 0

    logger.debug("Waiting for valid (non-zero) state...")

    time.sleep(config.wait_state_initial_delay)
    while retry_count < max_retries:
        if retry_count > 0:
            logger.debug(f"Retry attempt {retry_count}/{max_retries}...")

        # Check current state
        current_state = state_info(peer=peer, hsa=hsa, spare=spare)
        
        if current_state != 0:
            logger.debug(f"✓ Valid state {current_state} reached successfully")
            return current_state

        # If still in state 0, wait and retry
        retry_count += 1
        if retry_count < max_retries:
            logger.warning(
                f"Current state is 0 (invalid). Waiting 30 seconds before retry..."
            )
            time.sleep(config.wait_state_retry_delay)
            
    time.sleep(config.wait_state_settle_delay)
    
    # If we exit the loop without returning, raise an error
    raise RuntimeError(
        f"wait_valid_state failed: Valid state not reached after maximum retries (current state: 0)"
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
    logger.debug("Retrieving authentication token for peer node...")
    token_peer = get_token(username=args.username, password=args.password, port=args.port_peer)
    
    logger.debug("Retrieving authentication token for HSA node...")
    token_hsa = get_token(username=args.username, password=args.password, port=args.port_hsa)
    
    logger.debug("Retrieving authentication token for spare node...")
    token_spare = get_token(username=args.username, password=args.password, port=args.port_spare)

    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
    spare_node = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)

    # Determine the current state first
    current_state = state_info(peer=peer_node, hsa=hsa_node, spare=spare_node)

    # Print the state table with state information
    print(str_state(peer=peer_node, hsa=hsa_node, spare=spare_node, state=current_state))
    print()

    # Print state to console (stdout)
    print(f"State: {current_state}")
