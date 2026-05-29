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
)
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.get_integration_token import get_integration_token
from pave_repave.peer_info import peer_info
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.become_hsa import become_hsa
from pave_repave.get_token import get_token
from pave_repave.state_info import state3_table
from pave_repave.state_info import get_state3, state3_table, get_state2, state2_table, precondition2, postcondition2

logger = logging.getLogger(__name__)

def switch_fail_over(peer: Node, hsa: Node) -> None:
    precondition2(state=3, peer=peer, hsa=hsa)

    logger.info("Calling fail_over on HSA...")
    print("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.info("✓ fail_over initiated successfully")
    print("✓ fail_over initiated successfully")

    postcondition2(state=4, peer=peer, hsa=hsa)

def switch_switch_primary_secondary(peer: Node, hsa: Node) -> None:
    precondition2(state=4, peer=peer, hsa=hsa)

    logger.info("Getting peer info to obtain peer ID...")
    peer_status = peer_info(node=hsa)
    if peer_status is None:
        raise RuntimeError("Could not find peer information")
    id = peer_status.id
    logger.info(f"✓ Peer ID obtained: {id}")

    logger.info("Calling switch_primary_secondary on HSA...")   
    print("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=hsa, id=id)
    logger.info("✓ switch_primary_secondary initiated successfully")
    print("✓ switch_primary_secondary initiated successfully")

    postcondition2(state=5, peer=peer, hsa=hsa)


def switch(peer: Node, hsa: Node) -> None:
    """
    Perform switch operation on the cluster.

    Args:
        peer: Peer node
        hsa: HSA node

    Raises:
        ValueError: If IP addresses are not unique or system is not in state 1
        RuntimeError: If peer information cannot be obtained or validation checks fail
    """
    # Verify that all IP addresses are unique
    validate_unique_ips2(peer.ip, hsa.ip)

    # Wait for a valid (non-zero) state
    s = wait_valid_state2(peer=peer, hsa=hsa)
    print(state2_table(peer=peer, hsa=hsa, state=s))

    funcs = [
        switch_fail_over,
        switch_switch_primary_secondary,
    ]

    for f in funcs[s - 1 :] if 1 <= s <= len(funcs) else []:
        f(peer=peer, hsa=hsa)