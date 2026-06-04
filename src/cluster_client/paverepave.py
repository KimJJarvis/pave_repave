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

from cluster_client.config import config
from cluster_client.node import Node
from cluster_client.peer_info import peer_info
from cluster_client.utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    validate_unique_ips,
    setup_logging,
)
from cluster_client.state_info import (
    get_state3,
    verify_state3,
    wait_state3,
    wait_valid_state3
)
from cluster_client.fail_over import fail_over
from cluster_client.switch_primary_secondary import switch_primary_secondary
from cluster_client.get_integration_token import get_integration_token
from cluster_client.peer_info import peer_info
from cluster_client.leave_cluster_hsa import leave_cluster_hsa
from cluster_client.become_hsa import become_hsa
from cluster_client.get_token import get_token
from cluster_client.state_info import state3_table
from cluster_client.state_info import (
    get_state3,
    state3_table,
    get_state2,
    state2_table,
    wait_valid_state2,
)
from cluster_client.triple_state import get_triple_state, triple_state_table, precondition_triple, postcondition_triple, wait_triple_state
from cluster_client.double_state import get_double_state, double_state_table, precondition_double, postcondition_double, wait_double_state
from cluster_client.single_state import get_single_state, single_state_table, precondition_single, postcondition_single, wait_single_state

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
    precondition_triple(state=2, peer=peer, hsa=hsa, spare=spare)
    logger.info("Calling fail_over on peer...")
    fail_over(node=peer)
    logger.info("✓ fail_over initiated successfully")
    postcondition_triple(state=3, peer=peer, hsa=hsa, spare=spare)


def pave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=3, peer=peer, hsa=hsa, spare=spare)
    id = get_id(node=peer)
    logger.info("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=peer, id=id)
    logger.info("✓ switch_primary_secondary initiated successfully")
    postcondition_triple(state=4, peer=peer, hsa=hsa, spare=spare)


def pave_leave_cluster_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=4, peer=peer, hsa=hsa, spare=spare)
    logger.info("Get integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.info("Calling leave_cluster_hsa on HSA...")
    leave_cluster_hsa(node=peer, integration_token=integration_token)
    logger.info("✓ leave_cluster_hsa initiated successfully")
    postcondition_triple(state=5, peer=peer, hsa=hsa, spare=spare)


def repaveswitch_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=5, peer=peer, hsa=hsa, spare=spare)
    logger.info("Getting integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=hsa.ip, integration_token=integration_token)
    logger.info("✓ become_hsa initiated successfully")
    postcondition_triple(state=6, peer=peer, hsa=hsa, spare=spare)


def repave_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=5, peer=peer, hsa=hsa, spare=spare)
    logger.info("Getting integration token")
    integration_token = get_integration_token(node=hsa)
    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=hsa.ip, integration_token=integration_token)
    logger.info("✓ become_hsa initiated successfully")


def repave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=6, peer=peer, hsa=hsa, spare=spare)
    spare.token = hsa.token
    logger.info("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.info("✓ fail_over initiated successfully")
    postcondition_triple(state=7, peer=peer, hsa=hsa, spare=spare)


def repave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=7, peer=peer, hsa=hsa, spare=spare)
    spare.token = hsa.token
    id = get_id(node=hsa)
    logger.info("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=hsa, id=id)
    logger.info("✓ switch_primary_secondary initiated successfully")
    postcondition_triple(state=8, peer=peer, hsa=hsa, spare=spare)


def switch_fail_over(peer: Node, hsa: Node) -> None:
    logger.debug("switch_fail_over called")
    precondition_double(state=2, peer=peer, hsa=hsa)
    logger.info("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.info("✓ fail_over initiated successfully")
    postcondition_double(state=3, peer=peer, hsa=hsa)


def switch_switch_primary_secondary(peer: Node, hsa: Node) -> None:
    precondition_double(state=3, peer=peer, hsa=hsa)
    id = get_id(node=peer)
    logger.info("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=hsa, id=id)
    logger.info("✓ switch_primary_secondary initiated successfully")
    postcondition_double(state=4, peer=peer, hsa=hsa)


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

    for f in funcs[s - 2 :] if 2 <= s <= len(funcs) + 1 else []:
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

    for f in funcs[s - 2 :] if 2 <= s <= len(funcs) + 1 else []:
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

    for f in funcs[s - 2 :] if 2 <= s <= len(funcs) + 1 else []:
        f(peer=peer, hsa=hsa)


