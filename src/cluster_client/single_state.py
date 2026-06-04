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

from cluster_client.config import config
from cluster_client.node import Node
from cluster_client.peer_info import peer_info
from cluster_client.utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    setup_logging,
)
from cluster_client.peer_info1 import peer_info1

logger = logging.getLogger(__name__)
# logger.disabled = True  # Completely silences this logger

def get_single_state(peer: Node) -> int:
    """
    Determine the current state.
    """
    logger.debug(f"get_single_state {peer}")
    # Get status for each node
    peer_status = peer_info1(peer)

    LOOPBACK="127.0.0.1"

    if peer_status is None:
        logger.debug(f"Unable to get status for Peer")
    elif peer_status.primary_ip==LOOPBACK and peer_status.secondary_ip=="" and peer_status.active_appliance==1:
        logger.debug(f"Peer indicates state 1")
        return 1
    elif peer_status.primary_ip==peer.ip and peer_status.secondary_ip=="" and peer_status.active_appliance==1:
        logger.debug(f"Peer indicates state 2")
        return 2
    elif peer_status.primary_ip==peer.ip and peer_status.secondary_ip!="" and peer_status.active_appliance==1:
        logger.debug(f"Peer indicates state 3")
        return 3
    elif peer_status.primary_ip!="" and peer_status.secondary_ip==peer.ip and peer_status.active_appliance==2:
        logger.debug(f"Peer indicates state 4")
        return 4
    elif peer_status.primary_ip==peer.ip and peer_status.secondary_ip!="" and peer_status.active_appliance==2:
        logger.debug(f"Peer indicates state 5")
        return 5
    elif peer_status.primary_ip!="" and peer_status.secondary_ip==peer.ip and peer_status.active_appliance==1:
        logger.debug(f"Peer indicates state 6")
        return 6
    else:
        return 0
    return 0

def verify_single_state(state: int, peer: Node) -> bool:
    """
    Verify that the system is in the specified state.

    Returns:
        True if system is in the specified state, False otherwise
    """
    current_state = get_single_state(peer=peer)
    return current_state == state

def _wait_for_single_state_condition(
    peer: Node,
    condition_check,
    condition_description: str
) -> int | None:
    """
    Helper function to wait for a state condition to be met.
    
    Args:
        peer: Peer node
        condition_check: Callable that takes current_state and returns (bool, should_return_state)
                        Returns (True, state) if condition met, (False, None) otherwise
        condition_description: Description of the condition being waited for (for logging)
    
    Returns:
        The state when condition is met (if condition_check returns a state)
        
    Raises:
        RuntimeError: If condition is not met after maximum retries
    """
    max_retries = config.wait_state_max_retries
    retry_count = 0

    logger.debug(f"Waiting for {condition_description}...")

    time.sleep(config.wait_state_initial_delay)
    while retry_count < max_retries:
        if retry_count > 0:
            logger.debug(f"Retry attempt {retry_count}/{max_retries}...")

        # Check current state
        current_state = get_single_state(peer=peer)
        
        # Check if condition is met
        condition_met, return_value = condition_check(current_state)
        
        if condition_met:
            logger.debug(f"✓ {condition_description} reached successfully")
            return return_value

        # If condition not met, wait and retry
        retry_count += 1
        if retry_count < max_retries:
            logger.debug(
                f"Current state is {current_state}. Waiting {config.wait_state_retry_delay} seconds before retry..."
            )
            logger.info(
                f"Wait {config.wait_state_retry_delay} seconds. Retry attempt {retry_count}/{max_retries}..."
            )
            time.sleep(config.wait_state_retry_delay)
        else:
            raise RuntimeError(
                f"wait_state failed: {condition_description} not reached after maximum retries (current state: {current_state})"
            )
    
    time.sleep(config.wait_state_settle_delay)


def wait_single_state(state: int, peer: Node) -> None:
    """
    Wait for the system to reach the specified state.
    Calls verify_single_state() repeatedly until the desired state is reached.
    """
    def check_state(current_state):
        if current_state == state:
            return (True, None)
        return (False, None)
    
    _wait_for_single_state_condition(
        peer=peer,
        condition_check=check_state,
        condition_description=f"State {state}"
    )


def wait_valid_single_state(peer: Node) -> int:
    """
    Wait for the system to reach a valid (non-zero) state.
    Retries up to 10 times with 30 second waits between attempts.

    Args:
        peer: Peer node

    Returns:
        The valid state number (1-8) when reached

    Raises:
        RuntimeError: If a valid state is not reached after maximum retries
    """
    def check_valid_state(current_state):
        if current_state != 0:
            return (True, current_state)
        # Log warning for invalid state
        logger.warning(
            f"Current state is 0 (invalid). Waiting {config.wait_state_retry_delay} seconds before retry..."
        )
        print(
            f"Current state is 0 (invalid). Waiting {config.wait_state_retry_delay} seconds before retry..."
        )
        return (False, None)
    
    result = _wait_for_single_state_condition(
        peer=peer,
        condition_check=check_valid_state,
        condition_description="valid (non-zero) state"
    )
    # This should never be None since check_valid_state always returns a state when condition is met
    if result is None:
        raise RuntimeError("Unexpected None return from _wait_for_state_condition")
    return result



def single_state_table(peer: Node) -> str:
    """
    Print the status of a single node in a markdown table format.

    Args:
        peer: Peer node

    Returns:
        Formatted string with status information in markdown table format
    """

    # Get status for the node
    peer_status = peer_info1(peer)

    # Define column headers
    fields = ["active_appliance", "primary_ip", "secondary_ip", "id"]

    # Define column widths for alignment
    col1_width = 18  # Field column
    col2_width = 20  # Peer column

    # Build the table
    lines = []

    # Header row
    header = f"| {'Field':<{col1_width}} | {'Peer':<{col2_width}} |"
    lines.append(header)
    
    # Separator row (markdown table format)
    separator = f"|{'-' * (col1_width + 2)}|{'-' * (col2_width + 2)}|"
    lines.append(separator)

    # Add ip row (first row)
    ip_row = f"| {'ip':<{col1_width}} | {str(peer.ip):<{col2_width}} |"
    lines.append(ip_row)

    # Add port row (second row)
    port_row = f"| {'port':<{col1_width}} | {str(peer.port):<{col2_width}} |"
    lines.append(port_row)

    # Data rows
    for field in fields:
        peer_value = getattr(peer_status, field, "N/A") if peer_status else "N/A"

        # Convert active_appliance integer values to readable strings
        if field == "active_appliance":
            peer_value = (
                "Primary"
                if peer_value == 1
                else ("Secondary" if peer_value == 2 else "N/A")
            )

        row = f"| {field:<{col1_width}} | {str(peer_value):<{col2_width}} |"
        lines.append(row)

    return "\n".join(lines)


def precondition_single(state: int, peer: Node) -> None:
    """
    Verify that the system is in the expected state.

    Args:
        state: Expected state number
        peer: Peer node

    Raises:
        ValueError: If system is not in the expected state
    """
    target_state = state
    if not verify_single_state(state=target_state, peer=peer):
        raise ValueError(f"System is not in state {target_state}.")
    logger.debug(f"✓ System verified to be in state {target_state}.")


def postcondition_single(state: int, peer: Node) -> None:
    """
    Wait for the system to reach the expected state and verify.

    Args:
        state: Expected state number
        peer: Peer node
    """
    target_state = state
    logger.debug(f"Waiting for system to reach state {target_state}.")
    wait_single_state(state=target_state, peer=peer)
    logger.debug(f"✓ System verified to be in state {target_state}.")
