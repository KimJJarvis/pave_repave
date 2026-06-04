#!/usr/bin/env python3
"""
Script to leave an HSA cluster using NMS API.
Retrieves an integration token and calls the leave-cluster-hsa endpoint.
"""

import json
import logging

from cluster_client.config import config
from cluster_client.get_integration_token import get_integration_token
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def leave_cluster_hsa(node: Node, peer: Node) -> None:
    """
    Remove an HSA from the cluster by getting integration token from peer and calling leave-cluster-hsa on the HSA node.

    Args:
        node: Node object for the HSA to be removed
        peer: Node object for the peer node to get integration token from

    Raises:
        RuntimeError: If the API returns HTTP 400 or other error status
    """
    logger.debug(f"leave_cluster_hsa called with node: {node}, peer: {peer}")

    # Get integration token from peer
    logger.debug("Get integration token from peer")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    
    host = config.host if config.port_forward else node.ip
    base_url = f"https://{host}:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster-hsa"

    # Log parameters
    logger.debug("leave_cluster_hsa called with parameters:")
    logger.debug(f"  node.ip: {node.ip}")
    logger.debug(f"  node.port: {node.port}")
    logger.debug(f"  integration_token: {integration_token[:20]}...")

    logger.debug(f"Calling leave-cluster-hsa on {url}...")
    data = {"force": True, "ip": node.ip, "token": integration_token}

    response = make_single_api_request(
        url=url, bearer_token=node.token, method="POST", data=data
    )

    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP 400 Bad Request: {error_msg}")
        raise RuntimeError(f"leave_cluster_hsa returned HTTP 400: {response}")

    if http_status != 200:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP {http_status} Error: {error_msg}")
        raise RuntimeError(
            f"leave_cluster_hsa returned unexpected HTTP status {http_status}: {response}"
        )

    # Log response
    logger.debug("leave_cluster_hsa response:")
    logger.debug(json.dumps(response, indent=2))

    status_msg = response.get("status", "unknown")
    logger.debug(f"✓ leave-cluster-hsa completed: {status_msg}")

# Made with Bob
