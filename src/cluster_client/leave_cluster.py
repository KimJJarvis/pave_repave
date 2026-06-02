#!/usr/bin/env python3
"""
Script to leave a cluster using NMS API.
"""

import json
import logging

from cluster_client.node import Node
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.config import config

logger = logging.getLogger(__name__)


def leave_cluster(cluster: Node, peer: Node, integration_token: str) -> None:
    """
    Call the leave-cluster endpoint to remove a node from the cluster.

    Args:
        node_cluster: Node object for the cluster node (the one initiating the leave)
        node_peer: Node object for the peer node that is leaving
        integration_token: Integration token for the leave-cluster request

    Raises:
        RuntimeError: If the API returns HTTP 400, other error status, or unexpected response
    """
    # Log parameters
    logger.debug(
        f"leave-cluster called on cluster node {cluster}, peer node: {peer}, "
        f"integration_token provided: {bool(integration_token)}"
    )

    host = config.host if config.port_forward else cluster.ip
    base_url = f"https://{host}:{cluster.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster"

    data = {
        "force": True,
        "ip": peer.ip,
        "integrationToken": integration_token,
    }

    response = make_single_api_request(
        url=url, bearer_token=cluster.token, method="POST", data=data
    )

    # Log response object
    logger.debug(f"leave_cluster response: {json.dumps(response, indent=2)}")

    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP 400 Bad Request: {error_msg}")
        raise RuntimeError(f"leave_cluster returned HTTP 400: {response}")

    if http_status != 200:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP {http_status} Error: {error_msg}")
        raise RuntimeError(
            f"leave_cluster returned unexpected HTTP status {http_status}: {response}"
        )

    # Check for success message
    status_msg = response.get("status", "")
    logger.debug(f"leave_cluster response: {status_msg}")
    if "successfully initiated" not in status_msg.lower():
        logger.error(f"Unexpected response status: {status_msg}")
        raise RuntimeError(
            f"leave_cluster did not return expected success message. Got: {status_msg}"
        )

    logger.info(f"✓ leave-cluster started: {status_msg}")


# Made with Bob
