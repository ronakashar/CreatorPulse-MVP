import asyncio
from typing import List, Dict, Any, Optional
from services.supabase_client import (
    get_client,
    create_bulk_operation,
    update_bulk_operation_status,
    get_workspace_members,
    list_recent_content,
    get_latest_draft,
    mark_latest_draft_sent,
)
from services.newsletter_generator import generate_and_save_draft
from services.content_fetcher import fetch_all_sources
from services.resend_client import send_email
from utils.formatting import markdown_to_html, inject_tracking


class BulkOperationManager:
    """Manages bulk operations across multiple workspaces"""
    
    def __init__(self):
        self.sb = get_client()
    
    def create_bulk_fetch_operation(self, *, workspace_id: str, target_workspaces: List[str], created_by: str) -> Dict[str, Any]:
        """Create a bulk source fetching operation"""
        return create_bulk_operation(
            workspace_id=workspace_id,
            operation_type="source_fetch",
            target_workspaces=target_workspaces,
            created_by=created_by
        )
    
    def create_bulk_generate_operation(self, *, workspace_id: str, target_workspaces: List[str], created_by: str) -> Dict[str, Any]:
        """Create a bulk draft generation operation"""
        return create_bulk_operation(
            workspace_id=workspace_id,
            operation_type="draft_generate",
            target_workspaces=target_workspaces,
            created_by=created_by
        )
    
    def create_bulk_send_operation(self, *, workspace_id: str, target_workspaces: List[str], created_by: str) -> Dict[str, Any]:
        """Create a bulk newsletter sending operation"""
        return create_bulk_operation(
            workspace_id=workspace_id,
            operation_type="newsletter_send",
            target_workspaces=target_workspaces,
            created_by=created_by
        )
    
    def execute_bulk_fetch(self, operation_id: int) -> Dict[str, Any]:
        """Execute bulk source fetching across workspaces"""
        # Get operation details
        operation_res = self.sb.table("bulk_operations").select("*").eq("id", operation_id).execute()
        if not operation_res.data:
            raise ValueError("Operation not found")
        
        operation = operation_res.data[0]
        target_workspaces = operation["target_workspaces"]
        
        # Update status to running
        update_bulk_operation_status(operation_id=operation_id, status="running")
        
        results = {}
        progress = {"total": len(target_workspaces), "completed": 0, "failed": 0}
        
        try:
            for workspace_id in target_workspaces:
                try:
                    # Get workspace members to find a user to run the operation
                    members = get_workspace_members(workspace_id=workspace_id)
                    if not members:
                        results[workspace_id] = {"status": "failed", "error": "No members found"}
                        progress["failed"] += 1
                        continue
                    
                    # Use the first member as the user
                    user_id = members[0]["user_id"]
                    
                    # Fetch sources for this workspace
                    num_items = fetch_all_sources(user_id=user_id, workspace_id=workspace_id)
                    results[workspace_id] = {"status": "success", "items_fetched": num_items}
                    progress["completed"] += 1
                    
                except Exception as e:
                    results[workspace_id] = {"status": "failed", "error": str(e)}
                    progress["failed"] += 1
            
            # Update final status
            final_status = "completed" if progress["failed"] == 0 else "completed"
            update_bulk_operation_status(
                operation_id=operation_id,
                status=final_status,
                progress=progress,
                results=results
            )
            
            return {"status": final_status, "progress": progress, "results": results}
            
        except Exception as e:
            update_bulk_operation_status(
                operation_id=operation_id,
                status="failed",
                error_message=str(e)
            )
            raise
    
    def execute_bulk_generate(self, operation_id: int, temperature: float = 0.7, num_links: int = 5) -> Dict[str, Any]:
        """Execute bulk draft generation across workspaces"""
        # Get operation details
        operation_res = self.sb.table("bulk_operations").select("*").eq("id", operation_id).execute()
        if not operation_res.data:
            raise ValueError("Operation not found")
        
        operation = operation_res.data[0]
        target_workspaces = operation["target_workspaces"]
        
        # Update status to running
        update_bulk_operation_status(operation_id=operation_id, status="running")
        
        results = {}
        progress = {"total": len(target_workspaces), "completed": 0, "failed": 0}
        
        try:
            for workspace_id in target_workspaces:
                try:
                    # Get workspace members to find a user to run the operation
                    members = get_workspace_members(workspace_id=workspace_id)
                    if not members:
                        results[workspace_id] = {"status": "failed", "error": "No members found"}
                        progress["failed"] += 1
                        continue
                    
                    # Use the first member as the user
                    user_id = members[0]["user_id"]
                    
                    # Generate draft for this workspace
                    draft_text = generate_and_save_draft(
                        user_id=user_id,
                        workspace_id=workspace_id,
                        selected_item_ids=None,
                        temperature=temperature,
                        num_links=num_links
                    )
                    
                    if draft_text:
                        results[workspace_id] = {"status": "success", "draft_generated": True, "length": len(draft_text)}
                    else:
                        results[workspace_id] = {"status": "success", "draft_generated": False, "reason": "No content available"}
                    
                    progress["completed"] += 1
                    
                except Exception as e:
                    results[workspace_id] = {"status": "failed", "error": str(e)}
                    progress["failed"] += 1
            
            # Update final status
            final_status = "completed" if progress["failed"] == 0 else "completed"
            update_bulk_operation_status(
                operation_id=operation_id,
                status=final_status,
                progress=progress,
                results=results
            )
            
            return {"status": final_status, "progress": progress, "results": results}
            
        except Exception as e:
            update_bulk_operation_status(
                operation_id=operation_id,
                status="failed",
                error_message=str(e)
            )
            raise
    
    def execute_bulk_send(self, operation_id: int) -> Dict[str, Any]:
        """Execute bulk newsletter sending across workspaces"""
        # Get operation details
        operation_res = self.sb.table("bulk_operations").select("*").eq("id", operation_id).execute()
        if not operation_res.data:
            raise ValueError("Operation not found")
        
        operation = operation_res.data[0]
        target_workspaces = operation["target_workspaces"]
        
        # Update status to running
        update_bulk_operation_status(operation_id=operation_id, status="running")
        
        results = {}
        progress = {"total": len(target_workspaces), "completed": 0, "failed": 0}
        
        try:
            for workspace_id in target_workspaces:
                try:
                    # Get workspace members to find a user to run the operation
                    members = get_workspace_members(workspace_id=workspace_id)
                    if not members:
                        results[workspace_id] = {"status": "failed", "error": "No members found"}
                        progress["failed"] += 1
                        continue
                    
                    # Use the first member as the user
                    user_id = members[0]["user_id"]
                    
                    # Get user email
                    user_res = self.sb.table("users").select("email").eq("id", user_id).execute()
                    if not user_res.data:
                        results[workspace_id] = {"status": "failed", "error": "User not found"}
                        progress["failed"] += 1
                        continue
                    
                    user_email = user_res.data[0]["email"]
                    
                    # Get latest draft
                    latest_draft = get_latest_draft(user_id=user_id)
                    if not latest_draft or not latest_draft.get("draft_text"):
                        results[workspace_id] = {"status": "failed", "error": "No draft available"}
                        progress["failed"] += 1
                        continue
                    
                    # Send email
                    html = markdown_to_html(latest_draft["draft_text"])
                    html = inject_tracking(html, user_id=user_id, draft_id=latest_draft.get("id"), api_url="https://npedokgktkcbeltkaovz.supabase.co/functions/v1")
                    
                    send_email(to_email=user_email, subject="Your CreatorPulse Draft", html_content=html)
                    mark_latest_draft_sent(user_id=user_id)
                    
                    results[workspace_id] = {"status": "success", "email_sent": True, "recipient": user_email}
                    progress["completed"] += 1
                    
                except Exception as e:
                    results[workspace_id] = {"status": "failed", "error": str(e)}
                    progress["failed"] += 1
            
            # Update final status
            final_status = "completed" if progress["failed"] == 0 else "completed"
            update_bulk_operation_status(
                operation_id=operation_id,
                status=final_status,
                progress=progress,
                results=results
            )
            
            return {"status": final_status, "progress": progress, "results": results}
            
        except Exception as e:
            update_bulk_operation_status(
                operation_id=operation_id,
                status="failed",
                error_message=str(e)
            )
            raise


# Convenience functions
def run_bulk_fetch(*, workspace_id: str, target_workspaces: List[str], created_by: str) -> Dict[str, Any]:
    """Run bulk source fetching operation"""
    manager = BulkOperationManager()
    operation = manager.create_bulk_fetch_operation(
        workspace_id=workspace_id,
        target_workspaces=target_workspaces,
        created_by=created_by
    )
    return manager.execute_bulk_fetch(operation["id"])


def run_bulk_generate(*, workspace_id: str, target_workspaces: List[str], created_by: str, temperature: float = 0.7, num_links: int = 5) -> Dict[str, Any]:
    """Run bulk draft generation operation"""
    manager = BulkOperationManager()
    operation = manager.create_bulk_generate_operation(
        workspace_id=workspace_id,
        target_workspaces=target_workspaces,
        created_by=created_by
    )
    return manager.execute_bulk_generate(operation["id"], temperature=temperature, num_links=num_links)


def run_bulk_send(*, workspace_id: str, target_workspaces: List[str], created_by: str) -> Dict[str, Any]:
    """Run bulk newsletter sending operation"""
    manager = BulkOperationManager()
    operation = manager.create_bulk_send_operation(
        workspace_id=workspace_id,
        target_workspaces=target_workspaces,
        created_by=created_by
    )
    return manager.execute_bulk_send(operation["id"])
