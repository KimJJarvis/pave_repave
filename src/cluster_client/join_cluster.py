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


def join_cluster(peer: Node, spare: Node, name: str) -> None:
    """
    Add a peer to an existing cluster by joining it through the NMS API.

    This function retrieves an integration token from an existing cluster node,
    then calls the join-cluster endpoint on the spare node to add it to the cluster.

    API Endpoint:
        POST /api/v3/cluster-orchestrator/join-cluster

    Args:
        peer: Node object for an existing peer (must be in cluster)
        spare: Node object for the spare node to become peer
        name: Name of the peer to be added to the cluster

    Raises:
        RuntimeError: If any API call fails or validation checks fail
    """

    integration_token = get_integration_token(node=peer)

    host = config.host if config.port_forward else spare.ip
    base_url = f"https://{host}:{spare.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/join-cluster"

    data = {
        "clusterNodeIp": peer.ip,
        "newNodeIp": spare.ip,
        "newNodeName": name,
        "token": integration_token,
    }

    response = make_single_api_request(
        url=url, bearer_token=spare.token, method="POST", data=data
    )

    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_message = f"join_cluster returned HTTP 400: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    if http_status != 200:
        error_message = f"join_cluster returned unexpected HTTP status {http_status}: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Check for success message
    status_msg = response.get("status", "")
    if "Peer Add successfully initiated" not in status_msg:
        error_message = f"join_cluster did not return expected success message. Got: {status_msg}"
        logger.error(error_message)
        raise RuntimeError(error_message)

