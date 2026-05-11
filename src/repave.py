#!/usr/bin/env python3
"""
Repave workflow script that verifies peer and HSA configuration.
This script validates parameters, verifies initial state, joins HSA to cluster,
performs fail-over and switch operations, and verifies the final state.
"""

import argparse
import sys
import time

from node import Node
from peer_info import get_peer_info as get_peer_info_v3
from get_peer_info import get_peer_info
from get_integration_token import get_integration_token
from become_hsa import become_hsa
from fail_over import fail_over
from switch_primary_secondary import switch_primary_secondary
from utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    exit_with_error
)


def verify_peer_on_peer(peer_node: Node, node_ip: str, hsa_ip: str):
    """
    Verify peer information on the peer node.
    
    Expected state on peer:
    - node_ip should be found and be a primaryIp
    - hsa_ip should be not found
    - secondaryIp should be empty
    - activeAppliance should be PRIMARY
    
    Args:
        peer_node: Peer Node object to query
        node_ip: Expected node IP address
        hsa_ip: HSA IP address (should not be found)
    """
    print(f"\n[PEER] Verifying peer information...", file=sys.stderr)
    
    # Call get_peer_info with node_ip on the peer
    print(f"[PEER] Checking node IP {node_ip}...", file=sys.stderr)
    node_check = Node(port=peer_node.port, token=peer_node.token, ip=node_ip)
    node_status, node_response = get_peer_info_v3(node_check)
    
    if not node_status.found:
        exit_with_error(f"[PEER] Node {node_ip} not found in peer info")
    
    if node_status.primary_ip != node_ip:
        exit_with_error(f"[PEER] Node IP {node_ip} is not a primaryIp (found: {node_status.primary_ip})")
    
    print(f"✓ [PEER] Node {node_ip} verified as primaryIp", file=sys.stderr)
    
    # Call get_peer_info with hsa_ip on the peer
    print(f"[PEER] Checking HSA IP {hsa_ip}...", file=sys.stderr)
    hsa_check = Node(port=peer_node.port, token=peer_node.token, ip=hsa_ip)
    hsa_status, hsa_response = get_peer_info_v3(hsa_check)
    
    if hsa_status.found:
        exit_with_error(f"[PEER] HSA {hsa_ip} should not be found in peer info (but was found)")
    
    print(f"✓ [PEER] HSA {hsa_ip} verified as not found", file=sys.stderr)
    
    # Verify secondaryIp is empty on the node
    if node_status.secondary_ip != "":
        exit_with_error(f"[PEER] secondaryIp should be empty (found: {node_status.secondary_ip})")
    
    print(f"✓ [PEER] secondaryIp verified as empty", file=sys.stderr)
    
    # Verify activeAppliance is PRIMARY (1)
    if node_status.active_appliance != 1:
        exit_with_error(f"[PEER] activeAppliance should be PRIMARY (1) (found: {node_status.active_appliance})")
    
    print(f"✓ [PEER] activeAppliance verified as PRIMARY", file=sys.stderr)
    print(f"✓ [PEER] Peer information verification complete", file=sys.stderr)


def verify_peer_on_hsa(hsa_node: Node, node_ip: str, hsa_ip: str):
    """
    Verify peer information on the HSA node.
    
    Expected state on HSA:
    - node_ip should not be found
    - hsa_ip should not be found
    - primaryIp should be "127.0.0.1"
    - secondaryIp should be empty
    - activeAppliance should be PRIMARY
    
    Args:
        hsa_node: HSA Node object to query
        node_ip: Node IP address (should not be found)
        hsa_ip: HSA IP address (should not be found)
    """
    print(f"\n[HSA] Verifying peer information...", file=sys.stderr)
    
    # Call get_peer_info with node_ip on the HSA
    print(f"[HSA] Checking node IP {node_ip}...", file=sys.stderr)
    node_check = Node(port=hsa_node.port, token=hsa_node.token, ip=node_ip)
    node_status, node_response = get_peer_info_v3(node_check)
    
    if node_status.found:
        exit_with_error(f"[HSA] Node {node_ip} should not be found in peer info (but was found)")
    
    print(f"✓ [HSA] Node {node_ip} verified as not found", file=sys.stderr)
    
    # Call get_peer_info with hsa_ip on the HSA
    print(f"[HSA] Checking HSA IP {hsa_ip}...", file=sys.stderr)
    hsa_check = Node(port=hsa_node.port, token=hsa_node.token, ip=hsa_ip)
    hsa_status, hsa_response = get_peer_info_v3(hsa_check)
    
    if hsa_status.found:
        exit_with_error(f"[HSA] HSA {hsa_ip} should not be found in peer info (but was found)")
    
    print(f"✓ [HSA] HSA {hsa_ip} verified as not found", file=sys.stderr)
    
    # Now we need to check the actual peer entry on the HSA (should be 127.0.0.1)
    # Query with 127.0.0.1 to get the HSA's own peer info
    print(f"[HSA] Checking HSA's own peer info (127.0.0.1)...", file=sys.stderr)
    localhost_check = Node(port=hsa_node.port, token=hsa_node.token, ip="127.0.0.1")
    localhost_status, localhost_response = get_peer_info_v3(localhost_check)
    
    if not localhost_status.found:
        exit_with_error(f"[HSA] HSA's own peer info (127.0.0.1) not found")
    
    # Verify primaryIp is "127.0.0.1"
    if localhost_status.primary_ip != "127.0.0.1":
        exit_with_error(f"[HSA] primaryIp should be 127.0.0.1 (found: {localhost_status.primary_ip})")
    
    print(f"✓ [HSA] primaryIp verified as 127.0.0.1", file=sys.stderr)
    
    # Verify secondaryIp is empty
    if localhost_status.secondary_ip != "":
        exit_with_error(f"[HSA] secondaryIp should be empty (found: {localhost_status.secondary_ip})")
    
    print(f"✓ [HSA] secondaryIp verified as empty", file=sys.stderr)
    
    # Verify activeAppliance is PRIMARY (1)
    if localhost_status.active_appliance != 1:
        exit_with_error(f"[HSA] activeAppliance should be PRIMARY (1) (found: {localhost_status.active_appliance})")
    
    print(f"✓ [HSA] activeAppliance verified as PRIMARY", file=sys.stderr)
    print(f"✓ [HSA] Peer information verification complete", file=sys.stderr)


def verify_peer_after_join(peer_node: Node, node_ip: str, hsa_ip: str, node_name: str):
    """
    Verify peer information after HSA has joined the cluster.
    
    Expected state (both on peer and HSA):
    - node_ip should be found and be a primaryIp
    - hsa_ip should be found and be a secondaryIp
    - activeAppliance should be PRIMARY
    
    Args:
        peer_node: Node object to query
        node_ip: Expected primary IP address
        hsa_ip: Expected secondary IP address
        node_name: Name of the node being verified (for logging)
        
    Returns:
        True if verification succeeds, False otherwise
    """
    print(f"\n[{node_name}] Verifying peer information after join...", file=sys.stderr)
    
    # Call get_peer_info with node_ip
    print(f"[{node_name}] Checking node IP {node_ip}...", file=sys.stderr)
    node_check = Node(port=peer_node.port, token=peer_node.token, ip=node_ip)
    node_status, node_response = get_peer_info_v3(node_check)
    
    if not node_status.found:
        print(f"✗ [{node_name}] Node {node_ip} not found in peer info", file=sys.stderr)
        return False
    
    if node_status.primary_ip != node_ip:
        print(f"✗ [{node_name}] Node IP {node_ip} is not a primaryIp (found: {node_status.primary_ip})", file=sys.stderr)
        return False
    
    print(f"✓ [{node_name}] Node {node_ip} verified as primaryIp", file=sys.stderr)
    
    # Call get_peer_info with hsa_ip
    print(f"[{node_name}] Checking HSA IP {hsa_ip}...", file=sys.stderr)
    hsa_check = Node(port=peer_node.port, token=peer_node.token, ip=hsa_ip)
    hsa_status, hsa_response = get_peer_info_v3(hsa_check)
    
    if not hsa_status.found:
        print(f"✗ [{node_name}] HSA {hsa_ip} not found in peer info", file=sys.stderr)
        return False
    
    if hsa_status.secondary_ip != hsa_ip:
        print(f"✗ [{node_name}] HSA IP {hsa_ip} is not a secondaryIp (found: {hsa_status.secondary_ip})", file=sys.stderr)
        return False
    
    print(f"✓ [{node_name}] HSA {hsa_ip} verified as secondaryIp", file=sys.stderr)
    
    # Verify activeAppliance is PRIMARY (1)
    if hsa_status.active_appliance != 1:
        print(f"✗ [{node_name}] activeAppliance is not PRIMARY (found: {hsa_status.active_appliance})", file=sys.stderr)
        return False
    
    print(f"✓ [{node_name}] activeAppliance verified as PRIMARY", file=sys.stderr)
    print(f"✓ [{node_name}] Peer information verification complete", file=sys.stderr)
    return True


def main():
    """Main entry point for the repave workflow script."""
    print("[DEBUG] Starting repave.py script", file=sys.stderr)
    
    parser = argparse.ArgumentParser(
        description="Repave workflow for verifying peer and HSA configuration"
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
        "--token_hsa",
        required=True,
        help="Bearer token for HSA authentication"
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
    print(f"[DEBUG]   Peer Token: {args.token_peer[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   Peer IP: {args.ip_peer}", file=sys.stderr)
    print(f"[DEBUG]   Peer Port: {args.port_peer}", file=sys.stderr)
    print(f"[DEBUG]   HSA Token: {args.token_hsa[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   HSA IP: {args.ip_hsa}", file=sys.stderr)
    print(f"[DEBUG]   HSA Port: {args.port_hsa}", file=sys.stderr)

    # Step 0: Verify parameters
    print("\n[STEP 0] Verifying parameters...", file=sys.stderr)

    # Validate IP addresses
    if not validate_ip_address(args.ip_peer):
        exit_with_error(f"Invalid peer IP address: {args.ip_peer}")
    
    if not validate_ip_address(args.ip_hsa):
        exit_with_error(f"Invalid HSA IP address: {args.ip_hsa}")
    
    # Verify IPs are distinct
    if args.ip_peer == args.ip_hsa:
        exit_with_error(f"Peer and HSA IP addresses must be distinct: {args.ip_peer}")
    
    print(f"✓ IP addresses validated and are distinct", file=sys.stderr)
    
    # Validate port numbers
    if not validate_port(args.port_peer):
        exit_with_error(f"Invalid peer port number: {args.port_peer} (must be 0-65535)")
    
    if not validate_port(args.port_hsa):
        exit_with_error(f"Invalid HSA port number: {args.port_hsa} (must be 0-65535)")
    
    # Verify ports are distinct
    if args.port_peer == args.port_hsa:
        exit_with_error(f"Peer and HSA port numbers must be distinct: {args.port_peer}")
    
    print(f"✓ Port numbers validated and are distinct", file=sys.stderr)
    
    # Validate token lengths (361 characters)
    if not validate_token_length(args.token_peer, 361):
        exit_with_error(f"Invalid peer token length: {len(args.token_peer)} (expected 361)")
    
    if not validate_token_length(args.token_hsa, 361):
        exit_with_error(f"Invalid HSA token length: {len(args.token_hsa)} (expected 361)")
    
    print(f"✓ Token lengths validated (361 characters)", file=sys.stderr)
    
    # Verify tokens are distinct
    if args.token_peer == args.token_hsa:
        exit_with_error(f"Peer and HSA tokens must be distinct")
    
    print(f"✓ Tokens are distinct", file=sys.stderr)
    print("✓ All parameter validations passed", file=sys.stderr)
    
    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("Repave Workflow", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})", file=sys.stderr)
    print(f"HSA Node: https://localhost:{hsa_node.port} (forwarded to {hsa_node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # # Step 1: Verify peer information on the peer
    # print("\n[STEP 1] Verifying peer information on peer...", file=sys.stderr)
    # verify_peer_on_peer(peer_node, args.ip_peer, args.ip_hsa)
    # print("✓ Step 1 completed successfully", file=sys.stderr)
    
    # # Step 2: Verify peer information on the HSA
    # print("\n[STEP 2] Verifying peer information on HSA...", file=sys.stderr)
    # verify_peer_on_hsa(hsa_node, args.ip_peer, args.ip_hsa)
    # print("✓ Step 2 completed successfully", file=sys.stderr)
    
    # # Step 3: Get integration token from the peer
    # print("\n[STEP 3] Getting integration token from peer...", file=sys.stderr)
    # integration_token: str = ""
    # try:
    #     integration_token = get_integration_token(peer_node)
    #     print(f"✓ Integration token obtained (length: {len(integration_token)})", file=sys.stderr)
    #     print("✓ Step 3 completed successfully", file=sys.stderr)
    # except SystemExit:
    #     exit_with_error("Failed to get integration token from peer")
    # except Exception as e:
    #     # Check if the response contains HTTP 400 error
    #     if hasattr(e, 'args') and len(e.args) > 0:
    #         error_msg = str(e.args[0])
    #         if '400' in error_msg or 'HTTP' in error_msg:
    #             exit_with_error(f"get_integration_token returned 400 error: {error_msg}")
    #     exit_with_error(f"get_integration_token failed: {str(e)}")
    
    # # Step 4: Call become_hsa on the HSA
    # print("\n[STEP 4] Calling become_hsa on HSA...", file=sys.stderr)
    # try:
    #     response = become_hsa(hsa_node, args.ip_peer, integration_token)
        
    #     # Check for HTTP status code 200
    #     http_status = response.get('_http_status_code', 200)  # Default to 200 if not present
    #     if http_status == 400:
    #         exit_with_error(f"become_hsa returned HTTP 400: {response}")
        
    #     if http_status != 200:
    #         exit_with_error(f"become_hsa returned unexpected HTTP status {http_status}: {response}")
        
    #     # Check for success message
    #     status_msg = response.get('status', '')
    #     if "HSA add successfully initiated" not in status_msg:
    #         exit_with_error(f"become_hsa did not return expected success message. Got: {status_msg}")
        
    #     print(f"✓ become_hsa completed successfully: {status_msg}", file=sys.stderr)
    #     print("✓ Step 4 completed successfully", file=sys.stderr)
    # except SystemExit:
    #     raise  # Re-raise SystemExit to preserve exit_with_error behavior
    # except Exception as e:
    #     exit_with_error(f"become_hsa failed: {str(e)}")
    
    # # Step 5: Verify peer information after join (with retry loop)
    # print("\n[STEP 5] Verifying peer information after join...", file=sys.stderr)
    # max_retries = 10  # Maximum number of retries
    # retry_count = 0
    
    # while retry_count < max_retries:
    #     if retry_count > 0:
    #         print(f"\n[STEP 5] Retry attempt {retry_count}/{max_retries}...", file=sys.stderr)
        
    #     # Verify on peer
    #     peer_verified = verify_peer_after_join(peer_node, args.ip_peer, args.ip_hsa, "PEER")
        
    #     # Verify on HSA
    #     hsa_verified = verify_peer_after_join(hsa_node, args.ip_peer, args.ip_hsa, "HSA")
        
    #     # Check if both verifications succeeded
    #     if peer_verified and hsa_verified:
    #         print("\n✓ Step 5 completed successfully - peer information verified on both nodes", file=sys.stderr)
    #         break
        
    #     # If not successful, wait and retry
    #     retry_count += 1
    #     if retry_count < max_retries:
    #         print(f"\n⚠ Verification incomplete, waiting 30 seconds before retry...", file=sys.stderr)
    #         time.sleep(30)
    #     else:
    #         exit_with_error("Step 5 failed: Peer information verification did not succeed after maximum retries")
    
    # # Step 6: Call fail_over() on the peer
    # print("\n[STEP 6] Calling fail_over on peer...", file=sys.stderr)
    # fail_over_response = fail_over(peer_node)
    
    # if fail_over_response.code == 400:
    #     exit_with_error(f"fail_over returned 400: {fail_over_response.message}")
    
    # if "LeaderFollower Job Active, cannot Fail-Over" in fail_over_response.message:
    #     exit_with_error(f"fail_over error: {fail_over_response.message}")
    
    # if "Failover successfully started" not in fail_over_response.message:
    #     exit_with_error(f"Unexpected fail_over response: {fail_over_response.message}")
    
    # print("✓ fail_over completed successfully", file=sys.stderr)
    # print("✓ Step 6 completed successfully", file=sys.stderr)
    
    # Step 7: Get peer info to obtain peer ID
    print("\n[STEP 7] Getting peer info to obtain peer ID...", file=sys.stderr)
    peer_status = get_peer_info(peer_node)
    
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
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Repave workflow completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob