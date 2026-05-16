#!/usr/bin/env python3
"""
Fused workflow script that orchestrates fail-over, switch-primary-secondary,
get-integration-token, and leave-cluster-hsa operations.
"""

import argparse
import sys
import time

from node import Node
from fail_over import fail_over
from switch_primary_secondary import switch_primary_secondary
from get_integration_token import get_integration_token
from peer_info import peer_info
from leave_cluster_hsa import leave_cluster_hsa
from get_state import verify_state, wait_state
from utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    exit_with_error
)


def main():
    """Main entry point for the fused workflow script."""
    print("[DEBUG] Starting fused.py script", file=sys.stderr)
    
    parser = argparse.ArgumentParser(
        description="Fused workflow for fail-over and cluster operations"
    )
    parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node"
    )
    parser.add_argument(
        "--token_peer",
        required=True,
        help="Bearer token for peer authentication"
    )
    parser.add_argument(
        "--port_peer",
        required=True,
        type=int,
        help="Port number for peer node"
    )
    parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node"
    )
    parser.add_argument(
        "--port_hsa",
        required=True,
        type=int,
        help="Port number for HSA node"
    )
    
    args = parser.parse_args()
    
    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Peer IP: {args.ip_peer}", file=sys.stderr)
    print(f"[DEBUG]   Peer Token: {args.token_peer[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   Peer Port: {args.port_peer}", file=sys.stderr)
    print(f"[DEBUG]   HSA IP: {args.ip_hsa}", file=sys.stderr)
    print(f"[DEBUG]   HSA Port: {args.port_hsa}", file=sys.stderr)

    print("\nVerifying parameters...", file=sys.stderr)

    # Validate IP addresses
    if not validate_ip_address(args.ip_peer):
        exit_with_error(f"Invalid peer IP address: {args.ip_peer}")
    
    if not validate_ip_address(args.ip_hsa):
        exit_with_error(f"Invalid HSA IP address: {args.ip_hsa}")
    
    # Verify IPs are distinct
    if args.ip_peer == args.ip_hsa:
        exit_with_error(f"Peer and HSA IP addresses must be distinct: {args.ip_peer}")
    
    # Validate port numbers
    if not validate_port(args.port_peer):
        exit_with_error(f"Invalid peer port number: {args.port_peer} (must be 0-65535)")
    
    if not validate_port(args.port_hsa):
        exit_with_error(f"Invalid HSA port number: {args.port_hsa} (must be 0-65535)")
    
    # Verify ports are distinct
    if args.port_peer == args.port_hsa:
        exit_with_error(f"Peer and HSA port numbers must be distinct: {args.port_peer}")
    
    # Validate token length
    if not validate_token_length(args.token_peer, 361):
        exit_with_error(f"Invalid peer token length: {len(args.token_peer)} (expected 361)")
    
    print("✓ All validations passed", file=sys.stderr)
    
    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=args.token_peer, ip=args.ip_hsa)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("Fused Workflow", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})", file=sys.stderr)
    print(f"HSA Node: https://localhost:{hsa_node.port} (forwarded to {hsa_node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    print("\nVerifying system is in state 1...", file=sys.stderr)
    if not verify_state(1, peer_node, hsa_node):
        exit_with_error("System is not in state 1 (peer primary, hsa secondary, activeAppliance=PRIMARY)")
    print("✓ System verified to be in state 1", file=sys.stderr)
    
    print("\nCalling fail_over on peer...", file=sys.stderr)
    fail_over_response = fail_over(peer_node)
    
    if fail_over_response.code == 400:
        exit_with_error(f"fail_over returned 400: {fail_over_response.message}")
    
    if "LeaderFollower Job Active, cannot Fail-Over" in fail_over_response.message:
        exit_with_error(f"fail_over error: {fail_over_response.message}")
    
    if "Failover successfully started" not in fail_over_response.message:
        exit_with_error(f"Unexpected fail_over response: {fail_over_response.message}")
    
    print("✓ fail_over completed successfully", file=sys.stderr)
    
    print("\nWaiting for system to reach state 2...", file=sys.stderr)
    wait_state(2, peer_node, hsa_node)
    print("✓ System verified to be in state 2", file=sys.stderr)

    print("\nGetting peer info to obtain peer ID...", file=sys.stderr)
    peer_status, _ = peer_info(peer_node)
    
    if not peer_status.found:
        exit_with_error("Could not find peer information")
    
    peer_id = peer_status.id
    print(f"✓ Peer ID obtained: {peer_id}", file=sys.stderr)
    
    print("\nCalling switch_primary_secondary on peer...", file=sys.stderr)
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

    print("\nWaiting for system to reach state 3...", file=sys.stderr)
    wait_state(3, peer_node, hsa_node)
    print("✓ System verified to be in state 3", file=sys.stderr)

    print("\nGet integration token from peer...", file=sys.stderr)
    integration_token = get_integration_token(hsa_node)
      
    print(f"✓ Integration token obtained (length: {len(integration_token)})", file=sys.stderr)
    
    print("\nCalling leave_cluster_hsa on HSA...", file=sys.stderr)
    try:
        leave_cluster_hsa(peer_node, integration_token)
        print("✓ leave_cluster_hsa completed successfully", file=sys.stderr)
    except Exception as e:
        exit_with_error(f"leave_cluster_hsa failed: {str(e)}")
    
    print("\nWaiting for system to reach state 4...", file=sys.stderr)
    wait_state(4, peer_node, hsa_node)
    print("✓ System verified to be in state 4", file=sys.stderr)

    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Pave workflow completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob