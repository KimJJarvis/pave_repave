#!/usr/bin/env python3
"""
State machine-based script to replace a node in a cluster.
Uses get_state.py to determine current state and performs appropriate actions.
"""

import argparse
import sys
import json
import time
import subprocess
from pathlib import Path

from node import Node
from get_integration_token import get_integration_token
from fail_over import fail_over
from switch_primary_secondary import switch_primary_secondary
from leave_cluster_hsa import leave_cluster_hsa
from become_hsa import become_hsa


def validate_ip_address(ip: str) -> bool:
    """
    Validate that the IP address is a string with dots (e.g., "9.24.143.26").

    Args:
        ip: IP address string to validate

    Returns:
        True if valid, False otherwise
    """
    import re
    # Check if it's a string with dots and valid IP format
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, ip):
        return False

    # Validate each octet is 0-255
    octets = ip.split(".")
    for octet in octets:
        if int(octet) > 255:
            return False

    return True


def validate_port(port: int) -> bool:
    """
    Validate that the port is a valid integer in the range 0-65535.

    Args:
        port: Port number to validate

    Returns:
        True if valid, False otherwise
    """
    return 0 <= port <= 65535


def validate_bearer_token(token: str) -> bool:
    """
    Validate that the bearer token is a string with length of 361 characters.

    Args:
        token: Bearer token to validate

    Returns:
        True if valid, False otherwise
    """
    return len(token) == 361


def validate_integration_token(token: str) -> bool:
    """
    Validate that the integration token is a string with length of 273 characters.

    Args:
        token: Integration token to validate

    Returns:
        True if valid, False otherwise
    """
    return len(token) == 273


def get_current_state(peer: Node, hsa: Node, spare: Node) -> dict:
    """
    Get the current cluster state by calling get_state.py.
    
    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node
        
    Returns:
        Dictionary with 'state' and 'id' keys
    """
    print("\n[STATE CHECK] Getting current cluster state...", file=sys.stderr)
    
    # Build the command to call get_state.py
    script_dir = Path(__file__).parent
    get_state_script = script_dir / "get_state.py"
    
    cmd = [
        sys.executable,
        str(get_state_script),
        "--ip_peer", peer.ip,
        "--token_peer", peer.token,
        "--port_peer", str(peer.port),
        "--ip_hsa", hsa.ip,
        "--token_hsa", hsa.token,
        "--port_hsa", str(hsa.port),
        "--ip_spare", spare.ip,
        "--token_spare", spare.token,
        "--port_spare", str(spare.port)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON output
        state_info = json.loads(result.stdout.strip())
        print(f"[STATE CHECK] Current state: {state_info['state']}, ID: {state_info['id']}", file=sys.stderr)
        return state_info
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to get state: {e}", file=sys.stderr)
        print(f"[ERROR] stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse state output: {e}", file=sys.stderr)
        sys.exit(1)


def wait_for_state(peer: Node, hsa: Node, spare: Node, expected_state: int, current_state: int, max_retries: int = 10, wait_seconds: int = 30) -> bool:
    """
    Wait for the cluster to reach the expected state.
    
    Args:
        peer: Peer node
        hsa: HSA node
        spare: Spare node
        expected_state: The state we're waiting for
        current_state: The current state before waiting
        max_retries: Maximum number of retries (default: 10)
        wait_seconds: Seconds to wait between checks (default: 30)
        
    Returns:
        True if expected state reached, False otherwise
    """
    for attempt in range(1, max_retries + 1):
        print(f"\n[WAIT] Waiting {wait_seconds} seconds for state transition (attempt {attempt}/{max_retries})...", file=sys.stderr)
        time.sleep(wait_seconds)
        
        state_info = get_current_state(peer, hsa, spare)
        new_state = state_info['state']
        
        if new_state == expected_state:
            print(f"✓ State transitioned to {expected_state}", file=sys.stderr)
            return True
        elif new_state == current_state:
            print(f"[INFO] State still {current_state}, will retry...", file=sys.stderr)
            continue
        else:
            print(f"[ERROR] Unexpected state {new_state}, expected {expected_state}", file=sys.stderr)
            return False
    
    print(f"[ERROR] Failed to reach state {expected_state} after {max_retries} attempts", file=sys.stderr)
    return False


def execute_state_transition(state: int, peer: Node, hsa: Node, spare: Node, peer_id: int) -> int:
    """
    Execute the action for the current state and return the expected next state.
    
    Args:
        state: Current state
        peer: Peer node
        hsa: HSA node
        spare: Spare node
        peer_id: Peer ID
        
    Returns:
        Expected next state (0 means stop)
    """
    print(f"\n{'=' * 80}", file=sys.stderr)
    print(f"STATE {state} - Executing transition", file=sys.stderr)
    print(f"{'=' * 80}", file=sys.stderr)
    
    if state == 1:
        # State 1 -> 2: Step 6 fail over
        print("\n[Action] Step 6: Fail over peer...", file=sys.stderr)
        response = fail_over(node=peer)
        if response.code != 200:
            print(f"[ERROR] Fail over failed: {response.message} (code: {response.code})", file=sys.stderr)
            return 0  # Stop on error
        print(f"✓ Fail over initiated: {response.message}", file=sys.stderr)
        return 2
        
    elif state == 2:
        # State 2 -> 3: Step 7 switch primary secondary
        print("\n[Action] Step 7: Switch primary/secondary on Peer...", file=sys.stderr)
        response = switch_primary_secondary(node=peer, id=peer_id)
        if response.code not in [200]:
            print(f"[ERROR] Switch primary/secondary failed: {response.message} (code: {response.code})", file=sys.stderr)
            return 0  # Stop on error
        print(f"✓ Switch primary/secondary completed: {response.message}", file=sys.stderr)
        return 3
        
    elif state == 3:
        # State 3 -> 4: Step 8 then 9 get integration token then leave hsa
        print("\n[Action] Step 8: Get integration token from HSA...", file=sys.stderr)
        integration_token = get_integration_token(node=hsa)
        if not validate_integration_token(integration_token):
            print(
                f"[WARNING] Integration token length is {len(integration_token)}, expected 273",
                file=sys.stderr,
            )
        print(
            f"✓ Integration token retrieved (length: {len(integration_token)})",
            file=sys.stderr,
        )
        
        print("\n[Action] Step 9: Leave cluster HSA (peer)...", file=sys.stderr)
        leave_cluster_hsa(node=peer, integration_token=integration_token)
        print("✓ Peer left cluster", file=sys.stderr)
        return 4
        
    elif state == 4:
        # State 4 -> 5: Step 10 then 11 get integration token then become hsa
        print("\n[Action] Step 10: Get integration token from HSA (again)...", file=sys.stderr)
        integration_token = get_integration_token(node=hsa)
        if not validate_integration_token(integration_token):
            print(
                f"[WARNING] Integration token length is {len(integration_token)}, expected 273",
                file=sys.stderr,
            )
        print(
            f"✓ Integration token retrieved (length: {len(integration_token)})",
            file=sys.stderr,
        )
        
        print("\n[Action] Step 11: Become HSA (spare)...", file=sys.stderr)
        become_hsa(node=spare, ip_cluster=hsa.ip, integration_token=integration_token)
        print("✓ Spare became HSA", file=sys.stderr)
        return 5
        
    elif state == 5:
        # State 5 -> 6: Step 12 fail over
        print("\n[Action] Step 12: Fail over HSA...", file=sys.stderr)
        response = fail_over(node=hsa)
        if response.code != 200:
            print(f"[ERROR] HSA fail over failed: {response.message} (code: {response.code})", file=sys.stderr)
            return 0  # Stop on error
        print(f"✓ HSA fail over initiated: {response.message}", file=sys.stderr)
        return 6
        
    elif state == 6:
        # State 6 -> 7: Step 13 switch primary secondary
        print("\n[Action] Step 13: Switch primary/secondary on spare...", file=sys.stderr)
        response = switch_primary_secondary(node=spare, id=peer_id)
        if response.code not in [200]:
            print(f"[ERROR] Switch primary/secondary failed: {response.message} (code: {response.code})", file=sys.stderr)
            return 0  # Stop on error
        print(f"✓ Switch primary/secondary on spare completed: {response.message}", file=sys.stderr)
        return 7
        
    elif state == 7:
        # State 7 -> stop
        print("\n[Action] State 7 reached - workflow complete!", file=sys.stderr)
        return 0
        
    elif state == 8:
        # State 8 -> 9: Step 20 and 21
        print("\n[Action] Step 20: Get integration token from Peer...", file=sys.stderr)
        integration_token = get_integration_token(node=peer)
        if not validate_integration_token(integration_token):
            print(
                f"[WARNING] Integration token length is {len(integration_token)}, expected 273",
                file=sys.stderr,
            )
        print(
            f"✓ Integration token retrieved (length: {len(integration_token)})",
            file=sys.stderr,
        )
        
        print("\n[Action] Step 21: Become HSA (hsa)...", file=sys.stderr)
        become_hsa(node=hsa, ip_cluster=peer.ip, integration_token=integration_token)
        print("✓ HSA became HSA", file=sys.stderr)
        return 9
        
    elif state == 9:
        # State 9 -> stop
        print("\n[Action] State 9 reached - workflow complete!", file=sys.stderr)
        return 0
        
    elif state == 0:
        # State 0 -> stop
        print("\n[ERROR] State 0 (unknown/invalid state) - cannot proceed", file=sys.stderr)
        return 0
        
    else:
        print(f"\n[ERROR] Unknown state {state}", file=sys.stderr)
        return 0


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting replace-node-sm.py (state machine) script", file=sys.stderr)

    parser = argparse.ArgumentParser(
        description="Replace a peer node with a spare node in a cluster (state machine version)"
    )

    # Peer node arguments
    parser.add_argument(
        "--ip_peer",
        required=True,
        help="Peer IP address (dot format, e.g., 9.24.143.26)",
    )
    parser.add_argument(
        "--token_peer", required=True, help="Peer bearer token (362 characters)"
    )
    parser.add_argument(
        "--port_peer", required=True, type=int, help="Peer localhost port (0-65535)"
    )

    # HSA node arguments
    parser.add_argument(
        "--ip_hsa", required=True, help="HSA IP address (dot format, e.g., 9.24.143.26)"
    )
    parser.add_argument(
        "--token_hsa", required=True, help="HSA bearer token (362 characters)"
    )
    parser.add_argument(
        "--port_hsa", required=True, type=int, help="HSA localhost port (0-65535)"
    )

    # Spare node arguments
    parser.add_argument(
        "--ip_spare",
        required=True,
        help="Spare IP address (dot format, e.g., 9.24.143.26)",
    )
    parser.add_argument(
        "--token_spare", required=True, help="Spare bearer token (362 characters)"
    )
    parser.add_argument(
        "--port_spare", required=True, type=int, help="Spare localhost port (0-65535)"
    )

    args = parser.parse_args()

    # Validate IP addresses
    print("\n[Validation] Validating IP addresses...", file=sys.stderr)
    if not validate_ip_address(args.ip_peer):
        print(f"[ERROR] Invalid peer IP address: {args.ip_peer}", file=sys.stderr)
        sys.exit(1)
    if not validate_ip_address(args.ip_hsa):
        print(f"[ERROR] Invalid HSA IP address: {args.ip_hsa}", file=sys.stderr)
        sys.exit(1)
    if not validate_ip_address(args.ip_spare):
        print(f"[ERROR] Invalid spare IP address: {args.ip_spare}", file=sys.stderr)
        sys.exit(1)
    print("✓ All IP addresses are valid", file=sys.stderr)

    # Validate ports
    print("\n[Validation] Validating ports...", file=sys.stderr)
    if not validate_port(args.port_peer):
        print(f"[ERROR] Invalid peer port: {args.port_peer}", file=sys.stderr)
        sys.exit(1)
    if not validate_port(args.port_hsa):
        print(f"[ERROR] Invalid HSA port: {args.port_hsa}", file=sys.stderr)
        sys.exit(1)
    if not validate_port(args.port_spare):
        print(f"[ERROR] Invalid spare port: {args.port_spare}", file=sys.stderr)
        sys.exit(1)
    print("✓ All ports are valid", file=sys.stderr)

    # Validate bearer tokens
    print("\n[Validation] Validating bearer tokens...", file=sys.stderr)
    if not validate_bearer_token(args.token_peer):
        print(
            f"[ERROR] Invalid peer bearer token length: {len(args.token_peer)} (expected 362)",
            file=sys.stderr,
        )
        sys.exit(1)
    if not validate_bearer_token(args.token_hsa):
        print(
            f"[ERROR] Invalid HSA bearer token length: {len(args.token_hsa)} (expected 362)",
            file=sys.stderr,
        )
        sys.exit(1)
    if not validate_bearer_token(args.token_spare):
        print(
            f"[ERROR] Invalid spare bearer token length: {len(args.token_spare)} (expected 362)",
            file=sys.stderr,
        )
        sys.exit(1)
    print("✓ All bearer tokens are valid", file=sys.stderr)

    # Create Node objects
    peer = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)
    spare = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)

    print("\n" + "=" * 80, file=sys.stderr)
    print("REPLACE NODE WORKFLOW (STATE MACHINE)", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"Peer:  {peer.ip}:{peer.port}", file=sys.stderr)
    print(f"HSA:   {hsa.ip}:{hsa.port}", file=sys.stderr)
    print(f"Spare: {spare.ip}:{spare.port}", file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    # Get initial state
    state_info = get_current_state(peer, hsa, spare)
    current_state = state_info['state']
    peer_id = state_info['id']
    
    print(f"\n[INFO] Initial state: {current_state}, Peer ID: {peer_id}", file=sys.stderr)
    
    if current_state == 0:
        print("[ERROR] Initial state is 0 (invalid/unknown) - cannot proceed", file=sys.stderr)
        sys.exit(1)
    
    if current_state == 7 or current_state == 9:
        print(f"[INFO] Already in final state {current_state} - nothing to do", file=sys.stderr)
        print("\n" + "=" * 80, file=sys.stderr)
        print("✓ WORKFLOW ALREADY COMPLETE!", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        return
    
    # State machine loop
    while current_state not in [0, 7, 9]:
        # Execute the transition for current state
        expected_state = execute_state_transition(current_state, peer, hsa, spare, peer_id)
        
        if expected_state == 0:
            # Stop state reached or error
            break
        
        # Wait for the state to transition
        if not wait_for_state(peer, hsa, spare, expected_state, current_state):
            print(f"[ERROR] Failed to transition from state {current_state} to {expected_state}", file=sys.stderr)
            sys.exit(1)
        
        # Update current state
        state_info = get_current_state(peer, hsa, spare)
        current_state = state_info['state']
        
        if current_state != expected_state:
            print(f"[ERROR] State mismatch: expected {expected_state}, got {current_state}", file=sys.stderr)
            sys.exit(1)
    
    # Final state check
    if current_state == 7 or current_state == 9:
        print("\n" + "=" * 80, file=sys.stderr)
        print("✓ ALL STEPS COMPLETED SUCCESSFULLY!", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print(f"\nNode replacement complete (final state: {current_state}):", file=sys.stderr)
        if current_state == 7:
            print(f"  - Peer ({peer.ip}) has been removed from the cluster", file=sys.stderr)
            print(f"  - Spare ({spare.ip}) has replaced the peer in the cluster", file=sys.stderr)
            print(f"  - HSA ({hsa.ip}) remains in the cluster", file=sys.stderr)
        else:  # state 9
            print(f"  - Cluster recovered to operational state", file=sys.stderr)
    else:
        print(f"\n[ERROR] Workflow ended in unexpected state {current_state}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob