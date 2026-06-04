#!/usr/bin/env python3
"""
Script to query peer information, get tokens, or perform fail-over from NMS API.
Supports multiple commands: peer_info, get_integration_token, and fail_over.
"""

import argparse
import logging
import os
import sys

from cluster_client.add_hsa import add_hsa
from cluster_client.add_peer import add_peer
from cluster_client.config import config
from cluster_client.config_info import show_default_config
from cluster_client.double_state import (
    double_state_table,
    get_double_state,
    postcondition_double,
)
from cluster_client.fail_over import fail_over
from cluster_client.get_authentication_token import get_authentication_token
from cluster_client.get_integration_token import get_integration_token
from cluster_client.node import Node
from cluster_client.paverepave import repave, repaveswitch, switch
from cluster_client.remove_hsa import remove_hsa
from cluster_client.remove_peer import remove_peer
from cluster_client.single_state import (
    get_single_state,
    postcondition_single,
    precondition_single,
    single_state_table,
)
from cluster_client.switch_primary_secondary import switch_primary_secondary
from cluster_client.triple_state import get_triple_state, triple_state_table
from cluster_client.utilities import (
    setup_logging,
    validate_unique_ips,
    validate_unique_ports,
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the script."""
    # Create parent parser with common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--log-level",
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parent_parser.add_argument(
        "--log-file", type=str, default=None, help="Log to file instead of console"
    )
    parent_parser.add_argument(
        "--username",
        required=False,
        help="Username for authentication (defaults to CLUSTER_CLIENT_USERNAME env var)",
    )
    parent_parser.add_argument(
        "--password",
        required=False,
        help="Password for authentication (defaults to CLUSTER_CLIENT_PASSWORD env var)",
    )
    parent_parser.add_argument(
        "--host", type=str, default=None, help="Override config.host"
    )
    parent_parser.add_argument(
        "--http_502_max_retries",
        type=int,
        default=None,
        help="Override config.http_502_max_retries",
    )
    parent_parser.add_argument(
        "--http_502_retry_delay",
        type=int,
        default=None,
        help="Override config.http_502_retry_delay",
    )
    parent_parser.add_argument(
        "--http_timeout_value",
        type=int,
        default=None,
        help="Override config.http_timeout_value",
    )
    parent_parser.add_argument(
        "--wait_state_max_retries",
        type=int,
        default=None,
        help="Override config.wait_state_max_retries",
    )
    parent_parser.add_argument(
        "--wait_state_initial_delay",
        type=int,
        default=None,
        help="Override config.wait_state_initial_delay",
    )
    parent_parser.add_argument(
        "--wait_state_retry_delay",
        type=int,
        default=None,
        help="Override config.wait_state_retry_delay",
    )
    parent_parser.add_argument(
        "--wait_state_settle_delay",
        type=int,
        default=None,
        help="Override config.wait_state_settle_delay",
    )
    parent_parser.add_argument(
        "--switch_primary_secondary_max_retries",
        type=int,
        default=None,
        help="Override config.switch_primary_secondary_max_retries",
    )
    parent_parser.add_argument(
        "--switch_primary_secondary_retry_delay",
        type=int,
        default=None,
        help="Override config.switch_primary_secondary_retry_delay",
    )
    parent_parser.add_argument(
        "--fail_over_max_retries",
        type=int,
        default=None,
        help="Override config.fail_over_max_retries",
    )
    parent_parser.add_argument(
        "--fail_over_retry_delay",
        type=int,
        default=None,
        help="Override config.fail_over_retry_delay",
    )
    parent_parser.add_argument(
        "--port_forward",
        action="store_true",
        help="Enable port forwarding (sets config.port_forward to True)",
    )

    # Create main parser
    parser = argparse.ArgumentParser(
        description="Query peer information, get tokens, or perform fail-over from NMS API."
    )

    # Create subparsers for each command
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Command to execute"
    )

    # peer_info subcommand
    # get_integration_token subcommand
    get_integration_token_parser = subparsers.add_parser(
        "get_integration_token",
        parents=[parent_parser],
        help="Retrieve integration token",
    )
    get_integration_token_parser.add_argument(
        "--ip", required=True, help="IP address of the node (in dot format)"
    )
    get_integration_token_parser.add_argument(
        "--port", type=int, required=True, help="Port number of the node"
    )

    # fail_over subcommand
    fail_over_parser = subparsers.add_parser(
        "fail_over", parents=[parent_parser], help="Perform fail-over operation"
    )
    fail_over_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer (dot format)"
    )
    fail_over_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number of the peer"
    )

    # switch_primary_secondary subcommand
    switch_primary_secondary_parser = subparsers.add_parser(
        "switch_primary_secondary",
        parents=[parent_parser],
        help="Switch primary and secondary appliance roles on a peer",
    )
    switch_primary_secondary_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer (dot format)"
    )
    switch_primary_secondary_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number of the peer"
    )
    switch_primary_secondary_parser.add_argument(
        "--id", type=int, required=True, help="ID of the peer in the peers table"
    )

    # become_hsa subcommand
    # add_peer subcommand
    add_peer_parser = subparsers.add_parser(
        "add_peer",
        parents=[parent_parser],
        help="Add a spare node to an existing cluster",
    )
    add_peer_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)",
    )
    add_peer_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node",
    )
    add_peer_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node to add to the cluster (dot format)",
    )
    add_peer_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number of the spare node to add to the cluster",
    )
    add_peer_parser.add_argument(
        "--name", required=True, help="Name of the spare node to add to the cluster"
    )

    # remove_peer subcommand
    remove_peer_parser = subparsers.add_parser(
        "remove_peer",
        parents=[parent_parser],
        help="Remove a peer node from the cluster (automatically retrieves integration token)",
    )
    remove_peer_parser.add_argument(
        "--ip_cluster",
        required=True,
        help="IP address of the cluster node (dot format)",
    )
    remove_peer_parser.add_argument(
        "--port_cluster",
        type=int,
        required=True,
        help="Port number of the cluster node",
    )
    remove_peer_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node to remove from the cluster (dot format)",
    )
    remove_peer_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node to remove from the cluster",
    )

    # add_hsa subcommand
    add_hsa_parser = subparsers.add_parser(
        "add_hsa", parents=[parent_parser], help="Add an HSA to a cluster"
    )
    add_hsa_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer HSA node (dot format)"
    )
    add_hsa_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number of the peer HSA node"
    )
    add_hsa_parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node (dot format)"
    )
    add_hsa_parser.add_argument(
        "--port_spare", type=int, required=True, help="Port number of the spare node"
    )

    # remove_hsa subcommand
    remove_hsa_parser = subparsers.add_parser(
        "remove_hsa", parents=[parent_parser], help="Remove an HSA from a cluster"
    )
    remove_hsa_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    remove_hsa_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number of the peer node"
    )
    remove_hsa_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA to be removed (dot format)",
    )
    remove_hsa_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number of the HSA to be removed",
    )

    # state1 subcommand
    # single_state subcommand
    single_state_parser = subparsers.add_parser(
        "single_state",
        parents=[parent_parser],
        help="Determine the current state of a single node",
    )
    single_state_parser.add_argument(
        "--ip", required=True, help="IP address of the node (dot format)"
    )
    single_state_parser.add_argument(
        "--port", type=int, required=True, help="Port number for node"
    )

    # state2 subcommand
    # double_state subcommand
    double_state_parser = subparsers.add_parser(
        "double_state",
        parents=[parent_parser],
        help="Determine the current state of the peer/HSA cluster (double state)",
    )
    double_state_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    double_state_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number for peer node"
    )
    double_state_parser.add_argument(
        "--ip_hsa", required=True, help="IP address of the HSA node (dot format)"
    )
    double_state_parser.add_argument(
        "--port_hsa", type=int, required=True, help="Port number for HSA node"
    )

    # switch subcommand
    switch_parser = subparsers.add_parser(
        "switch", parents=[parent_parser], help="Switch primary and secondary roles"
    )
    switch_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    switch_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number for peer node"
    )
    switch_parser.add_argument(
        "--ip_hsa", required=True, help="IP address of the HSA node (dot format)"
    )
    switch_parser.add_argument(
        "--port_hsa", type=int, required=True, help="Port number for HSA node"
    )

    # state3 subcommand
    # triple_state subcommand
    triple_state_parser = subparsers.add_parser(
        "triple_state",
        parents=[parent_parser],
        help="Determine the current repave state of the peer/HSA cluster",
    )
    triple_state_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    triple_state_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number for peer node"
    )
    triple_state_parser.add_argument(
        "--ip_hsa", required=True, help="IP address of the HSA node (dot format)"
    )
    triple_state_parser.add_argument(
        "--port_hsa", type=int, required=True, help="Port number for HSA node"
    )
    triple_state_parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node"
    )
    triple_state_parser.add_argument(
        "--port_spare", type=int, required=True, help="Port number for spare node"
    )

    # repaveswitch subcommand
    repaveswitch_parser = subparsers.add_parser(
        "repaveswitch",
        parents=[parent_parser],
        help="Perform pave/repave operation on the cluster",
    )
    repaveswitch_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    repaveswitch_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number for peer node"
    )
    repaveswitch_parser.add_argument(
        "--ip_hsa", required=True, help="IP address of the HSA node (dot format)"
    )
    repaveswitch_parser.add_argument(
        "--port_hsa", type=int, required=True, help="Port number for HSA node"
    )
    repaveswitch_parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node"
    )
    repaveswitch_parser.add_argument(
        "--port_spare", type=int, required=True, help="Port number for spare node"
    )

    # repave subcommand
    repave_parser = subparsers.add_parser(
        "repave",
        parents=[parent_parser],
        help="Perform repave operation on the cluster",
    )
    repave_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    repave_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number for peer node"
    )
    repave_parser.add_argument(
        "--ip_hsa", required=True, help="IP address of the HSA node (dot format)"
    )
    repave_parser.add_argument(
        "--port_hsa", type=int, required=True, help="Port number for HSA node"
    )
    repave_parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node"
    )
    repave_parser.add_argument(
        "--port_spare", type=int, required=True, help="Port number for spare node"
    )

    # show_config subcommand
    show_config_parser = subparsers.add_parser(
        "show_config",
        help="Display default configuration values",
    )

    args = parser.parse_args()

    # Handle show_config command early (doesn't need authentication)
    if args.command == "show_config":
        config_table = show_default_config()
        print(config_table)
        return

    # Handle username and password from environment variables if not provided
    username = args.username
    password = args.password

    if username is None:
        username = os.environ.get("CLUSTER_CLIENT_USERNAME")
        if username is None:
            print(
                "✗ Error: --username not provided and CLUSTER_CLIENT_USERNAME environment variable not set",
                file=sys.stderr,
            )
            sys.exit(1)

    if password is None:
        password = os.environ.get("CLUSTER_CLIENT_PASSWORD")
        if password is None:
            print(
                "✗ Error: --password not provided and CLUSTER_CLIENT_PASSWORD environment variable not set",
                file=sys.stderr,
            )
            sys.exit(1)

    config_overrides = {
        "host": args.host,
        "http_502_max_retries": args.http_502_max_retries,
        "http_502_retry_delay": args.http_502_retry_delay,
        "http_timeout_value": args.http_timeout_value,
        "wait_state_max_retries": args.wait_state_max_retries,
        "wait_state_initial_delay": args.wait_state_initial_delay,
        "wait_state_retry_delay": args.wait_state_retry_delay,
        "wait_state_settle_delay": args.wait_state_settle_delay,
        "switch_primary_secondary_max_retries": args.switch_primary_secondary_max_retries,
        "switch_primary_secondary_retry_delay": args.switch_primary_secondary_retry_delay,
        "fail_over_max_retries": args.fail_over_max_retries,
        "fail_over_retry_delay": args.fail_over_retry_delay,
        "log_level": args.log_level,
        "log_file": args.log_file,
    }

    for config_key, config_value in config_overrides.items():
        if config_value is not None:
            setattr(config, config_key, config_value)

    # Handle port_forward separately since it's a boolean flag
    # Only override if the flag was explicitly provided (True)
    if args.port_forward:
        config.port_forward = True

    # ⚠️ Must be called before any other logging calls
    setup_logging(config.log_level, config.log_file)

    unique_ip_args = [
        ip
        for ip in (
            getattr(args, "ip_peer", None),
            getattr(args, "ip_spare", None),
            getattr(args, "ip_hsa", None),
            getattr(args, "ip_cluster", None),
        )
        if ip is not None
    ]
    validate_unique_ips(*unique_ip_args)

    if config.port_forward:
        unique_port_args = [
            port
            for port in (
                getattr(args, "port_peer", None),
                getattr(args, "port_spare", None),
                getattr(args, "port_hsa", None),
                getattr(args, "port_cluster", None),
            )
            if port is not None
        ]
        validate_unique_ports(*unique_port_args)

    try:
        if args.command == "get_integration_token":
            # Get authentication token
            token = get_authentication_token(
                username=username, password=password, ip=args.ip, port=args.port
            )

            # Create Node object with IP
            node = Node(port=args.port, token=token, ip=args.ip)

            # Get integration token
            integration_token = get_integration_token(node=node)

            # Output the integration token to stdout
            print(integration_token)

        elif args.command == "fail_over":
            # Get authentication token using port_peer
            token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )

            # Create Node object with peer IP and port
            node = Node(port=args.port_peer, token=token, ip=args.ip_peer)

            # Call fail-over
            fail_over(node=node)

            print("✓ Operation completed successfully!")

        elif args.command == "switch_primary_secondary":
            # Get authentication token
            token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )

            # Create Node object
            node = Node(port=args.port_peer, token=token, ip=args.ip_peer)

            # Call switch-primary-secondary
            switch_primary_secondary(node=node, id=args.id)

            print("✓ Operation completed successfully!")

        elif args.command == "add_peer":
            # Get authentication token for cluster node
            peer_token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )
            # Create cluster Node object
            peer = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            # Get authentication token for spare node
            spare_token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_spare,
                port=args.port_spare,
            )

            # Create spare Node object
            spare = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)

            # Add spare node as peer to the cluster
            precondition_single(state=1, peer=spare)
            add_peer(
                peer=peer,
                spare=spare,
                name=args.name,
            )
            spare.token = peer.token
            postcondition_single(state=2, peer=spare)

            print("✓ Operation completed successfully!")

        elif args.command == "remove_peer":
            # Get authentication token for cluster node
            cluster_token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_cluster,
                port=args.port_cluster,
            )

            # Create cluster Node object
            cluster_node = Node(
                port=args.port_cluster, token=cluster_token, ip=args.ip_cluster
            )

            # Get authentication token for peer node
            peer_token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )

            # Create peer Node object
            peer = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)

            precondition_single(state=2, peer=peer)
            remove_peer(
                cluster=cluster_node,
                peer=peer,
            )
            postcondition_single(state=1, peer=peer)

            print("✓ Operation completed successfully!")

        elif args.command == "add_hsa":
            # Get authentication token for peer node
            peer_token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )

            # Get authentication token for spare node
            spare_token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_spare,
                port=args.port_spare,
            )

            # Create Node objects
            peer = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            spare = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)

            peer_state = get_single_state(peer=peer)
            if peer_state not in [1, 2]:
                raise RuntimeError("Peer node already has a HSA)")
            precondition_single(state=1, peer=spare)
            add_hsa(peer=peer, spare=spare)
            postcondition_double(state=2, peer=peer, hsa=spare)

            print("✓ Operation completed successfully!")

        elif args.command == "remove_hsa":
            # Get authentication token for peer node
            peer_token = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )

            # Get authentication token for HSA node
            hsa_token = get_authentication_token(
                username=username, password=password, ip=args.ip_hsa, port=args.port_hsa
            )

            # Create Node objects
            peer = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=hsa_token, ip=args.ip_hsa)

            # Call remove_hsa
            postcondition_double(state=2, peer=peer, hsa=hsa)
            remove_hsa(peer=peer, hsa=hsa)
            postcondition_single(state=1, peer=hsa)
            postcondition_single(state=2, peer=peer)

            print("✓ Operation completed successfully!")

        elif args.command == "double_state":
            # Get authentication tokens for each node
            token_peer = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )
            token_hsa = get_authentication_token(
                username=username, password=password, ip=args.ip_hsa, port=args.port_hsa
            )

            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)

            # Determine the current state first
            current_state = get_double_state(peer=peer, hsa=hsa)

            # Print the state table
            print(double_state_table(peer=peer, hsa=hsa))
            print()

            # Print state to console (stdout)
            print(f"State: {current_state}")

        elif args.command == "single_state":
            token = get_authentication_token(
                username=username, password=password, ip=args.ip, port=args.port
            )
            node = Node(port=args.port, token=token, ip=args.ip)
            # Determine the current state first
            current_state = get_single_state(peer=node)

            # Print the state table with state information
            print(single_state_table(peer=node))
            print()

            # Print state to console (stdout)
            print(f"State: {current_state}")

        elif args.command == "triple_state":
            # Get authentication tokens for each node
            token_peer = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )
            token_hsa = get_authentication_token(
                username=username, password=password, ip=args.ip_hsa, port=args.port_hsa
            )
            token_spare = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_spare,
                port=args.port_spare,
            )

            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)

            # Determine the current state first
            current_state = get_triple_state(peer=peer, hsa=hsa, spare=spare)

            # Print the state table with state information
            print(triple_state_table(peer=peer, hsa=hsa, spare=spare))
            print()

            # Print state to console (stdout)
            print(f"State: {current_state}")

        elif args.command == "repaveswitch":
            # Get authentication tokens for each node
            token_peer = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )
            token_hsa = get_authentication_token(
                username=username, password=password, ip=args.ip_hsa, port=args.port_hsa
            )
            token_spare = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_spare,
                port=args.port_spare,
            )

            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)

            # Call paverepave
            repaveswitch(peer=peer, hsa=hsa, spare=spare)

            print("✓ SUCCESS: Pave/Swich completed successfully!")

        elif args.command == "repave":
            # Get authentication tokens for each node
            token_peer = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )
            token_hsa = get_authentication_token(
                username=username, password=password, ip=args.ip_hsa, port=args.port_hsa
            )
            token_spare = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_spare,
                port=args.port_spare,
            )

            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)

            # Call repave
            repave(peer=peer, hsa=hsa, spare=spare)

            print("✓ SUCCESS: Repave completed successfully!")

        elif args.command == "switch":
            # Get authentication tokens for each node
            token_peer = get_authentication_token(
                username=username,
                password=password,
                ip=args.ip_peer,
                port=args.port_peer,
            )
            token_hsa = get_authentication_token(
                username=username, password=password, ip=args.ip_hsa, port=args.port_hsa
            )

            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)

            # Call repave
            switch(peer=peer, hsa=hsa)

            print("✓ SUCCESS: Switch completed successfully!")

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"✗ Operation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Operation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Operation failed with unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
