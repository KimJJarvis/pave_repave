#!/usr/bin/env python3
"""
Script to remove a peer from a cluster using NMS API.
Similar to leave_cluster but automatically retrieves the integration token.
"""

import json
import logging

from cluster_client.node import Node
from cluster_client.get_integration_token import get_integration_token
from cluster_client.leave_cluster import leave_cluster

logger = logging.getLogger(__name__)


def remove_peer(cluster: Node, peer: Node) -> None:
    """
    Remove a peer node from the cluster by automatically retrieving the integration token
    and calling leave_cluster.

    Args:
        node_cluster: Node object for the cluster node (the one initiating the removal)
        node_peer: Node object for the peer node to be removed

    Raises:
        RuntimeError: If the API returns HTTP 400, other error status, or unexpected response
    """
    # Log parameters
    logger.debug(f"remove_peer called on cluster node {cluster}, peer node: {peer}")

    # Get integration token from cluster node
    logger.info("Retrieving integration token from cluster node...")
    integration_token = get_integration_token(node=cluster)

    # Call leave_cluster with the retrieved integration token
    logger.info("Calling leave_cluster to remove peer...")
    leave_cluster(
        cluster=cluster,
        peer=peer,
        integration_token=integration_token,
    )

    logger.info(f"✓ remove_peer completed successfully")


# Made with Bob
