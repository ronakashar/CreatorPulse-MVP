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
    res = sb.table("users").select("id,email,name,timezone").eq("id", user_id).single().execute()
    return res.data if getattr(res, "data", None) else None


def update_user_profile(*, user_id: str, name: str, email: str, timezone: str) -> None:
    sb = get_client()
    sb.table("users").update({"name": name, "email": email, "timezone": timezone}).eq("id", user_id).execute()


# ---------- Sources ----------
def list_sources(*, user_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("user_sources").select("id,source_type,source_value").eq("user_id", user_id).order("id").execute()
    return res.data or []


def add_source(*, user_id: str, source_type: str, source_value: str) -> None:
    sb = get_client()
    sb.table("user_sources").insert({
        "user_id": user_id,
        "source_type": source_type,
        "source_value": source_value,
    }).execute()


def remove_source(source_id: Any) -> None:
    sb = get_client()
    sb.table("user_sources").delete().eq("id", source_id).execute()


# ---------- Content items ----------
def save_content_items(*, user_id: str, items: List[Dict[str, Any]]) -> int:
    if not items:
        return 0
    sb = get_client()
    rows = []
    for it in items:
        rows.append({
            "user_id": user_id,
            "source_id": it.get("source_id"),
            "title": it.get("title"),
            "url": it.get("url"),
            "summary": it.get("summary"),
        })
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


def list_recent_content(*, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("content_items")
        .select("id,title,url,summary,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
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


# ---------- Storage for style files ----------
def upload_style_file(*, user_id: str, filename: str, data: bytes) -> None:
    sb = get_client()
    path = f"{user_id}/{filename}"
    sb.storage.from_(_STYLE_BUCKET).upload(path, data)


def list_style_files(*, user_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    path = f"{user_id}"
    try:
        return sb.storage.from_(_STYLE_BUCKET).list(path) or []
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


