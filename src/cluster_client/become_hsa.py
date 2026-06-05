import json
import logging

from cluster_client.config import config
from cluster_client.get_integration_token import get_integration_token
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def become_hsa(spare: Node, peer: Node) -> None:
    """
    Add an HSA (High-Speed Appliance) to an existing cluster.

    Gets an integration token from the primary peer and calls the
    become-hsa API endpoint on the secondary node to join it to the cluster.

    API Endpoint:
        POST /api/v3/cluster-orchestrator/become-hsa

    Args:
        spare: Node object for the secondary node that will become an HSA
        peer: Node object for the primary HSA node (must already be in cluster)

    Returns:
        None

    Raises:
        RuntimeError: If the API returns HTTP 400, non-200 status, or doesn't
            return the expected success message "HSA add successfully initiated"
    """
    integration_token = get_integration_token(node=peer)

    host = config.host if config.port_forward else spare.ip
    base_url = f"https://{host}:{spare.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/become-hsa"

    data = {"primaryIp": peer.ip, "secondaryIp": spare.ip, "token": integration_token}

    response = make_single_api_request(
        url=url, bearer_token=spare.token, method="POST", data=data
    )

    http_status = response.get("_http_status_code", 200)

    if http_status == 400:
        error_message = f"become_hsa returned HTTP 400: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    if http_status != 200:
        error_message = f"become_hsa returned unexpected HTTP status {http_status}: {response}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Check for success message
    status_msg = response.get("status", "")
    if "HSA add successfully initiated" not in status_msg:
        error_message = f"become_hsa did not return expected success message. Got: {status_msg}"
        logger.error(error_message)
        raise RuntimeError(error_message)
