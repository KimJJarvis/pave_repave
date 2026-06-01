#!/usr/bin/env python3
"""
Script to add an HSA to a cluster using NMS API.
Retrieves an integration token from the peer HSA and calls become-hsa on the spare node.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.get_integration_token import get_integration_token
from pave_repave.become_hsa import become_hsa
from pave_repave.peer_info import peer_info
from pave_repave.utilities import setup_logging
from pave_repave.get_token import get_token
from pave_repave.join_cluster import join_cluster

logger = logging.getLogger(__name__)

def add_new_peer(cluster: Node, spare: Node, name: str) -> None:
    """
    Add a peer to an existing cluster by getting integration token from a cluster node and calling join_cluster on spare.

    Args:
        peer: Node object for an existing peer (must be in cluster)
        spare: Node object for the spare node to become peer
        name: Name of the peer to be added to the cluster
        
    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"add_peer called with peer: {cluster}, spare: {spare}")
    
    # Validate peer node - should not be in any cluster
    logger.debug("Validating peer node...")
    cluster_status = peer_info(node=cluster)
    
    if cluster_status is not None:
        raise RuntimeError(
            f"Cluster node {cluster.ip} is already in a cluster (primary_ip={cluster_status.primary_ip}, secondary_ip={cluster_status.secondary_ip}). Cannot create new cluster."
        )
    logger.debug("✓ Cluster node validation passed (not found in any cluster)")
    
    # Validate spare node
    logger.debug("Validating spare node...")
    spare_status = peer_info(node=spare)
    if spare_status is not None:
        raise RuntimeError(
            f"Spare node {spare.ip} is already in a cluster (primary_ip={spare_status.primary_ip}, secondary_ip={spare_status.secondary_ip})"
        )
    
    logger.debug("✓ Spare node validation passed (not found in cluster)")


    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=cluster)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    
    logger.info("Calling join_cluster on spare...")
    join_cluster(
        node=spare,
        ip_peer=cluster.ip,
        integration_token=integration_token,
        name=name,
    )
    
    logger.debug("✓ add_peer completed successfully")

def add_peer(cluster: Node, spare: Node, name: str) -> None:
    """
    Add a peer to an existing cluster by getting integration token from a cluster node and calling join_cluster on spare.

    Args:
        peer: Node object for an existing peer (must be in cluster)
        spare: Node object for the spare node to become peer
        name: Name of the peer to be added to the cluster
        
    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """
    logger.info(f"add_peer called with peer: {cluster}, spare: {spare}")
    
    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=cluster)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    
    logger.info("Calling join_cluster on spare...")
    join_cluster(
        node=spare,
        ip_peer=cluster.ip,
        integration_token=integration_token,
        name=name,
    )
    
    logger.debug("✓ add_peer completed successfully")