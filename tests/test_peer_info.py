#!/usr/bin/env python3
"""
Tests for peer_info.py module.
"""

import pytest
from unittest.mock import patch, MagicMock

from pave_repave.peer_info import peer_info
from pave_repave.node import Node
from pave_repave.status import Status


@pytest.fixture
def mock_node():
    """Create a mock Node object for testing."""
    return Node(port=443, token="test_token_123", ip="192.168.122.1")


@pytest.fixture
def api_response_primary():
    """API response with PRIMARY active appliance matching target IP."""
    return {
        "peers": [
            {
                "activeAppliance": "PRIMARY",
                "id": 1,
                "primaryIp": "192.168.122.1",
                "secondaryIp": "",
            }
        ]
    }


@pytest.fixture
def api_response_secondary():
    """API response with SECONDARY active appliance."""
    return {
        "peers": [
            {
                "activeAppliance": "SECONDARY",
                "id": 2,
                "primaryIp": "192.168.122.2",
                "secondaryIp": "192.168.122.1",
            }
        ]
    }


@pytest.fixture
def api_response_unknown():
    """API response with UNKNOWN active appliance."""
    return {
        "peers": [
            {
                "activeAppliance": "UNKNOWN",
                "id": 3,
                "primaryIp": "192.168.122.1",
                "secondaryIp": "",
            }
        ]
    }


@pytest.fixture
def api_response_no_match():
    """API response with no matching peer."""
    return {
        "peers": [
            {
                "activeAppliance": "PRIMARY",
                "id": 4,
                "primaryIp": "192.168.122.10",
                "secondaryIp": "192.168.122.11",
            }
        ]
    }


@pytest.fixture
def api_response_empty_peers():
    """API response with empty peers list."""
    return {"peers": []}


@pytest.fixture
def api_response_no_peers_field():
    """API response without peers field."""
    return {}


class TestPeerInfo:
    """Test cases for peer_info function."""

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_primary_match(
        self, mock_api_request, mock_node, api_response_primary
    ):
        """Test parsing response with PRIMARY active appliance matching target IP."""
        mock_api_request.return_value = api_response_primary

        status, response = peer_info(mock_node)

        # Verify API was called correctly
        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert "https://localhost:443/api/v3/peers" in call_args[0][0]
        assert call_args[0][1] == "test_token_123"
        assert call_args[1]["method"] == "GET"

        # Verify status object
        assert status.found is True
        assert status.active_appliance == 1  # PRIMARY = 1
        assert status.primary_ip == "192.168.122.1"
        assert status.secondary_ip == ""
        assert status.id == 1

        # Verify full response is returned
        assert response == api_response_primary

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_secondary_match(
        self, mock_api_request, mock_node, api_response_secondary
    ):
        """Test parsing response with SECONDARY active appliance matching target IP."""
        mock_api_request.return_value = api_response_secondary

        status, response = peer_info(mock_node)

        # Verify status object
        assert status.found is True
        assert status.active_appliance == 2  # SECONDARY = 2
        assert status.primary_ip == "192.168.122.2"
        assert status.secondary_ip == "192.168.122.1"
        assert status.id == 2

        # Verify full response is returned
        assert response == api_response_secondary

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_unknown_appliance(
        self, mock_api_request, mock_node, api_response_unknown
    ):
        """Test parsing response with UNKNOWN active appliance."""
        mock_api_request.return_value = api_response_unknown

        status, response = peer_info(mock_node)

        # Verify status object
        assert status.found is True
        assert status.active_appliance == 0  # UNKNOWN = 0
        assert status.primary_ip == "192.168.122.1"
        assert status.secondary_ip == ""
        assert status.id == 3

        # Verify full response is returned
        assert response == api_response_unknown

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_no_match(
        self, mock_api_request, mock_node, api_response_no_match
    ):
        """Test parsing response when no peer matches target IP."""
        mock_api_request.return_value = api_response_no_match

        status, response = peer_info(mock_node)

        # Verify status object indicates no match
        assert status.found is False
        assert status.active_appliance == 0
        assert status.primary_ip == ""
        assert status.secondary_ip == ""
        assert status.id == 0

        # Verify full response is returned
        assert response == api_response_no_match

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_empty_peers(
        self, mock_api_request, mock_node, api_response_empty_peers
    ):
        """Test parsing response with empty peers list."""
        mock_api_request.return_value = api_response_empty_peers

        status, response = peer_info(mock_node)

        # Verify status object indicates no peers found
        assert status.found is False
        assert status.active_appliance == 0
        assert status.primary_ip == ""
        assert status.secondary_ip == ""
        assert status.id == 0

        # Verify full response is returned
        assert response == api_response_empty_peers

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_no_peers_field(
        self, mock_api_request, mock_node, api_response_no_peers_field
    ):
        """Test parsing response without peers field."""
        mock_api_request.return_value = api_response_no_peers_field

        status, response = peer_info(mock_node)

        # Verify status object indicates peers field not found
        assert status.found is False
        assert status.active_appliance == 0
        assert status.primary_ip == ""
        assert status.secondary_ip == ""
        assert status.id == 0

        # Verify full response is returned
        assert response == api_response_no_peers_field

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_match_secondary_ip(self, mock_api_request, mock_node):
        """Test that peer is matched when target IP matches secondaryIp."""
        response_data = {
            "peers": [
                {
                    "activeAppliance": "PRIMARY",
                    "id": 5,
                    "primaryIp": "192.168.122.5",
                    "secondaryIp": "192.168.122.1",
                }
            ]
        }
        mock_api_request.return_value = response_data

        status, response = peer_info(mock_node)

        # Verify peer is found when secondaryIp matches
        assert status.found is True
        assert status.active_appliance == 1
        assert status.primary_ip == "192.168.122.5"
        assert status.secondary_ip == "192.168.122.1"
        assert status.id == 5

    @patch("pave_repave.peer_info.make_single_api_request")
    def test_peer_info_multiple_peers_finds_match(self, mock_api_request, mock_node):
        """Test that correct peer is found when multiple peers exist."""
        response_data = {
            "peers": [
                {
                    "activeAppliance": "PRIMARY",
                    "id": 1,
                    "primaryIp": "192.168.122.20",
                    "secondaryIp": "",
                },
                {
                    "activeAppliance": "SECONDARY",
                    "id": 2,
                    "primaryIp": "192.168.122.1",
                    "secondaryIp": "192.168.122.21",
                },
                {
                    "activeAppliance": "PRIMARY",
                    "id": 3,
                    "primaryIp": "192.168.122.22",
                    "secondaryIp": "",
                },
            ]
        }
        mock_api_request.return_value = response_data

        status, response = peer_info(mock_node)

        # Verify the matching peer (id=2) is found
        assert status.found is True
        assert status.active_appliance == 2
        assert status.primary_ip == "192.168.122.1"
        assert status.secondary_ip == "192.168.122.21"
        assert status.id == 2

# Made with Bob
