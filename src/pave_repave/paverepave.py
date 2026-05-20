#!/usr/bin/env python3
"""
Get state script that determines the current state of the peer/HSA cluster.
This script performs the same verification as repave.py prior to step 1,
then determines and prints the current state (0-4).
"""

import argparse
import sys
import time
import logging

from pave_repave.node import Node
from pave_repave.peer_info import peer_info
from pave_repave.utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    validate_unique_ips,
    setup_logging,
)
from pave_repave.state_info import state_info, verify_state, wait_state,state_description
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.get_integration_token import get_integration_token
from pave_repave.peer_info import peer_info
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.become_hsa import become_hsa

logger = logging.getLogger(__name__)


def precondition(state: int, peer: Node, hsa: Node, spare: Node) -> None:
    """
    Verify that the system is in the expected state.
    
    Args:
        state: Expected state number
        peer: Peer node
        hsa: HSA node
        spare: Spare node
        
    Raises:
        ValueError: If system is not in the expected state
    """
    target_state = state
    description = state_description(state=target_state)
    if not verify_state(state=target_state, peer=peer, hsa=hsa, spare=spare):
        raise ValueError(f"System is not in state {target_state}. {description}")
    logger.info(f"✓ System verified to be in state {target_state}. {description}")


def postcondition(state: int, peer: Node, hsa: Node, spare: Node) -> None:
    """
    Wait for the system to reach the expected state and verify.
    
    Args:
        state: Expected state number
        peer: Peer node
        hsa: HSA node
        spare: Spare node
    """
    target_state = state
    description = state_description(state=target_state)
    logger.info(f"Waiting for system to reach state {target_state}. {description}")
    wait_state(state=target_state, peer=peer, hsa=hsa, spare=spare)
    logger.info(f"✓ System verified to be in state {target_state}. {description}")


def pave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    """
    Perform fail-over operation on the peer node.
    
    Verifies system is in state 1, initiates fail-over on peer node,
    and waits for system to reach state 2.
    
    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node
        
    Returns:
        0 on success
        
    Raises:
        ValueError: If system is not in state 1
        RuntimeError: If fail-over fails or returns unexpected response
    """
    precondition(state=1, peer=peer, hsa=hsa, spare=spare)

    logger.info("Calling fail_over on peer...")
    fail_over_response = fail_over(node=peer)

    if fail_over_response.code == 400:
        raise RuntimeError(f"fail_over returned 400: {fail_over_response.message}")

    if "LeaderFollower Job Active, cannot Fail-Over" in fail_over_response.message:
        raise RuntimeError(f"fail_over error: {fail_over_response.message}")

    if "Failover successfully started" not in fail_over_response.message:
        raise RuntimeError(f"Unexpected fail_over response: {fail_over_response.message}")

    logger.info("✓ fail_over initiated successfully")

    postcondition(state=2, peer=peer, hsa=hsa, spare=spare)

def pave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=2, peer=peer, hsa=hsa, spare=spare)

    logger.info("Getting peer info to obtain peer ID...")
    peer_status = peer_info(node=peer)

    if peer_status is None:
        raise RuntimeError("Could not find peer information")

    id = peer_status.id
    logger.info(f"✓ Peer ID obtained: {id}")

    logger.info("Calling switch_primary_secondary on peer...")
    while True:
        switch_response = switch_primary_secondary(node=peer, id=id)

        # Check for LeaderFollower Job Active
        if (
            "LeaderFollower Job Active, cannot switch-primary-secondary"
            in switch_response.message
        ):
            logger.warning(
                "⚠ LeaderFollower Job Active, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Check for fail over not yet complete
        if (
            "A secondary-leader appliance was not found on this peer"
            in switch_response.message
        ):
            logger.warning(
                "⚠ Fail over not yet complete, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Now check for other 400 errors
        if switch_response.code == 400:
            raise RuntimeError(
                f"switch_primary_secondary returned 400: {switch_response.message}"
            )

        # Check for success
        if (
            "The primary / secondary appliance roles on this peer have been switched"
            in switch_response.message
        ):
            logger.info("✓ switch_primary_secondary completed successfully")
            break

        # Any other response is an error
        raise RuntimeError(
            f"Unexpected switch_primary_secondary response: {switch_response.message}"
        )

    postcondition(state=3, peer=peer, hsa=hsa, spare=spare)

def pave_leave_cluster_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=3, peer=peer, hsa=hsa, spare=spare)

    logger.info("Get integration token")
    integration_token = get_integration_token(node=hsa)

    logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")

    logger.info("Calling leave_cluster_hsa on HSA...")
    try:
        leave_cluster_hsa(node=peer, integration_token=integration_token)
        logger.info("✓ leave_cluster_hsa completed successfully")
    except Exception as e:
        raise RuntimeError(f"leave_cluster_hsa failed: {str(e)}")

    postcondition(state=4, peer=peer, hsa=hsa, spare=spare)

def repave_become_hsa(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=4, peer=peer, hsa=hsa, spare=spare)

    logger.info("Getting integration token")
    integration_token: str = ""
    try:
        integration_token = get_integration_token(node=hsa)
        logger.info(f"✓ Integration token obtained (length: {len(integration_token)})")
    except SystemExit:
        raise RuntimeError("Failed to get integration token from peer")
    except Exception as e:
        # Check if the response contains HTTP 400 error
        if hasattr(e, "args") and len(e.args) > 0:
            error_msg = str(e.args[0])
            if "400" in error_msg or "HTTP" in error_msg:
                raise RuntimeError(
                    f"get_integration_token returned 400 error: {error_msg}"
                )
        raise RuntimeError(f"get_integration_token failed: {str(e)}")

    logger.info("Calling become_hsa on spare...")
    try:
        response = become_hsa(
            node=spare, ip_peer=hsa.ip, integration_token=integration_token
        )

        # Check for HTTP status code 200
        http_status = response.get(
            "_http_status_code", 200
        )  # Default to 200 if not present
        if http_status == 400:
            raise RuntimeError(f"become_hsa returned HTTP 400: {response}")

        if http_status != 200:
            raise RuntimeError(
                f"become_hsa returned unexpected HTTP status {http_status}: {response}"
            )

        # Check for success message
        status_msg = response.get("status", "")
        if "HSA add successfully initiated" not in status_msg:
            raise RuntimeError(
                f"become_hsa did not return expected success message. Got: {status_msg}"
            )

        logger.info(f"✓ become_hsa completed successfully: {status_msg}")
        logger.info("✓ Step 4 completed successfully")
    except SystemExit:
        raise  # Re-raise SystemExit to preserve exit_with_error behavior
    except Exception as e:
        raise RuntimeError(f"become_hsa failed: {str(e)}")

    postcondition(state=5, peer=peer, hsa=hsa, spare=spare)
    pass

def repave_fail_over(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=5, peer=peer, hsa=hsa, spare=spare)

    spare.token = hsa.token    
    
    logger.info("Calling fail_over on hsa...")
    fail_over_response = fail_over(node=hsa)

    if fail_over_response.code == 400:
        raise RuntimeError(f"fail_over returned 400: {fail_over_response.message}")

    if "LeaderFollower Job Active, cannot Fail-Over" in fail_over_response.message:
        raise RuntimeError(f"fail_over error: {fail_over_response.message}")

    if "Failover successfully started" not in fail_over_response.message:
        raise RuntimeError(f"Unexpected fail_over response: {fail_over_response.message}")

    logger.info("✓ fail_over initiated successfully")

    postcondition(state=6, peer=peer, hsa=hsa, spare=spare)
    pass

def repave_switch_primary_secondary(peer: Node, hsa: Node, spare: Node) -> None:
    precondition(state=6, peer=peer, hsa=hsa, spare=spare)
    
    spare.token = hsa.token

    logger.info("Getting peer info to obtain peer ID...")
    peer_status = peer_info(node=hsa)

    if peer_status is None:
        raise RuntimeError("Could not find peer information")

    id = peer_status.id
    logger.info(f"✓ Peer ID obtained: {id}")

    logger.info("Calling switch_primary_secondary on hsa...")
    while True:
        switch_response = switch_primary_secondary(node=hsa, id=id)

        # Check for LeaderFollower Job Active
        if (
            "LeaderFollower Job Active, cannot switch-primary-secondary"
            in switch_response.message
        ):
            logger.warning(
                "⚠ LeaderFollower Job Active, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Check for fail over not yet complete
        if (
            "A secondary-leader appliance was not found on this peer"
            in switch_response.message
        ):
            logger.warning(
                "⚠ Fail over not yet complete, waiting 30 seconds before retry..."
            )
            time.sleep(30)
            continue

        # Now check for other 400 errors
        if switch_response.code == 400:
            raise RuntimeError(
                f"switch_primary_secondary returned 400: {switch_response.message}"
            )

        # Check for success
        if (
            "The primary / secondary appliance roles on this peer have been switched"
            in switch_response.message
        ):
            logger.info("✓ switch_primary_secondary completed successfully")
            break

        # Any other response is an error
        raise RuntimeError(
            f"Unexpected switch_primary_secondary response: {switch_response.message}"
        )

    postcondition(state=7, peer=peer, hsa=hsa, spare=spare)
    pass

def paverepave(peer: Node, hsa: Node, spare: Node) -> None:
    """
    Perform pave/repave operation on the cluster.
    
    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node
        
    Raises:
        ValueError: If IP addresses are not unique or system is not in state 1
        RuntimeError: If peer information cannot be obtained
    """
    # Verify that all IP addresses are unique
    validate_unique_ips(peer.ip, hsa.ip, spare.ip)
    logger.info("✓ IP addresses verified to be unique")
    
    s = state_info(peer,hsa,spare)
    
    funcs = [pave_fail_over, pave_switch_primary_secondary, pave_leave_cluster_hsa, repave_become_hsa, repave_fail_over, repave_switch_primary_secondary]

    for f in funcs[s-1:] if 1 <= s <= 6 else []:
        f(peer=peer, hsa=hsa, spare=spare)


def main():
    """Main entry point for the state_info script."""
    parser = argparse.ArgumentParser(
        description="Calls the gRPC endpoint api.v3.peers on the peer node and another node."
    )
    parser.add_argument(
        "--log-level",
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Log to file instead of console"
    )
    parser.add_argument(
        "--token_peer", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip_peer", required=True, help="IP address of the peer node (in dot format)")
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Port number for peer node"
    )
    parser.add_argument(
        "--token_hsa", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip_hsa", required=True, help="IP address of the HSA node (in dot format)")
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="Port number for HSA node"
    )
    parser.add_argument(
        "--token_spare", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip_spare", required=True, help="IP address of the spare node")
    parser.add_argument(
        "--port_spare", required=True, type=int, help="Port number for spare node"
    )

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    # Construct Node objects
    try:
        peer = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
        hsa = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)
        spare = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)

        paverepave(peer=peer, hsa=hsa, spare=spare)

        print("✓ Pave/Repave completed successfully!")
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"✗ Pave/Repave failed: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Pave/Repave failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Pave/Repave failed with unexpected error: {e}")
        sys.exit(1)