import argparse
import json
import logging
import os
import sys

from cluster_client.become_hsa import become_hsa
from cluster_client.config import config
from cluster_client.config_info import show_default_config
from cluster_client.double_state import (
    double_state_table,
    get_double_state,
    postcondition_double,
)
from cluster_client.fail_over import fail_over
from cluster_client.get_integration_token import get_integration_token
from cluster_client.join_cluster import join_cluster
from cluster_client.leave_cluster import leave_cluster
from cluster_client.leave_cluster_hsa import leave_cluster_hsa
from cluster_client.node import Node
from cluster_client.paverepave import repave, repaveswitch
from cluster_client.peer_table import peer_table
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

    # peer_table subcommand
    peer_table_parser = subparsers.add_parser(
        "peer_table",
        parents=[parent_parser],
        help="Display peer information table",
    )
    peer_table_parser.add_argument(
        "--ip", required=True, help="IP address of the node (in dot format)"
    )
    peer_table_parser.add_argument(
        "--port", type=int, required=True, help="Port number of the node"
    )

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

    # join_cluster subcommand
    join_cluster_parser = subparsers.add_parser(
        "join_cluster",
        parents=[parent_parser],
        help="Add a spare node to an existing cluster",
    )
    join_cluster_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)",
    )
    join_cluster_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node",
    )
    join_cluster_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node to add to the cluster (dot format)",
    )
    join_cluster_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number of the spare node to add to the cluster",
    )
    join_cluster_parser.add_argument(
        "--name", required=True, help="Name of the spare node to add to the cluster"
    )

    # leave_cluster subcommand
    leave_cluster_parser = subparsers.add_parser(
        "leave_cluster",
        parents=[parent_parser],
        help="Remove a peer node from the cluster (automatically retrieves integration token)",
    )
    leave_cluster_parser.add_argument(
        "--ip_cluster",
        required=True,
        help="IP address of the cluster node (dot format)",
    )
    leave_cluster_parser.add_argument(
        "--port_cluster",
        type=int,
        required=True,
        help="Port number of the cluster node",
    )
    leave_cluster_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node to remove from the cluster (dot format)",
    )
    leave_cluster_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node to remove from the cluster",
    )
    leave_cluster_parser.add_argument(
        "--force",
        action="store_true",
        help="Force the removal of the peer node",
    )

    # become_hsa subcommand
    become_hsa_parser = subparsers.add_parser(
        "become_hsa", parents=[parent_parser], help="Add an HSA to a cluster"
    )
    become_hsa_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer HSA node (dot format)"
    )
    become_hsa_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number of the peer HSA node"
    )
    become_hsa_parser.add_argument(
        "--ip_spare", required=True, help="IP address of the spare node (dot format)"
    )
    become_hsa_parser.add_argument(
        "--port_spare", type=int, required=True, help="Port number of the spare node"
    )

    # leave_cluster_hsa subcommand
    leave_cluster_hsa_parser = subparsers.add_parser(
        "leave_cluster_hsa",
        parents=[parent_parser],
        help="Remove an HSA from a cluster",
    )
    leave_cluster_hsa_parser.add_argument(
        "--ip_peer", required=True, help="IP address of the peer node (dot format)"
    )
    leave_cluster_hsa_parser.add_argument(
        "--port_peer", type=int, required=True, help="Port number of the peer node"
    )
    leave_cluster_hsa_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA to be removed (dot format)",
    )
    leave_cluster_hsa_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number of the HSA to be removed",
    )
    leave_cluster_hsa_parser.add_argument(
        "--force",
        action="store_true",
        help="Force the removal of the HSA",
    )


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
    repaveswitch_parser.add_argument(
        "--force",
        action="store_true",
        help="Force the leave cluster operations",
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
    repave_parser.add_argument(
        "--force",
        action="store_true",
        help="Force the leave cluster operations",
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

    logger.info(f"Cluster client started")

    # Log configuration options
    logger.info(f"Configuration: {json.dumps(config_overrides, indent=2)}")

    # Log the command and parameters
    command_params = vars(args).copy()
    # Remove sensitive information from logging
    if 'password' in command_params:
        command_params['password'] = '***REDACTED***'
    logger.info(f"Command: {args.command}")
    logger.info(f"Parameters: {json.dumps(command_params, indent=2)}")
    
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
        if args.command == "peer_table":
            node = Node(port=args.port, ip=args.ip, username=username, password=password)
            peer_table(peer=node)
        elif args.command == "get_integration_token":
            node = Node(port=args.port, ip=args.ip, username=username, password=password)
            integration_token = get_integration_token(node=node)
            print(integration_token)
        elif args.command == "fail_over":
            node = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            fail_over(node=node)
        elif args.command == "switch_primary_secondary":
            node = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            switch_primary_secondary(peer=node)
        elif args.command == "join_cluster":
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            spare = Node(port=args.port_spare, ip=args.ip_spare, username=username, password=password)
            precondition_single(state=1, peer=spare)
            join_cluster(
                peer=peer,
                spare=spare,
                name=args.name,
            )
            spare.token = peer.token
            postcondition_single(state=2, peer=spare)
        elif args.command == "leave_cluster":
            cluster_node = Node(
                port=args.port_cluster, ip=args.ip_cluster, username=username, password=password
            )
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            precondition_single(state=2, peer=peer)
            leave_cluster(
                cluster=cluster_node,
                peer=peer,
                force=args.force,
            )
            postcondition_single(state=1, peer=peer)
        elif args.command == "become_hsa":
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            spare = Node(port=args.port_spare, ip=args.ip_spare, username=username, password=password)
            peer_state = get_single_state(peer=peer)
            if peer_state not in [1, 2]:
                raise RuntimeError("Peer node already has a HSA)")
            precondition_single(state=1, peer=spare)
            become_hsa(spare=spare, peer=peer)
            spare.token=peer.token
            postcondition_double(state=2, peer=peer, hsa=spare)
        elif args.command == "leave_cluster_hsa":
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            hsa = Node(port=args.port_hsa, ip=args.ip_hsa, username=username, password=password)
            postcondition_double(state=2, peer=peer, hsa=hsa)
            leave_cluster_hsa(hsa=hsa, peer=peer, force=args.force)
            postcondition_single(state=1, peer=hsa)
            postcondition_single(state=2, peer=peer)
        elif args.command == "double_state":
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            hsa = Node(port=args.port_hsa, ip=args.ip_hsa, username=username, password=password)
            current_state = get_double_state(peer=peer, hsa=hsa)
            print()
            print(double_state_table(peer=peer, hsa=hsa))
            print()
            print(f"State: {current_state}")
        elif args.command == "single_state":
            node = Node(port=args.port, ip=args.ip, username=username, password=password)
            current_state = get_single_state(peer=node)
            print()
            print(single_state_table(peer=node))
            print()
            print(f"State: {current_state}")
        elif args.command == "triple_state":
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            hsa = Node(port=args.port_hsa, ip=args.ip_hsa, username=username, password=password)
            spare = Node(port=args.port_spare, ip=args.ip_spare, username=username, password=password)
            current_state = get_triple_state(peer=peer, hsa=hsa, spare=spare)
            print()
            print(triple_state_table(peer=peer, hsa=hsa, spare=spare))
            print()
            print(f"State: {current_state}")
        elif args.command == "repaveswitch":
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            hsa = Node(port=args.port_hsa, ip=args.ip_hsa, username=username, password=password)
            spare = Node(port=args.port_spare, ip=args.ip_spare, username=username, password=password)
            repaveswitch(peer=peer, hsa=hsa, spare=spare, force=args.force)
        elif args.command == "repave":
            peer = Node(port=args.port_peer, ip=args.ip_peer, username=username, password=password)
            hsa = Node(port=args.port_hsa, ip=args.ip_hsa, username=username, password=password)
            spare = Node(port=args.port_spare, ip=args.ip_spare, username=username, password=password)
            repave(peer=peer, hsa=hsa, spare=spare, force=args.force)
        else:
            logger.error(f"Unknown command: {args.command}")
        print("✓ Operation completed successfully!")

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
