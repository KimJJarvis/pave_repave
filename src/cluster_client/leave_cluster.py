#!/usr/bin/env python3
"""
Script to leave a cluster using NMS API.
"""

import json
import logging

from cluster_client.config import config
from cluster_client.get_integration_token import get_integration_token
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def leave_cluster(cluster: Node, peer: Node, force: bool = True) -> None:
    """
    Remove a node from the cluster using the NMS Cluster Orchestrator API.
    
    This function calls the leave-cluster endpoint on the peer node to remove it
    from the cluster. The operation uses an integration token automatically
    retrieved from the cluster node.

    API Endpoint:
        POST /api/v3/cluster-orchestrator/leave-cluster

    Args:
        cluster: Node object for the cluster node (the one initiating the leave operation)
        peer: Node object for the peer node that is leaving the cluster
        force: Whether to force the removal (default: True)

    Raises:
        RuntimeError: If the API returns HTTP 400, other error status, or unexpected response
    """
    integration_token = get_integration_token(node=cluster)

    host = config.host if config.port_forward else peer.ip
    base_url = f"https://{host}:{peer.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster"

    data = {
        "force": force,
        "ip": peer.ip,
        "token": integration_token,
    }

    response = make_single_api_request(
        url=url, bearer_token=cluster.token, method="POST", data=data
    )

    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_message = f"leave_cluster returned HTTP 400: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    if http_status != 200:
        error_message = f"leave_cluster returned unexpected HTTP status {http_status}: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Check for success message
    status_msg = response.get("status", "")
    if "peer successfully removed" not in status_msg.lower():
        error_message = f"leave_cluster did not return expected success message. Got: {status_msg}"
        logger.error(error_message)
        raise RuntimeError(error_message)

