#!/usr/bin/env python3
"""
Script to become an HSA using NMS API.
Retrieves an integration token and calls the become-hsa endpoint.
"""

import argparse
import sys
import json
import logging

from cluster_client.node import Node
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.utilities import setup_logging
from cluster_client.get_token import get_token
from cluster_client.config import config

logger = logging.getLogger(__name__)


def join_cluster(
    cluster: Node, ip_spare: str, integration_token: str, name: str
) -> None:
    """
    Call the join-cluster endpoint.

    Args:
        node: Node object with connection details
        ip_peer: Peer IP address (primary IP)
        integration_token: Integration token
        name: Name of the new node joining the cluster

    Returns:
        Response dictionary from the API

    Raises:
        RuntimeError: If the API returns HTTP 400, other error status, or unexpected response
    """
    # Log parameters
    logger.debug(f"join-cluster called on {cluster}, ip_peer: {ip_spare}, name: {name}")

    host = config.host if config.port_forward else cluster.ip
    base_url = f"https://{host}:{cluster.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/join-cluster"

    data = {
        "clusterNodeIp": cluster.ip,
        "newNodeIp": ip_spare,
        "newNodeName": name,
        "token": integration_token,
    }

    response = make_single_api_request(
        url=url, bearer_token=cluster.token, method="POST", data=data
    )

    # Log response object
    logger.debug(f"join_cluster response: {json.dumps(response, indent=2)}")

    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP 400 Bad Request: {error_msg}")
        raise RuntimeError(f"join_cluster returned HTTP 400: {response}")

    if http_status != 200:
        error_msg = response.get("error", "Unknown error")
        logger.error(f"HTTP {http_status} Error: {error_msg}")
        raise RuntimeError(
            f"join_cluster returned unexpected HTTP status {http_status}: {response}"
        )

    # Check for success message
    status_msg = response.get("status", "")
    logger.debug(f"join_cluster response: {status_msg}")
    if "Peer Add successfully initiated" not in status_msg:
        logger.error(f"Unexpected response status: {status_msg}")
        raise RuntimeError(
            f"join_cluster did not return expected success message. Got: {status_msg}"
        )

    logger.info(f"✓ join- started: {status_msg}")
