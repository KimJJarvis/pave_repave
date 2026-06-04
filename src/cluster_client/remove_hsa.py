#!/usr/bin/env python3
"""
Script to remove an HSA from a cluster using NMS API.
Retrieves an integration token from the HSA and calls leave-cluster-hsa on the peer node.
"""

import logging

from cluster_client.get_integration_token import get_integration_token
from cluster_client.leave_cluster_hsa import leave_cluster_hsa
from cluster_client.node import Node
from cluster_client.peer_info import peer_info

logger = logging.getLogger(__name__)


def remove_hsa(peer: Node, hsa: Node) -> None:
    """
    Remove an HSA from the cluster by getting integration token from HSA and calling leave-cluster-hsa on peer.

    Args:
        peer: Node object for the peer node that will execute the leave-cluster-hsa command
        hsa: Node object for the HSA to be removed

    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"remove_hsa called with peer: {peer}, hsa: {hsa}")

    logger.debug("Get integration token")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling leave_cluster_hsa on HSA...")
    leave_cluster_hsa(node=hsa, integration_token=integration_token)

    logger.info("✓ remove_hsa completed successfully")
