#!/usr/bin/env python3
"""
Single API request handler for NMS API calls.
Provides SSL context handling, error handling, and debug logging.
Makes a single request without retries.
"""

import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import ssl
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def make_single_api_request(
    url: str,
    bearer_token: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make a single API request to the NMS API without retries.

    Args:
        url: The full URL to request
        bearer_token: The bearer token for authentication
        method: HTTP method (GET or POST)
        data: Optional data dictionary for POST requests

    Returns:
        Response data as dictionary

    Raises:
        SystemExit: If the request fails
    """
    parsed_url = urllib.parse.urlparse(url)
    port = parsed_url.port
    if port is None:
        if parsed_url.scheme == "https":
            port = 443
        elif parsed_url.scheme == "http":
            port = 80
        else:
            port = "unknown"

    logger.debug(f"Making {method} request to: {url}")
    logger.debug(f"Request port: {port}")
    if data:
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")

    # Create SSL context that doesn't verify certificates (equivalent to curl -k)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Prepare headers
    headers = {"Accept": "application/json", "Authorization": f"bearer {bearer_token}"}

    # Prepare request data
    request_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        request_data = json.dumps(data).encode("utf-8")

    # Create request
    request = urllib.request.Request(
        url, data=request_data, headers=headers, method=method
    )

    logger.debug("Sending request...")

    try:
        # Make the request with timeout
        with urllib.request.urlopen(
            request, context=ssl_context, timeout=30
        ) as response:
            logger.debug(f"Response status: {response.status}")
            response_data = response.read().decode("utf-8")
            parsed_response = json.loads(response_data)
            logger.debug(f"Response data: {json.dumps(parsed_response, indent=2)}")
            return parsed_response

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logger.debug(f"HTTP Error {e.code}: {e.reason}")
        logger.debug(f"URL: {url}")
        logger.debug(f"Response: {error_body}")

        # Exit with error if authentication fails (401 Unauthorized)
        if e.code == 401:
            # Check if token is expired or just invalid
            error_message_lower = error_body.lower()
            if (
                "token is expired" in error_message_lower
                or "token expired" in error_message_lower
            ):
                logger.error("Bearer token expired")
            else:
                logger.error("Invalid bearer token")
            sys.exit(1)

        # Parse and return the error response so caller can handle it
        try:
            error_data = json.loads(error_body)
            # Add the HTTP status code to the response
            error_data["_http_status_code"] = e.code
            return error_data
        except json.JSONDecodeError:
            # If response is not JSON, return a structured error
            return {"error": error_body, "_http_status_code": e.code}

    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        logger.error(f"URL: {url}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        sys.exit(1)
    except TimeoutError as e:
        logger.error("Request timed out after 30 seconds")
        logger.error(f"URL: {url}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        logger.error(f"URL: {url}")
        sys.exit(1)
