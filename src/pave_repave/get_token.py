#!/usr/bin/env python3
"""
Script to retrieve an authentication token from NMS API using username and password.
Makes a POST request to /api/v3/users/signin without requiring a bearer token.
"""

import argparse
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import ssl
import logging
from typing import Dict, Any

from pave_repave.utilities import setup_logging
from pave_repave.config import config

logger = logging.getLogger(__name__)


def get_token(username: str, password: str, port: int) -> str:
    """
    Retrieve authentication token from the NMS API using username and password.

    Args:
        username: Username for authentication
        password: Password for authentication
        port: Port number for the API endpoint

    Returns:
        The authentication token string

    Raises:
        ValueError: If authentication fails or response is invalid
        RuntimeError: If the request fails due to network or other errors
    """
    logger.debug("Retrieving authentication token for port={port}")
    
    base_url = f"https://localhost:{port}"
    url = f"{base_url}/api/v3/users/signin"
    
    # Prepare the request data
    data = {
        "username": username,
        "password": password
    }
    
    logger.debug(f"Making POST request to: {url}")
    logger.debug(f"Request data: {json.dumps({'username': username, 'password': '***'}, indent=2)}")
    
    # Create SSL context that doesn't verify certificates (equivalent to curl -k)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Prepare request data
    request_data = json.dumps(data).encode("utf-8")
    
    # Create request
    request = urllib.request.Request(
        url, data=request_data, headers=headers, method="POST"
    )
    
    logger.debug("Sending request...")
    
    try:
        # Make the request with timeout
        with urllib.request.urlopen(
            request, context=ssl_context, timeout=config.http_timeout_value
        ) as response:
            logger.debug(f"Response status: {response.status}")
            response_data = response.read().decode("utf-8")
            parsed_response = json.loads(response_data)
            logger.debug(f"Response received (token hidden for security)")
            
            # Extract the token from the response
            if "token" not in parsed_response:
                logger.error(f"'token' field not found in response")
                logger.debug(f"Response data: {json.dumps(parsed_response, indent=2)}")
                raise ValueError("'token' field not found in response")
            
            token = parsed_response["token"]
            logger.debug("✓ Authentication token retrieved")
            return token
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logger.error(f"HTTP Error {e.code}: {e.reason}")
        logger.debug(f"URL: {url}")
        logger.debug(f"Response: {error_body}")
        
        # Raise ValueError if authentication fails (401 Unauthorized)
        if e.code == 401:
            logger.error("Authentication failed: Invalid username or password")
            raise ValueError("Authentication failed: Invalid username or password") from e
        
        # For other errors, raise RuntimeError
        logger.error(f"Request failed with status code {e.code}")
        raise RuntimeError(f"HTTP request failed with status code {e.code}: {e.reason}") from e
    
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        logger.error(f"URL: {url}")
        raise RuntimeError(f"URL Error: {e.reason}") from e
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        raise ValueError(f"JSON Decode Error: {e}") from e
    except TimeoutError as e:
        logger.error("Request timed out after 30 seconds")
        logger.error(f"URL: {url}")
        raise RuntimeError("Request timed out after 30 seconds") from e
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        logger.error(f"URL: {url}")

def get_authentication_token(username: str, password: str, ip: str, port: int) -> str:
    """
    Retrieve authentication token from the NMS API using username and password.
    
    Args:
        username: Username for authentication
        password: Password for authentication
        ip: IP address of the node
        port: Port number for the API endpoint
    
    Returns:
        The authentication token string
    
    Raises:
        ValueError: If authentication fails or response is invalid
        RuntimeError: If the request fails due to network or other errors
    """
    logger.debug(f"Retrieving authentication token for ip={ip}, port={port}")
    
    # Use config.host if port_forward is enabled, otherwise use ip
    host = config.host if config.port_forward else ip
    base_url = f"https://{host}:{port}"
    url = f"{base_url}/api/v3/users/signin"
    
    # Prepare the request data
    data = {
        "username": username,
        "password": password
    }
    
    logger.debug(f"Making POST request to: {url}")
    logger.debug(f"Request data: {json.dumps({'username': username, 'password': '***'}, indent=2)}")
    
    # Create SSL context that doesn't verify certificates (equivalent to curl -k)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Prepare request data
    request_data = json.dumps(data).encode("utf-8")
    
    # Create request
    request = urllib.request.Request(
        url, data=request_data, headers=headers, method="POST"
    )
    
    logger.debug("Sending request...")
    
    try:
        # Make the request with timeout
        with urllib.request.urlopen(
            request, context=ssl_context, timeout=config.http_timeout_value
        ) as response:
            logger.debug(f"Response status: {response.status}")
            response_data = response.read().decode("utf-8")
            parsed_response = json.loads(response_data)
            logger.debug(f"Response received (token hidden for security)")
            
            # Extract the token from the response
            if "token" not in parsed_response:
                logger.error(f"'token' field not found in response")
                logger.debug(f"Response data: {json.dumps(parsed_response, indent=2)}")
                raise ValueError("'token' field not found in response")
            
            token = parsed_response["token"]
            logger.debug("✓ Authentication token retrieved")
            return token
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logger.error(f"HTTP Error {e.code}: {e.reason}")
        logger.debug(f"URL: {url}")
        logger.debug(f"Response: {error_body}")
        
        # Raise ValueError if authentication fails (401 Unauthorized)
        if e.code == 401:
            logger.error("Authentication failed: Invalid username or password")
            raise ValueError("Authentication failed: Invalid username or password") from e
        
        # For other errors, raise RuntimeError
        logger.error(f"Request failed with status code {e.code}")
        raise RuntimeError(f"HTTP request failed with status code {e.code}: {e.reason}") from e
    
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        logger.error(f"URL: {url}")
        raise RuntimeError(f"URL Error: {e.reason}") from e
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        raise ValueError(f"JSON Decode Error: {e}") from e
    except TimeoutError as e:
        logger.error("Request timed out after 30 seconds")
        logger.error(f"URL: {url}")
        raise RuntimeError("Request timed out after 30 seconds") from e
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        logger.error(f"URL: {url}")
        raise RuntimeError(f"Unexpected error: {type(e).__name__}: {e}") from e

        raise RuntimeError(f"Unexpected error: {type(e).__name__}: {e}") from e


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Retrieve authentication token from NMS API using username and password."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Log to file instead of console"
    )
    parser.add_argument(
        "--username", required=True, help="Username for authentication"
    )
    parser.add_argument(
        "--password", required=True, help="Password for authentication"
    )
    parser.add_argument(
        "--port", required=True, type=int, help="Port number for the API endpoint"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        # Get authentication token
        token = get_token(username=args.username, password=args.password, port=args.port)

        # Output the token to stdout
        print(token)
    except (ValueError, RuntimeError) as e:
        logger.error(f"Failed to retrieve token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
