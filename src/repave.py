#!/usr/bin/env python3
"""
Repave workflow script that verifies peer and spare configuration.
This script validates parameters, verifies initial state, joins spare to cluster,
performs fail-over and switch operations, and verifies the final state.
"""

import argparse
import sys
import time

from node import Node
from peer_info import peer_info
from get_integration_token import get_integration_token
from become_hsa import become_hsa
from fail_over import fail_over
from switch_primary_secondary import switch_primary_secondary
from get_state import verify_state, wait_state
from utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    exit_with_error
)


def main():
    """Main entry point for the repave workflow script."""
    print("[DEBUG] Starting repave.py script", file=sys.stderr)
    
    parser = argparse.ArgumentParser(
        description="Repave workflow for verifying peer and spare configuration"
    )
    parser.add_argument(
        "--token_peer",
        required=True,
        help="Bearer token for peer authentication"
    )
    parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node"
    )
    parser.add_argument(
        "--port_peer",
        required=True,
        type=int,
        help="Port number for peer node"
    )
    parser.add_argument(
        "--token_spare",
        required=True,
        help="Bearer token for spare authentication"
    )
    parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node"
    )
    parser.add_argument(
        "--port_spare",
        required=True,
        type=int,
        help="Port number for spare node"
    )
    
    args = parser.parse_args()
    
    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Peer Token: {args.token_peer[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   Peer IP: {args.ip_peer}", file=sys.stderr)
    print(f"[DEBUG]   Peer Port: {args.port_peer}", file=sys.stderr)
    print(f"[DEBUG]   Spare Token: {args.token_spare[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   Spare IP: {args.ip_spare}", file=sys.stderr)
    print(f"[DEBUG]   Spare Port: {args.port_spare}", file=sys.stderr)

    # Step 0: Verify parameters
    print("\n[STEP 0] Verifying parameters...", file=sys.stderr)

    # Validate IP addresses
    if not validate_ip_address(args.ip_peer):
        exit_with_error(f"Invalid peer IP address: {args.ip_peer}")
    
    if not validate_ip_address(args.ip_spare):
        exit_with_error(f"Invalid spare IP address: {args.ip_spare}")
    
    # Verify IPs are distinct
    if args.ip_peer == args.ip_spare:
        exit_with_error(f"Peer and spare IP addresses must be distinct: {args.ip_peer}")
    
    print(f"✓ IP addresses validated and are distinct", file=sys.stderr)
    
    # Validate port numbers
    if not validate_port(args.port_peer):
        exit_with_error(f"Invalid peer port number: {args.port_peer} (must be 0-65535)")
    
    if not validate_port(args.port_spare):
        exit_with_error(f"Invalid spare port number: {args.port_spare} (must be 0-65535)")
    
    # Verify ports are distinct
    if args.port_peer == args.port_spare:
        exit_with_error(f"Peer and spare port numbers must be distinct: {args.port_peer}")
    
    print(f"✓ Port numbers validated and are distinct", file=sys.stderr)
    
    # Validate token lengths (361 characters)
    if not validate_token_length(args.token_peer, 361):
        exit_with_error(f"Invalid peer token length: {len(args.token_peer)} (expected 361)")
    
    if not validate_token_length(args.token_spare, 361):
        exit_with_error(f"Invalid spare token length: {len(args.token_spare)} (expected 361)")
    
    print(f"✓ Token lengths validated (361 characters)", file=sys.stderr)
    print("✓ All parameter validations passed", file=sys.stderr)
    
    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    spare_node = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("Repave Workflow", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})", file=sys.stderr)
    print(f"Spare Node: https://localhost:{spare_node.port} (forwarded to {spare_node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Step 1: Verify system is in state 4
    print("\n[STEP 3] Verifying system is in state 4...", file=sys.stderr)
    if not verify_state(state=4, peer=peer_node, hsa=spare_node):
        exit_with_error("System is not in state 4 (peer primary, spare secondary, activeAppliance=PRIMARY)")
    print("✓ System verified to be in state 4", file=sys.stderr)
    print("✓ Step 1 completed successfully", file=sys.stderr)
   
    # Step 3: Get integration token from the peer
    print("\n[STEP 3] Getting integration token from peer...", file=sys.stderr)
    integration_token: str = ""
    try:
        integration_token = get_integration_token(peer_node)
        print(f"✓ Integration token obtained (length: {len(integration_token)})", file=sys.stderr)
        print("✓ Step 3 completed successfully", file=sys.stderr)
    except SystemExit:
        exit_with_error("Failed to get integration token from peer")
    except Exception as e:
        # Check if the response contains HTTP 400 error
        if hasattr(e, 'args') and len(e.args) > 0:
            error_msg = str(e.args[0])
            if '400' in error_msg or 'HTTP' in error_msg:
                exit_with_error(f"get_integration_token returned 400 error: {error_msg}")
        exit_with_error(f"get_integration_token failed: {str(e)}")
    
    # Step 4: Call become_hsa on the spare
    print("\n[STEP 4] Calling become_hsa on spare...", file=sys.stderr)
    try:
        response = become_hsa(spare_node, args.ip_peer, integration_token)
        
        # Check for HTTP status code 200
        http_status = response.get('_http_status_code', 200)  # Default to 200 if not present
        if http_status == 400:
            exit_with_error(f"become_hsa returned HTTP 400: {response}")
        
        if http_status != 200:
            exit_with_error(f"become_hsa returned unexpected HTTP status {http_status}: {response}")
        
        # Check for success message
        status_msg = response.get('status', '')
        if "HSA add successfully initiated" not in status_msg:
            exit_with_error(f"become_hsa did not return expected success message. Got: {status_msg}")
        
        print(f"✓ become_hsa completed successfully: {status_msg}", file=sys.stderr)
        print("✓ Step 4 completed successfully", file=sys.stderr)
    except SystemExit:
        raise  # Re-raise SystemExit to preserve exit_with_error behavior
    except Exception as e:
        exit_with_error(f"become_hsa failed: {str(e)}")

    spare_node.token=peer_node.token

    # Wait for system to reach state 3
    print("\n[STEP 4] Waiting for system to reach state 3...", file=sys.stderr)
    wait_state(1, peer=peer_node, hsa=spare_node)
    print("✓ Step 4 completed successfully", file=sys.stderr)
    
    # Step 6: Call fail_over() on the peer
    print("\n[STEP 6] Calling fail_over on peer...", file=sys.stderr)
    fail_over_response = fail_over(peer_node)
    
    if fail_over_response.code == 400:
        exit_with_error(f"fail_over returned 400: {fail_over_response.message}")
    
    if "LeaderFollower Job Active, cannot Fail-Over" in fail_over_response.message:
        exit_with_error(f"fail_over error: {fail_over_response.message}")
    
    if "Failover successfully started" not in fail_over_response.message:
        exit_with_error(f"Unexpected fail_over response: {fail_over_response.message}")
    
    print("✓ fail_over completed successfully", file=sys.stderr)
    print("✓ Step 6 completed successfully", file=sys.stderr)
    
    # Wait for system to reach state 2
    print("\n[STEP 4] Waiting for system to reach state 2...", file=sys.stderr)
    wait_state(2, peer=peer_node, hsa=spare_node)
    print("✓ Step 4 completed successfully", file=sys.stderr)

    # Step 7: Get peer info to obtain peer ID
    print("\n[STEP 7] Getting peer info to obtain peer ID...", file=sys.stderr)
    peer_status, _ = peer_info(spare_node)
    
    if not peer_status.found:
        exit_with_error("Could not find peer information")
    
    peer_id = peer_status.id
    print(f"✓ Peer ID obtained: {peer_id}", file=sys.stderr)
    print("✓ Step 7 completed successfully", file=sys.stderr)
    
    # Step 8: Call switch_primary_secondary() on the peer
    print("\n[STEP 8] Calling switch_primary_secondary on peer...", file=sys.stderr)
    
    while True:
        switch_response = switch_primary_secondary(peer_node, peer_id)
        
        # Check for LeaderFollower Job Active 
        if "LeaderFollower Job Active, cannot switch-primary-secondary" in switch_response.message:
            print("⚠ LeaderFollower Job Active, waiting 30 seconds before retry...", file=sys.stderr)
            time.sleep(30)
            continue

        # Check for fail over not yet complete 
        if "A secondary-leader appliance was not found on this peer" in switch_response.message:
            print("⚠ Fail over not yet complete, waiting 30 seconds before retry...", file=sys.stderr)
            time.sleep(30)
            continue

        # Now check for other 400 errors
        if switch_response.code == 400:
            exit_with_error(f"switch_primary_secondary returned 400: {switch_response.message}")
        
        # Check for success
        if "The primary / secondary appliance roles on this peer have been switched" in switch_response.message:
            print("✓ switch_primary_secondary completed successfully", file=sys.stderr)
            break
        
        # Any other response is an error
        exit_with_error(f"Unexpected switch_primary_secondary response: {switch_response.message}")
    
    print("✓ Step 8 completed successfully", file=sys.stderr)

    # Wait for system to reach state 1
    print("\n[STEP 4] Waiting for system to reach state 1...", file=sys.stderr)
    wait_state(3,peer=peer_node, hsa=spare_node)
    print("✓ Step 4 completed successfully", file=sys.stderr)

    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Repave workflow completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob