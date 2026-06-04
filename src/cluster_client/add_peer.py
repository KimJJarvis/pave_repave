#!/usr/bin/env python3
"""
Script to add an HSA to a cluster using NMS API.
Retrieves an integration token from the peer HSA and calls become-hsa on the spare node.
"""

import logging

from cluster_client.get_integration_token import get_integration_token
from cluster_client.join_cluster import join_cluster
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def add_peer(peer: Node, spare: Node, name: str) -> None:
    """
    Add a peer to an existing cluster by getting integration token from a cluster node and calling join_cluster on spare.

    Args:
        peer: Node object for an existing peer (must be in cluster)
        spare: Node object for the spare node to become peer
        name: Name of the peer to be added to the cluster

    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"add_peer called with peer: {peer}, spare: {spare}")

    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling join_cluster on spare...")
    join_cluster(
        peer=peer,
        spare=spare,
        integration_token=integration_token,
        name=name,
    )

    logger.debug("✓ add_peer completed successfully")
