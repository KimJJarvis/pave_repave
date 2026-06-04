#!/usr/bin/env python3
"""
Script to add an HSA to a cluster using NMS API.
Retrieves an integration token from the peer HSA and calls become-hsa on the spare node.
"""

import argparse
import sys
import json
import logging

from cluster_client.node import Node
from cluster_client.get_integration_token import get_integration_token
from cluster_client.become_hsa import become_hsa
from cluster_client.peer_info import peer_info
from cluster_client.utilities import setup_logging
from cluster_client.get_token import get_token

logger = logging.getLogger(__name__)


def add_hsa(peer: Node, spare: Node) -> None:
    """
    Add an HSA to an existing cluster by getting integration token from peer and calling become-hsa on spare.

    Args:
        peer: Node object for the existing HSA peer (must be in cluster)
        spare: Node object for the spare node to become HSA

    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"add_hsa called with peer: {peer}, spare: {spare}")

    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling become_hsa on spare...")
    become_hsa(node=spare, ip_peer=peer.ip, integration_token=integration_token)

    logger.debug("✓ add_hsa completed successfully")

