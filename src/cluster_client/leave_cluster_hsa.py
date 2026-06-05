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


def leave_cluster_hsa(hsa: Node, peer: Node, force: bool = True) -> None:
    """
    Remove an HSA (High-Availability Standby Appliance) from the cluster.

    This function retrieves an integration token from the peer node and calls the
    NMS API endpoint `/api/v3/cluster-orchestrator/leave-cluster-hsa` on the HSA
    node to remove it from the cluster.

    API Endpoint:
        POST /api/v3/cluster-orchestrator/leave-cluster-hsa

    Args:
        hsa: Node object for the HSA to be removed from the cluster
        peer: Node object for the peer node to retrieve the integration token from
        force: Whether to force the removal (default: True)

    Raises:
        RuntimeError: If the API returns HTTP 400 (Bad Request) or any other
                     non-200 HTTP status code
    """
    integration_token = get_integration_token(node=peer)
    
    host = config.host if config.port_forward else hsa.ip
    base_url = f"https://{host}:{hsa.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster-hsa"

    data = {"force": force, "ip": hsa.ip, "token": integration_token}

    response = make_single_api_request(
        url=url, bearer_token=hsa.token, method="POST", data=data
    )

    # Check for HTTP status code (default to 200 if not present)
    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_message = f"leave_cluster_hsa returned HTTP 400: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    if http_status != 200:
        error_message = f"leave_cluster_hsa returned unexpected HTTP status {http_status}: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

