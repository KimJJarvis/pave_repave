import json
import logging
import ssl
import urllib.error
import urllib.request

from cluster_client.config import config

logger = logging.getLogger(__name__)
logger.disabled = True  # Completely silences this logger


def get_authentication_token(username: str, password: str, ip: str, port: int) -> str:
    """
    Retrieve authentication token from the NMS API using username and password.
    
    Makes a POST request to /api/v3/users/signin endpoint with SSL verification
    disabled. Uses config.host instead of ip when port forwarding is enabled.

    Args:
        username: Username for authentication
        password: Password for authentication
        ip: IP address of the node (overridden by config.host if port_forward enabled)
        port: HTTPS port number for the NMS API endpoint

    Returns:
        The authentication token string extracted from the API response

    Raises:
        ValueError: If authentication fails (401 Unauthorized), the 'token' field
                   is missing from the response, or JSON decoding fails
        RuntimeError: If the request fails due to HTTP errors (non-401)
    """
    # Use config.host if port_forward is enabled, otherwise use ip
    host = config.host if config.port_forward else ip
    base_url = f"https://{host}:{port}"
    url = f"{base_url}/api/v3/users/signin"

    # Prepare the request data
    data = {"username": username, "password": password}

    # Create SSL context that doesn't verify certificates (equivalent to curl -k)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Prepare headers
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # Prepare request data
    request_data = json.dumps(data).encode("utf-8")

    # Create request
    request = urllib.request.Request(
        url, data=request_data, headers=headers, method="POST"
    )

    try:
        # Make the request with timeout
        with urllib.request.urlopen(
            request, context=ssl_context, timeout=config.http_timeout_value
        ) as response:
            response_data = response.read().decode("utf-8")
            parsed_response = json.loads(response_data)

            # Extract the token from the response
            if "token" not in parsed_response:
                error_message = "'token' field not found in response"
                logger.error(error_message)
                raise ValueError(error_message)

            token = parsed_response["token"]
            return token

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logger.error(f"HTTP Error {e.code}: {e.reason}")

        # Raise ValueError if authentication fails (401 Unauthorized)
        if e.code == 401:
            error_message = "Authentication failed: Invalid username or password"
            logger.error(error_message)
            raise ValueError(error_message) from e

        # For other errors, raise RuntimeError
        error_message = f"HTTP request failed with status code {e.code}: {e.reason}"
        logger.error(error_message)
        raise RuntimeError(error_message) from e

    except json.JSONDecodeError as e:
        error_message = f"JSON Decode Error: {e}"
        logger.error(error_message)
        raise ValueError(error_message) from e
