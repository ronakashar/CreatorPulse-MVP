import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from services.supabase_client import get_client


class AnalyticsTracker:
    """Advanced analytics tracking and reporting system"""
    
    def __init__(self):
        self.sb = get_client()
    
    def track_event(self, *, user_id: str, workspace_id: str, event_type: str, event_category: str, event_name: str, metadata: Dict[str, Any] = None, cost_cents: int = 0) -> None:
        """Track an analytics event"""
        event_data = {
            "user_id": user_id,
            "workspace_id": workspace_id,
            "event_type": event_type,
            "event_category": event_category,
            "event_name": event_name,
            "cost_cents": cost_cents
        }
        
        if metadata:
            event_data["metadata"] = metadata
        
        self.sb.table("analytics_events").insert(event_data).execute()
    
    def track_api_call(self, *, user_id: str, workspace_id: str, api_provider: str, endpoint: str, tokens_used: int = 0, cost_cents: int = 0) -> None:
        """Track API calls with cost information"""
        metadata = {
            "api_provider": api_provider,
            "endpoint": endpoint,
            "tokens_used": tokens_used
        }
        
        self.track_event(
            user_id=user_id,
            workspace_id=workspace_id,
            event_type="api_call",
            event_category="external_api",
            event_name=f"{api_provider}_{endpoint}",
            metadata=metadata,
            cost_cents=cost_cents
        )
    
    def track_storage_upload(self, *, user_id: str, workspace_id: str, file_size_bytes: int, file_type: str, storage_provider: str = "supabase") -> None:
        """Track storage uploads"""
        metadata = {
            "file_size_bytes": file_size_bytes,
            "file_type": file_type,
            "storage_provider": storage_provider
        }
        
        # Calculate cost based on storage (rough estimate)
        cost_cents = int(file_size_bytes / 1024 / 1024 * 0.1)  # $0.10 per MB
        
        self.track_event(
            user_id=user_id,
            workspace_id=workspace_id,
            event_type="storage_upload",
            event_category="storage",
            event_name="file_upload",
            metadata=metadata,
            cost_cents=cost_cents
        )
    
    def track_email_sent(self, *, user_id: str, workspace_id: str, recipient_count: int, email_provider: str = "resend") -> None:
        """Track email sends"""
        metadata = {
            "recipient_count": recipient_count,
            "email_provider": email_provider
        }
        
        # Calculate cost based on email sends (rough estimate)
        cost_cents = recipient_count * 1  # $0.01 per email
        
        self.track_event(
            user_id=user_id,
            workspace_id=workspace_id,
            event_type="email_sent",
            event_category="communication",
            event_name="newsletter_send",
            metadata=metadata,
            cost_cents=cost_cents
        )
    
    def track_source_fetch(self, *, user_id: str, workspace_id: str, source_type: str, items_fetched: int, source_url: str = None) -> None:
        """Track source fetching operations"""
        metadata = {
            "source_type": source_type,
            "items_fetched": items_fetched,
            "source_url": source_url
        }
        
        self.track_event(
            user_id=user_id,
            workspace_id=workspace_id,
            event_type="source_fetch",
            event_category="content",
            event_name="fetch_sources",
            metadata=metadata
        )
    
    def track_draft_generation(self, *, user_id: str, workspace_id: str, draft_length: int, sources_used: int, generation_time_ms: int = None) -> None:
        """Track draft generation"""
        metadata = {
            "draft_length": draft_length,
            "sources_used": sources_used,
            "generation_time_ms": generation_time_ms
        }
        
        self.track_event(
            user_id=user_id,
            workspace_id=workspace_id,
            event_type="draft_generate",
            event_category="ai_generation",
            event_name="generate_draft",
            metadata=metadata
        )
    
    def track_user_action(self, *, user_id: str, workspace_id: str, action: str, page: str, metadata: Dict[str, Any] = None) -> None:
        """Track user actions"""
        self.track_event(
            user_id=user_id,
            workspace_id=workspace_id,
            event_type="user_action",
            event_category="engagement",
            event_name=action,
            metadata={"page": page, **(metadata or {})}
        )


class AnalyticsReporter:
    """Generate analytics reports and insights"""
    
    def __init__(self):
        self.sb = get_client()
    
    def get_usage_summary(self, *, workspace_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for a workspace"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Get all events for the period
        events_res = (
            self.sb.table("analytics_events")
            .select("*")
            .eq("workspace_id", workspace_id)
            .gte("created_at", cutoff_date)
            .execute()
        )
        
        events = events_res.data or []
        
        # Calculate metrics
        total_cost = sum(event.get("cost_cents", 0) for event in events)
        
        api_calls = [e for e in events if e["event_type"] == "api_call"]
        storage_uploads = [e for e in events if e["event_type"] == "storage_upload"]
        emails_sent = [e for e in events if e["event_type"] == "email_sent"]
        source_fetches = [e for e in events if e["event_type"] == "source_fetch"]
        draft_generations = [e for e in events if e["event_type"] == "draft_generate"]
        
        # API usage breakdown
        api_providers = {}
        for call in api_calls:
            provider = call.get("metadata", {}).get("api_provider", "unknown")
            api_providers[provider] = api_providers.get(provider, 0) + 1
        
        # Storage usage
        total_storage_bytes = sum(
            upload.get("metadata", {}).get("file_size_bytes", 0) 
            for upload in storage_uploads
        )
        
        # Email metrics
        total_recipients = sum(
            email.get("metadata", {}).get("recipient_count", 1) 
            for email in emails_sent
        )
        
        # Source fetch metrics
        total_items_fetched = sum(
            fetch.get("metadata", {}).get("items_fetched", 0) 
            for fetch in source_fetches
        )
        
        return {
            "period_days": days,
            "total_events": len(events),
            "total_cost_cents": total_cost,
            "total_cost_dollars": total_cost / 100,
            "api_calls": {
                "total": len(api_calls),
                "by_provider": api_providers
            },
            "storage": {
                "uploads": len(storage_uploads),
                "total_bytes": total_storage_bytes,
                "total_mb": total_storage_bytes / 1024 / 1024
            },
            "emails": {
                "sent": len(emails_sent),
                "recipients": total_recipients
            },
            "content": {
                "source_fetches": len(source_fetches),
                "items_fetched": total_items_fetched,
                "draft_generations": len(draft_generations)
            }
        }
    
    def get_cost_breakdown(self, *, workspace_id: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed cost breakdown"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        events_res = (
            self.sb.table("analytics_events")
            .select("event_type, cost_cents, metadata")
            .eq("workspace_id", workspace_id)
            .gte("created_at", cutoff_date)
            .gt("cost_cents", 0)
            .execute()
        )
        
        events = events_res.data or []
        
        cost_by_type = {}
        cost_by_category = {}
        
        for event in events:
            event_type = event["event_type"]
            cost = event["cost_cents"]
            
            cost_by_type[event_type] = cost_by_type.get(event_type, 0) + cost
            
            # Categorize costs
            if event_type == "api_call":
                category = "API Usage"
            elif event_type == "storage_upload":
                category = "Storage"
            elif event_type == "email_sent":
                category = "Email Delivery"
            else:
                category = "Other"
            
            cost_by_category[category] = cost_by_category.get(category, 0) + cost
        
        return {
            "total_cost_cents": sum(cost_by_type.values()),
            "total_cost_dollars": sum(cost_by_type.values()) / 100,
            "by_event_type": cost_by_type,
            "by_category": cost_by_category,
            "period_days": days
        }
    
    def get_performance_metrics(self, *, workspace_id: str, days: int = 30) -> Dict[str, Any]:
        """Get performance metrics"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Get draft generation events with timing data
        drafts_res = (
            self.sb.table("analytics_events")
            .select("metadata, created_at")
            .eq("workspace_id", workspace_id)
            .eq("event_type", "draft_generate")
            .gte("created_at", cutoff_date)
            .execute()
        )
        
        drafts = drafts_res.data or []
        
        generation_times = []
        draft_lengths = []
        
        for draft in drafts:
            metadata = draft.get("metadata", {})
            if metadata.get("generation_time_ms"):
                generation_times.append(metadata["generation_time_ms"])
            if metadata.get("draft_length"):
                draft_lengths.append(metadata["draft_length"])
        
        # Calculate averages
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0
        avg_draft_length = sum(draft_lengths) / len(draft_lengths) if draft_lengths else 0
        
        return {
            "draft_generation": {
                "total_generations": len(drafts),
                "avg_generation_time_ms": avg_generation_time,
                "avg_draft_length": avg_draft_length
            },
            "period_days": days
        }
    
    def get_engagement_metrics(self, *, workspace_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user engagement metrics"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Get user action events
        actions_res = (
            self.sb.table("analytics_events")
            .select("event_name, metadata, created_at")
            .eq("workspace_id", workspace_id)
            .eq("event_type", "user_action")
            .gte("created_at", cutoff_date)
            .execute()
        )
        
        actions = actions_res.data or []
        
        # Count actions by type
        action_counts = {}
        page_visits = {}
        
        for action in actions:
            action_name = action["event_name"]
            metadata = action.get("metadata", {})
            page = metadata.get("page", "unknown")
            
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
            page_visits[page] = page_visits.get(page, 0) + 1
        
        return {
            "total_actions": len(actions),
            "action_breakdown": action_counts,
            "page_visits": page_visits,
            "period_days": days
        }
    
    def generate_report(self, *, workspace_id: str, report_type: str, period_start: datetime, period_end: datetime, generated_by: str) -> Dict[str, Any]:
        """Generate a comprehensive analytics report"""
        days = (period_end - period_start).days
        
        if report_type == "usage":
            data = self.get_usage_summary(workspace_id=workspace_id, days=days)
        elif report_type == "cost":
            data = self.get_cost_breakdown(workspace_id=workspace_id, days=days)
        elif report_type == "performance":
            data = self.get_performance_metrics(workspace_id=workspace_id, days=days)
        elif report_type == "engagement":
            data = self.get_engagement_metrics(workspace_id=workspace_id, days=days)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Save report to database
        report_res = self.sb.table("analytics_reports").insert({
            "workspace_id": workspace_id,
            "report_type": report_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "data": data,
            "generated_by": generated_by
        }).execute()
        
        return report_res.data[0]


# Convenience functions
def track_api_call(*, user_id: str, workspace_id: str, api_provider: str, endpoint: str, tokens_used: int = 0, cost_cents: int = 0) -> None:
    """Track an API call"""
    tracker = AnalyticsTracker()
    tracker.track_api_call(
        user_id=user_id,
        workspace_id=workspace_id,
        api_provider=api_provider,
        endpoint=endpoint,
        tokens_used=tokens_used,
        cost_cents=cost_cents
    )


def track_email_sent(*, user_id: str, workspace_id: str, recipient_count: int = 1) -> None:
    """Track an email send"""
    tracker = AnalyticsTracker()
    tracker.track_email_sent(
        user_id=user_id,
        workspace_id=workspace_id,
        recipient_count=recipient_count
    )


def track_draft_generation(*, user_id: str, workspace_id: str, draft_length: int, sources_used: int, generation_time_ms: int = None) -> None:
    """Track draft generation"""
    tracker = AnalyticsTracker()
    tracker.track_draft_generation(
        user_id=user_id,
        workspace_id=workspace_id,
        draft_length=draft_length,
        sources_used=sources_used,
        generation_time_ms=generation_time_ms
    )


def track_user_action(*, user_id: str, workspace_id: str, action: str, page: str, metadata: Dict[str, Any] = None) -> None:
    """Track a user action"""
    tracker = AnalyticsTracker()
    tracker.track_user_action(
        user_id=user_id,
        workspace_id=workspace_id,
        action=action,
        page=page,
        metadata=metadata
    )
