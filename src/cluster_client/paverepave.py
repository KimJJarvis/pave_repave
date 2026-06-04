#!/usr/bin/env python3
"""
Get state script that determines the current state of the peer/HSA cluster.
This script performs the same verification as repave.py prior to step 1,
then determines and prints the current state (0-4).
"""

import logging

from cluster_client.become_hsa import become_hsa
from cluster_client.double_state import (
    postcondition_double,
    precondition_double,
    wait_valid_double_state,
)
from cluster_client.fail_over import fail_over
from cluster_client.get_integration_token import get_integration_token
from cluster_client.leave_cluster_hsa import leave_cluster_hsa
from cluster_client.node import Node
from cluster_client.peer_info import peer_info
from cluster_client.switch_primary_secondary import switch_primary_secondary
from cluster_client.triple_state import (
    postcondition_triple,
    precondition_triple,
    wait_valid_triple_state,
)


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
    logger.debug("Calling fail_over on peer...")
    fail_over(node=peer)
    logger.debug("✓ fail_over initiated successfully")
    postcondition_triple(state=3, peer=peer, hsa=hsa, spare=spare)


def pave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=3, peer=peer, hsa=hsa, spare=spare)
    id = get_id(node=peer)
    logger.debug("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=peer, id=id)
    logger.debug("✓ switch_primary_secondary initiated successfully")
    postcondition_triple(state=4, peer=peer, hsa=hsa, spare=spare)


def pave_leave_cluster_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=4, peer=peer, hsa=hsa, spare=spare)
    logger.debug("Get integration token")
    integration_token = get_integration_token(node=hsa)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.debug("Calling leave_cluster_hsa on HSA...")
    leave_cluster_hsa(node=peer, integration_token=integration_token)
    logger.debug("✓ leave_cluster_hsa initiated successfully")
    postcondition_triple(state=5, peer=peer, hsa=hsa, spare=spare)


def repaveswitch_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=5, peer=peer, hsa=hsa, spare=spare)
    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=hsa)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.debug("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=hsa.ip, integration_token=integration_token)
    logger.debug("✓ become_hsa initiated successfully")
    postcondition_triple(state=6, peer=peer, hsa=hsa, spare=spare)


def repave_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=5, peer=peer, hsa=hsa, spare=spare)
    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=hsa)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    logger.debug("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=hsa.ip, integration_token=integration_token)
    logger.debug("✓ become_hsa initiated successfully")


def repave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=6, peer=peer, hsa=hsa, spare=spare)
    spare.token = hsa.token
    logger.debug("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.debug("✓ fail_over initiated successfully")
    postcondition_triple(state=7, peer=peer, hsa=hsa, spare=spare)


def repave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition_triple(state=7, peer=peer, hsa=hsa, spare=spare)
    spare.token = hsa.token
    id = get_id(node=hsa)
    logger.debug("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=hsa, id=id)
    logger.debug("✓ switch_primary_secondary initiated successfully")
    postcondition_triple(state=8, peer=peer, hsa=hsa, spare=spare)


def switch_fail_over(peer: Node, hsa: Node) -> None:
    logger.debug("switch_fail_over called")
    precondition_double(state=2, peer=peer, hsa=hsa)
    logger.debug("Calling fail_over on HSA...")
    fail_over(node=hsa)
    logger.debug("✓ fail_over initiated successfully")
    postcondition_double(state=3, peer=peer, hsa=hsa)


def switch_switch_primary_secondary(peer: Node, hsa: Node) -> None:
    precondition_double(state=3, peer=peer, hsa=hsa)
    id = get_id(node=peer)
    logger.debug("Calling switch_primary_secondary on HSA...")
    switch_primary_secondary(node=hsa, id=id)
    logger.debug("✓ switch_primary_secondary initiated successfully")
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

    # Wait for a valid (non-zero) state
    s = wait_valid_triple_state(peer=peer, hsa=hsa, spare=spare)

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

    # Wait for a valid (non-zero) state
    s = wait_valid_triple_state(peer=peer, hsa=hsa, spare=spare)

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


