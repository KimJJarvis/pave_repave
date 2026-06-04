#!/usr/bin/env python3
"""
Script to retrieve an integration token from NMS API.
Simplified version that only gets and prints the integration token from porta.
"""

import argparse
import logging
import sys

from cluster_client.config import config
from cluster_client.get_authentication_token import get_authentication_token
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node
from cluster_client.utilities import setup_logging

logger = logging.getLogger(__name__)


def get_integration_token(node: Node) -> str:
    """
    Retrieve integration token from the NMS API.

    Args:
        node: Node object with connection details

    Returns:
        The integration token string

    Raises:
        RuntimeError: If token field is not found in response or HTTP error occurs
    """
    logger.debug(
        f"get_integration_token called with node: ip={node.ip}, port={node.port}"
    )
    host = config.host if config.port_forward else node.ip
    base_url = f"https://{host}:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/integration-token"

    response = make_single_api_request(url=url, bearer_token=node.token, method="GET")

    # Check for HTTP error status codes
    if "_http_status_code" in response:
        status_code = response["_http_status_code"]
        if status_code == 400:
            error_msg = response.get("error", "Unknown error")
            logger.error(f"HTTP 400 Bad Request: {error_msg}")
            raise RuntimeError(f"get_integration_token returned HTTP 400: {response}")
        elif status_code >= 400:
            error_msg = response.get("error", "Unknown error")
            logger.error(f"HTTP {status_code} Error: {error_msg}")
            raise RuntimeError(
                f"get_integration_token returned HTTP {status_code}: {response}"
            )

    if "token" not in response:
        logger.error(f"'token' field not found in response: {response}")
        raise RuntimeError("get_integration_token: 'token' field not found in response")

    token = response["token"]
    logger.debug("✓ Integration token retrieved")
    return token
