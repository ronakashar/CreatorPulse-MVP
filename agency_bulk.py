#!/usr/bin/env python3
"""
Agency Bulk Operations CLI

This script allows running bulk operations from the command line,
useful for scheduled tasks and automation.

Usage:
    python agency_bulk.py fetch --workspace-id <id> --target-workspaces <id1,id2,id3>
    python agency_bulk.py generate --workspace-id <id> --target-workspaces <id1,id2,id3>
    python agency_bulk.py send --workspace-id <id> --target-workspaces <id1,id2,id3>
"""

import os
import argparse
import sys
from typing import List

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.bulk_operations import run_bulk_fetch, run_bulk_generate, run_bulk_send
from services.supabase_client import get_user_by_email


def parse_workspace_ids(workspace_ids_str: str) -> List[str]:
    """Parse comma-separated workspace IDs"""
    return [ws_id.strip() for ws_id in workspace_ids_str.split(',') if ws_id.strip()]


def main():
    parser = argparse.ArgumentParser(description="Agency Bulk Operations CLI")
    subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')
    
    # Common arguments
    parser.add_argument('--workspace-id', required=True, help='Agency workspace ID')
    parser.add_argument('--target-workspaces', required=True, help='Comma-separated target workspace IDs')
    parser.add_argument('--created-by', required=True, help='Email of user creating the operation')
    
    # Fetch operation
    fetch_parser = subparsers.add_parser('fetch', help='Bulk fetch sources')
    
    # Generate operation
    generate_parser = subparsers.add_parser('generate', help='Bulk generate drafts')
    generate_parser.add_argument('--temperature', type=float, default=0.7, help='Creativity level (0.0-1.0)')
    generate_parser.add_argument('--num-links', type=int, default=5, help='Number of links to include')
    
    # Send operation
    send_parser = subparsers.add_parser('send', help='Bulk send newsletters')
    
    args = parser.parse_args()
    
    if not args.operation:
        parser.print_help()
        return
    
    # Parse workspace IDs
    target_workspaces = parse_workspace_ids(args.target_workspaces)
    
    # Get user ID from email
    try:
        user = get_user_by_email(email=args.created_by)
        if not user:
            print(f"Error: User with email {args.created_by} not found")
            return
        created_by = user["id"]
    except Exception as e:
        print(f"Error getting user: {e}")
        return
    
    # Run the appropriate operation
    try:
        if args.operation == 'fetch':
            print(f"Running bulk fetch for {len(target_workspaces)} workspaces...")
            result = run_bulk_fetch(
                workspace_id=args.workspace_id,
                target_workspaces=target_workspaces,
                created_by=created_by
            )
            print(f"✅ Bulk fetch completed: {result['progress']['completed']} successful, {result['progress']['failed']} failed")
            
        elif args.operation == 'generate':
            print(f"Running bulk generate for {len(target_workspaces)} workspaces...")
            result = run_bulk_generate(
                workspace_id=args.workspace_id,
                target_workspaces=target_workspaces,
                created_by=created_by,
                temperature=args.temperature,
                num_links=args.num_links
            )
            print(f"✅ Bulk generate completed: {result['progress']['completed']} successful, {result['progress']['failed']} failed")
            
        elif args.operation == 'send':
            print(f"Running bulk send for {len(target_workspaces)} workspaces...")
            result = run_bulk_send(
                workspace_id=args.workspace_id,
                target_workspaces=target_workspaces,
                created_by=created_by
            )
            print(f"✅ Bulk send completed: {result['progress']['completed']} successful, {result['progress']['failed']} failed")
        
        # Print detailed results
        if result.get('results'):
            print("\nDetailed Results:")
            for workspace_id, workspace_result in result['results'].items():
                status = workspace_result.get('status', 'unknown')
                if status == 'success':
                    print(f"  ✅ {workspace_id}: {workspace_result}")
                else:
                    print(f"  ❌ {workspace_id}: {workspace_result}")
    
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return


if __name__ == "__main__":
    main()
