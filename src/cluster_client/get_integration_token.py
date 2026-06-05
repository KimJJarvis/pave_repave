import logging

from cluster_client.config import config
from cluster_client.get_authentication_token import get_authentication_token
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node
from cluster_client.utilities import setup_logging

logger = logging.getLogger(__name__)


def get_integration_token(node: Node) -> str:
    """
    Retrieve integration token from the NMS API.

    API Endpoint:
        GET /api/v3/cluster-orchestrator/integration-token

    Args:
        node: Node object with connection details

    Returns:
        The integration token string

    Raises:
        RuntimeError: If HTTP error occurs (status code >= 400) or if 'token'
                     field is not found in the API response
    """
    host = config.host if config.port_forward else node.ip
    base_url = f"https://{host}:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/integration-token"

    response = make_single_api_request(url=url, bearer_token=node.token, method="GET")

    # Check for HTTP error status codes
    if "_http_status_code" in response:
        status_code = response["_http_status_code"]
        if status_code == 400:
            error_message = f"get_integration_token returned HTTP 400: {response}"
            logger.error(error_message)
            raise RuntimeError(error_message)
        elif status_code >= 400:
            error_message = f"get_integration_token returned HTTP {status_code}: {response}"
            logger.error(error_message)
            raise RuntimeError(error_message)

    if "token" not in response:
        error_message = "get_integration_token: 'token' field not found in response"
        logger.error(error_message)
        raise RuntimeError(error_message)

    token = response["token"]
    return token
