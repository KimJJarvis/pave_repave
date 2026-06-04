#!/usr/bin/env python3
"""
Script to leave an HSA cluster using NMS API.
Retrieves an integration token and calls the leave-cluster-hsa endpoint.
"""

import argparse
import sys
import json
import logging

from cluster_client.node import Node
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.utilities import setup_logging
from cluster_client.get_token import get_token, get_authentication_token
from cluster_client.config import config

logger = logging.getLogger(__name__)


def leave_cluster_hsa(node: Node, integration_token: str) -> None:
    """
    Call the leave-cluster-hsa endpoint.

    Args:
        node: Node object with connection details
        integration_token: Integration token

    Raises:
        RuntimeError: If the API returns HTTP 400 or other error status
    """
    host = config.host if config.port_forward else node.ip
    base_url = f"https://{host}:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster-hsa"

    # Log parameters
    logger.info(f"leave_cluster_hsa called with parameters:")
    logger.info(f"  node.ip: {node.ip}")
    logger.info(f"  node.port: {node.port}")
    logger.info(f"  integration_token: {integration_token[:20]}...")

    logger.info(f"Calling leave-cluster-hsa on {url}...")
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
    logger.info(f"leave_cluster_hsa response:")
    logger.info(json.dumps(response, indent=2))

    status_msg = response.get("status", "unknown")
    logger.info(f"✓ leave-cluster-hsa completed: {status_msg}")

