import os
from typing import Any, Dict, List, Optional

from supabase import Client, create_client


_client: Optional[Client] = None
_STYLE_BUCKET = "style-samples"


def get_client() -> Client:
    global _client
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")
    _client = create_client(url, key)
    return _client


# ---------- Auth ----------
def sign_up_with_password(*, email: str, password: str, name: str = "", timezone: str = "") -> Dict[str, Any]:
    sb = get_client()
    res = sb.auth.sign_up({"email": email, "password": password})
    user = getattr(res, "user", None)
    if user and getattr(user, "id", None):
        upsert_user(user.id, email=email, name=name, timezone=timezone)
    return {"user": {"id": getattr(user, "id", None), "email": email}}


def sign_in_with_password(*, email: str, password: str) -> Dict[str, Any]:
    sb = get_client()
    res = sb.auth.sign_in_with_password({"email": email, "password": password})
    user = getattr(res, "user", None)
    return {"user": {"id": getattr(user, "id", None), "email": email}}


def sign_out() -> None:
    sb = get_client()
    sb.auth.sign_out()


def get_current_user() -> Optional[Dict[str, Any]]:
    try:
        sb = get_client()
    except Exception:
        return None
    session = sb.auth.get_session()
    if not session or not getattr(session, "user", None):
        return None
    return {"id": session.user.id, "email": session.user.email}


# ---------- Users table ----------
def upsert_user(user_id: str, *, email: str, name: str = "", timezone: str = "") -> None:
    sb = get_client()
    sb.table("users").upsert({
        "id": user_id,
        "email": email,
        "name": name,
        "timezone": timezone,
    }).execute()


def get_user_profile(*, user_id: str) -> Optional[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("users").select("id,email,name,timezone,send_time_local,send_days,frequency").eq("id", user_id).single().execute()
    return res.data if getattr(res, "data", None) else None


def update_user_profile(*, user_id: str, name: str, email: str, timezone: str, send_time_local: str | None = None, send_days: list[str] | None = None, frequency: str | None = None) -> None:
    sb = get_client()
    payload: Dict[str, Any] = {"name": name, "email": email, "timezone": timezone}
    if send_time_local is not None:
        payload["send_time_local"] = send_time_local
    if send_days is not None:
        payload["send_days"] = send_days
    if frequency is not None:
        payload["frequency"] = frequency
    sb.table("users").update(payload).eq("id", user_id).execute()


def get_user_by_email(*, email: str) -> Optional[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("users").select("id,email,name,timezone,send_time_local,send_days,frequency").eq("email", email).limit(1).execute()
    if res.data:
        return res.data[0]
    return None


# ---------- Sources ----------
def list_sources(*, user_id: str, workspace_id: str = None) -> List[Dict[str, Any]]:
    sb = get_client()
    query = sb.table("user_sources").select("id,source_type,source_value,boost_factor").eq("user_id", user_id).order("id")
    
    if workspace_id:
        query = query.eq("workspace_id", workspace_id)
    
    res = query.execute()
    return res.data or []


def add_source(*, user_id: str, source_type: str, source_value: str, boost_factor: float = 1.0, workspace_id: str = None) -> None:
    sb = get_client()
    data = {
        "user_id": user_id,
        "source_type": source_type,
        "source_value": source_value,
        "boost_factor": boost_factor,
    }
    if workspace_id:
        data["workspace_id"] = workspace_id
    
    sb.table("user_sources").insert(data).execute()


def update_source_boost(*, source_id: int, boost_factor: float) -> None:
    sb = get_client()
    sb.table("user_sources").update({"boost_factor": boost_factor}).eq("id", source_id).execute()


def remove_source(source_id: Any) -> None:
    sb = get_client()
    sb.table("user_sources").delete().eq("id", source_id).execute()


# ---------- Content items ----------
def save_content_items(*, user_id: str, items: List[Dict[str, Any]], workspace_id: str = None) -> int:
    if not items:
        return 0
    sb = get_client()
    rows = []
    for it in items:
        row = {
            "user_id": user_id,
            "source_id": it.get("source_id"),
            "title": it.get("title"),
            "url": it.get("url"),
            "summary": it.get("summary"),
        }
        if workspace_id:
            row["workspace_id"] = workspace_id
        rows.append(row)
    # Attempt upsert; if not supported in client version, fallback to insert
    try:
        sb.table("content_items").upsert(rows).execute()
    except Exception:
        for r in rows:
            try:
                sb.table("content_items").insert(r).execute()
            except Exception:
                pass
    return len(rows)


def list_recent_content(*, user_id: str, workspace_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    sb = get_client()
    query = (
        sb.table("content_items")
        .select("id,title,url,summary,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    
    if workspace_id:
        query = query.eq("workspace_id", workspace_id)
    
    res = query.execute()
    return res.data or []


# ---------- Drafts ----------
def save_draft(user_id: str, draft_text: str, feedback: Optional[str] = None) -> None:
    sb = get_client()
    sb.table("drafts").insert({
        "user_id": user_id,
        "draft_text": draft_text,
        "feedback": feedback,
        "sent": False,
    }).execute()


def get_latest_draft(*, user_id: str) -> Optional[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("drafts")
        .select("id,user_id,draft_text,feedback,sent,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None


def save_draft_feedback(user_id: str, draft_text: str, *, feedback: str) -> None:
    sb = get_client()
    sb.table("drafts").update({"feedback": feedback}).eq("user_id", user_id).eq("draft_text", draft_text).execute()


def mark_latest_draft_sent(*, user_id: str) -> None:
    sb = get_client()
    latest = get_latest_draft(user_id=user_id)
    if latest:
        sb.table("drafts").update({"sent": True}).eq("id", latest["id"]).execute()


def list_drafts(*, user_id: str, limit: int = 20, search: str = "") -> List[Dict[str, Any]]:
    sb = get_client()
    q = (
        sb.table("drafts")
        .select("id,user_id,draft_text,feedback,sent,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if search:
        # Simple filter: PostgREST ilike on draft_text
        q = q.ilike("draft_text", f"%{search}%")
    res = q.execute()
    return res.data or []


def get_draft_by_id(*, draft_id: int) -> Optional[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("drafts").select("id,user_id,draft_text,feedback,sent,created_at").eq("id", draft_id).single().execute()
    return res.data if getattr(res, "data", None) else None


# ---------- Draft edits ----------
def save_draft_edit(*, user_id: str, original_draft_id: int | None, original_text: str, edited_text: str, diff_text: str) -> None:
    sb = get_client()
    sb.table("draft_edits").insert({
        "user_id": user_id,
        "original_draft_id": original_draft_id,
        "original_text": original_text,
        "edited_text": edited_text,
        "diff_text": diff_text,
    }).execute()


# ---------- Analytics & Reporting ----------
def get_analytics_events(*, workspace_id: str, event_type: str = None, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
    from datetime import datetime, timedelta
    
    sb = get_client()
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    query = (
        sb.table("analytics_events")
        .select("*")
        .eq("workspace_id", workspace_id)
        .gte("created_at", cutoff_date)
        .order("created_at", desc=True)
        .limit(limit)
    )
    
    if event_type:
        query = query.eq("event_type", event_type)
    
    res = query.execute()
    return res.data or []


def get_analytics_reports(*, workspace_id: str, report_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
    sb = get_client()
    query = (
        sb.table("analytics_reports")
        .select("*, users(email, name)")
        .eq("workspace_id", workspace_id)
        .order("generated_at", desc=True)
        .limit(limit)
    )
    
    if report_type:
        query = query.eq("report_type", report_type)
    
    res = query.execute()
    return res.data or []


def create_analytics_dashboard(*, workspace_id: str, dashboard_name: str, dashboard_config: Dict[str, Any], created_by: str, is_default: bool = False) -> Dict[str, Any]:
    sb = get_client()
    res = sb.table("analytics_dashboards").insert({
        "workspace_id": workspace_id,
        "dashboard_name": dashboard_name,
        "dashboard_config": dashboard_config,
        "created_by": created_by,
        "is_default": is_default
    }).execute()
    return res.data[0]


def get_analytics_dashboards(*, workspace_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("analytics_dashboards")
        .select("*, users(email, name)")
        .eq("workspace_id", workspace_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def update_analytics_dashboard(*, dashboard_id: int, dashboard_name: str = None, dashboard_config: Dict[str, Any] = None) -> None:
    sb = get_client()
    update_data = {}
    
    if dashboard_name:
        update_data["dashboard_name"] = dashboard_name
    if dashboard_config:
        update_data["dashboard_config"] = dashboard_config
    
    if update_data:
        update_data["updated_at"] = "now()"
        sb.table("analytics_dashboards").update(update_data).eq("id", dashboard_id).execute()


def delete_analytics_dashboard(*, dashboard_id: int) -> None:
    sb = get_client()
    sb.table("analytics_dashboards").delete().eq("id", dashboard_id).execute()


def get_cost_trends(*, workspace_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get daily cost trends for a workspace"""
    from datetime import datetime, timedelta
    
    sb = get_client()
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Get daily cost aggregation
    res = (
        sb.table("analytics_events")
        .select("cost_cents, created_at")
        .eq("workspace_id", workspace_id)
        .gte("created_at", cutoff_date)
        .gt("cost_cents", 0)
        .execute()
    )
    
    events = res.data or []
    
    # Group by date
    daily_costs = {}
    for event in events:
        date = event["created_at"][:10]  # YYYY-MM-DD
        daily_costs[date] = daily_costs.get(date, 0) + event["cost_cents"]
    
    # Convert to list of daily records
    trends = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        trends.append({
            "date": date,
            "cost_cents": daily_costs.get(date, 0),
            "cost_dollars": daily_costs.get(date, 0) / 100
        })
    
    return sorted(trends, key=lambda x: x["date"])


def get_usage_trends(*, workspace_id: str, event_type: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get daily usage trends for a specific event type"""
    from datetime import datetime, timedelta
    
    sb = get_client()
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    res = (
        sb.table("analytics_events")
        .select("created_at")
        .eq("workspace_id", workspace_id)
        .eq("event_type", event_type)
        .gte("created_at", cutoff_date)
        .execute()
    )
    
    events = res.data or []
    
    # Group by date
    daily_counts = {}
    for event in events:
        date = event["created_at"][:10]  # YYYY-MM-DD
        daily_counts[date] = daily_counts.get(date, 0) + 1
    
    # Convert to list of daily records
    trends = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        trends.append({
            "date": date,
            "count": daily_counts.get(date, 0)
        })
    
    return sorted(trends, key=lambda x: x["date"])


# ---------- Agency Dashboard ----------
def create_client_profile(*, workspace_id: str, client_name: str, client_email: str = None, client_website: str = None, industry: str = None, contact_person: str = None, notes: str = None) -> Dict[str, Any]:
    sb = get_client()
    res = sb.table("client_profiles").insert({
        "workspace_id": workspace_id,
        "client_name": client_name,
        "client_email": client_email,
        "client_website": client_website,
        "industry": industry,
        "contact_person": contact_person,
        "notes": notes
    }).execute()
    return res.data[0]


def get_client_profiles(*, workspace_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("client_profiles").select("*").eq("workspace_id", workspace_id).order("created_at", desc=True).execute()
    return res.data or []


def update_client_profile(*, client_id: str, **updates) -> None:
    sb = get_client()
    sb.table("client_profiles").update(updates).eq("id", client_id).execute()


def delete_client_profile(*, client_id: str) -> None:
    sb = get_client()
    sb.table("client_profiles").delete().eq("id", client_id).execute()


def create_client_workspace(*, agency_workspace_id: str, client_profile_id: str, client_workspace_id: str) -> Dict[str, Any]:
    sb = get_client()
    res = sb.table("client_workspaces").insert({
        "agency_workspace_id": agency_workspace_id,
        "client_profile_id": client_profile_id,
        "client_workspace_id": client_workspace_id
    }).execute()
    return res.data[0]


def get_client_workspaces(*, agency_workspace_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("client_workspaces")
        .select("*, client_profiles(*), workspaces(name, slug)")
        .eq("agency_workspace_id", agency_workspace_id)
        .execute()
    )
    return res.data or []


def create_bulk_operation(*, workspace_id: str, operation_type: str, target_workspaces: List[str], created_by: str) -> Dict[str, Any]:
    sb = get_client()
    res = sb.table("bulk_operations").insert({
        "workspace_id": workspace_id,
        "operation_type": operation_type,
        "target_workspaces": target_workspaces,
        "created_by": created_by
    }).execute()
    return res.data[0]


def get_bulk_operations(*, workspace_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("bulk_operations")
        .select("*, users(email, name)")
        .eq("workspace_id", workspace_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def update_bulk_operation_status(*, operation_id: int, status: str, progress: Dict[str, Any] = None, results: Dict[str, Any] = None, error_message: str = None) -> None:
    sb = get_client()
    update_data = {"status": status}
    
    if status == "running":
        update_data["started_at"] = "now()"
    elif status in ["completed", "failed"]:
        update_data["completed_at"] = "now()"
    
    if progress:
        update_data["progress"] = progress
    if results:
        update_data["results"] = results
    if error_message:
        update_data["error_message"] = error_message
    
    sb.table("bulk_operations").update(update_data).eq("id", operation_id).execute()


def get_workspace_analytics(*, workspace_id: str, days: int = 30) -> Dict[str, Any]:
    """Get analytics for a specific workspace"""
    from datetime import datetime, timedelta
    
    sb = get_client()
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Get newsletters sent
    newsletters_res = (
        sb.table("usage_tracking")
        .select("metric_value")
        .eq("workspace_id", workspace_id)
        .eq("metric_type", "newsletter_sent")
        .gte("created_at", cutoff_date)
        .execute()
    )
    newsletters_sent = sum(float(item["metric_value"]) for item in (newsletters_res.data or []))
    
    # Get sources count
    sources_res = sb.table("user_sources").select("id").eq("workspace_id", workspace_id).execute()
    sources_count = len(sources_res.data or [])
    
    # Get team members count
    members_res = sb.table("workspace_members").select("id").eq("workspace_id", workspace_id).execute()
    members_count = len(members_res.data or [])
    
    # Get drafts count
    drafts_res = sb.table("drafts").select("id").eq("workspace_id", workspace_id).gte("created_at", cutoff_date).execute()
    drafts_count = len(drafts_res.data or [])
    
    return {
        "newsletters_sent": newsletters_sent,
        "sources_count": sources_count,
        "members_count": members_count,
        "drafts_count": drafts_count,
        "period_days": days
    }


# ---------- Billing & Subscriptions ----------
def get_subscription_plans() -> List[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("subscription_plans").select("*").eq("active", True).order("price_monthly_cents").execute()
    return res.data or []


def get_user_subscription(*, user_id: str) -> Optional[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("user_subscriptions")
        .select("*, subscription_plans(*)")
        .eq("user_id", user_id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def create_user_subscription(*, user_id: str, plan_id: str, stripe_customer_id: str = None, stripe_subscription_id: str = None) -> Dict[str, Any]:
    sb = get_client()
    subscription_data = {
        "user_id": user_id,
        "plan_id": plan_id,
        "status": "active"
    }
    if stripe_customer_id:
        subscription_data["stripe_customer_id"] = stripe_customer_id
    if stripe_subscription_id:
        subscription_data["stripe_subscription_id"] = stripe_subscription_id
    
    res = sb.table("user_subscriptions").insert(subscription_data).execute()
    return res.data[0]


def update_subscription_status(*, subscription_id: str, status: str, current_period_start: str = None, current_period_end: str = None) -> None:
    sb = get_client()
    update_data = {"status": status}
    if current_period_start:
        update_data["current_period_start"] = current_period_start
    if current_period_end:
        update_data["current_period_end"] = current_period_end
    
    sb.table("user_subscriptions").update(update_data).eq("stripe_subscription_id", subscription_id).execute()


def track_usage(*, user_id: str, workspace_id: str, metric_type: str, metric_value: float = 1.0, metadata: Dict[str, Any] = None) -> None:
    sb = get_client()
    usage_data = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "metric_type": metric_type,
        "metric_value": metric_value
    }
    if metadata:
        usage_data["metadata"] = metadata
    
    sb.table("usage_tracking").insert(usage_data).execute()


def get_usage_for_period(*, user_id: str, metric_type: str, days: int = 30) -> int:
    from datetime import datetime, timedelta
    
    sb = get_client()
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    res = (
        sb.table("usage_tracking")
        .select("metric_value")
        .eq("user_id", user_id)
        .eq("metric_type", metric_type)
        .gte("created_at", cutoff_date)
        .execute()
    )
    
    return sum(float(item["metric_value"]) for item in (res.data or []))


def check_usage_limit(*, user_id: str, metric_type: str, limit: int) -> bool:
    """Check if user has exceeded usage limit for a metric"""
    current_usage = get_usage_for_period(user_id=user_id, metric_type=metric_type)
    return current_usage >= limit


def get_user_plan_limits(*, user_id: str) -> Dict[str, Any]:
    """Get current user's plan limits"""
    subscription = get_user_subscription(user_id=user_id)
    if not subscription:
        # Default to free plan limits
        return {
            "max_workspaces": 1,
            "max_team_members": 1,
            "max_sources": 5,
            "max_newsletters_per_month": 10
        }
    
    plan_data = subscription.get("subscription_plans", {})
    limits = plan_data.get("limits", {})
    return limits


# ---------- Workspaces ----------
def create_workspace(*, name: str, slug: str, description: str = "", owner_id: str) -> Dict[str, Any]:
    sb = get_client()
    
    # Create workspace
    workspace_res = sb.table("workspaces").insert({
        "name": name,
        "slug": slug,
        "description": description
    }).execute()
    
    workspace = workspace_res.data[0]
    
    # Add owner as workspace member
    sb.table("workspace_members").insert({
        "workspace_id": workspace["id"],
        "user_id": owner_id,
        "role": "owner",
        "joined_at": "now()"
    }).execute()
    
    return workspace


def get_user_workspaces(*, user_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("workspace_members")
        .select("workspace_id, role, joined_at, workspaces(name, slug, description, created_at)")
        .eq("user_id", user_id)
        .not_.is_("joined_at", "null")
        .execute()
    )
    return res.data or []


def get_workspace_members(*, workspace_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("workspace_members")
        .select("id, user_id, role, invited_at, joined_at, users!workspace_members_user_id_fkey(email, name)")
        .eq("workspace_id", workspace_id)
        .execute()
    )
    return res.data or []


def invite_user_to_workspace(*, workspace_id: str, email: str, role: str, invited_by: str) -> None:
    sb = get_client()
    
    # Get user by email
    user_res = sb.table("users").select("id").eq("email", email).execute()
    if not user_res.data:
        raise ValueError(f"User with email {email} not found")
    
    user_id = user_res.data[0]["id"]
    
    # Add workspace member
    sb.table("workspace_members").insert({
        "workspace_id": workspace_id,
        "user_id": user_id,
        "role": role,
        "invited_by": invited_by
    }).execute()


def update_workspace_member_role(*, member_id: int, role: str) -> None:
    sb = get_client()
    sb.table("workspace_members").update({"role": role}).eq("id", member_id).execute()


def remove_workspace_member(*, member_id: int) -> None:
    sb = get_client()
    sb.table("workspace_members").delete().eq("id", member_id).execute()


def get_user_workspace_role(*, user_id: str, workspace_id: str) -> Optional[str]:
    sb = get_client()
    res = (
        sb.table("workspace_members")
        .select("role")
        .eq("user_id", user_id)
        .eq("workspace_id", workspace_id)
        .not_.is_("joined_at", "null")
        .execute()
    )
    return res.data[0]["role"] if res.data else None


# ---------- Analytics ----------
def get_email_analytics(*, user_id: str, days: int = 30) -> Dict[str, Any]:
    from datetime import datetime, timedelta
    
    sb = get_client()
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Get opens
    opens_res = (
        sb.table("email_events")
        .select("id,created_at")
        .eq("user_id", user_id)
        .eq("event_type", "open")
        .gte("created_at", cutoff_date)
        .execute()
    )
    opens = opens_res.data or []
    
    # Get clicks
    clicks_res = (
        sb.table("link_clicks")
        .select("id,url,created_at")
        .eq("user_id", user_id)
        .gte("created_at", cutoff_date)
        .execute()
    )
    clicks = clicks_res.data or []
    
    # Get sent emails
    sent_res = (
        sb.table("drafts")
        .select("id,created_at")
        .eq("user_id", user_id)
        .eq("sent", True)
        .gte("created_at", cutoff_date)
        .execute()
    )
    sent = sent_res.data or []
    
    return {
        "opens": len(opens),
        "clicks": len(clicks),
        "sent": len(sent),
        "open_rate": len(opens) / len(sent) if sent else 0,
        "ctr": len(clicks) / len(opens) if opens else 0,
        "clicks_by_url": {url: sum(1 for c in clicks if c["url"] == url) for url in set(c["url"] for c in clicks)},
    }


# ---------- Storage for style files ----------
def upload_style_file(*, user_id: str, filename: str, data: bytes) -> None:
    sb = get_client()
    path = f"{user_id}/{filename}"
    sb.storage.from_(_STYLE_BUCKET).upload(path, data)


def list_style_files(*, user_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    path = f"{user_id}"
    try:
        files = sb.storage.from_(_STYLE_BUCKET).list(path) or []
        # Enhance with content and size for progress meter
        enhanced_files = []
        for file_obj in files:
            enhanced_file = dict(file_obj)
            try:
                # Get file content and size
                content = download_style_file(user_id=user_id, filename=file_obj.get("name", ""))
                enhanced_file["content"] = content.decode('utf-8') if content else ""
                enhanced_file["size"] = len(content) if content else 0
            except:
                enhanced_file["content"] = ""
                enhanced_file["size"] = 0
            enhanced_files.append(enhanced_file)
        return enhanced_files
    except Exception:
        return []


def download_style_file(*, user_id: str, filename: str) -> Optional[bytes]:
    sb = get_client()
    path = f"{user_id}/{filename}"
    try:
        res = sb.storage.from_(_STYLE_BUCKET).download(path)
        return res
    except Exception:
        return None


def delete_style_file(*, user_id: str, filename: str) -> None:
    sb = get_client()
    path = f"{user_id}/{filename}"
    sb.storage.from_(_STYLE_BUCKET).remove([path])


