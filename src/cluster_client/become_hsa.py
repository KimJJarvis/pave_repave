#!/usr/bin/env python3
"""
Script to become an HSA using NMS API.
Retrieves an integration token and calls the become-hsa endpoint.
"""

import json
import logging

from cluster_client.config import config
from cluster_client.get_integration_token import get_integration_token
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def become_hsa(node: Node, peer: Node) -> None:
    """
    Add an HSA to an existing cluster by getting integration token from peer and calling become-hsa on node.

    Args:
        node: Node object for the spare node to become HSA
        peer: Node object for the existing HSA peer (must be in cluster)

    Raises:
        RuntimeError: If the API returns HTTP 400, other error status, or unexpected response
    """
    logger.debug(f"become_hsa called with peer: {peer}, spare: {node}")
    
    # Get integration token from peer
    logger.debug("Getting integration token")
    integration_token = get_integration_token(node=peer)
    logger.debug(f"✓ Integration token obtained (length: {len(integration_token)})")
    
    # Log parameters
    logger.debug(f"Calling become-hsa on {node}")
    
    ip_peer = peer.ip

    host = config.host if config.port_forward else node.ip
    base_url = f"https://{host}:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/become-hsa"

    data = {"primaryIp": ip_peer, "secondaryIp": node.ip, "token": integration_token}

    response = make_single_api_request(
        url=url, bearer_token=node.token, method="POST", data=data
    )

    # Log response object
    logger.debug(f"become_hsa response: {json.dumps(response, indent=2)}")

    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP 400 Bad Request: {error_msg}")
        raise RuntimeError(f"become_hsa returned HTTP 400: {response}")

    if http_status != 200:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP {http_status} Error: {error_msg}")
        raise RuntimeError(
            f"become_hsa returned unexpected HTTP status {http_status}: {response}"
        )

    # Check for success message
    status_msg = response.get("status", "")
    if "HSA add successfully initiated" not in status_msg:
        logger.error(f"Unexpected response status: {status_msg}")
        raise RuntimeError(
            f"become_hsa did not return expected success message. Got: {status_msg}"
        )

    logger.debug(f"✓ become-hsa started: {status_msg}")
