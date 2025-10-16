from typing import List

from .supabase_client import list_style_files, download_style_file, list_recent_content, save_draft
from .groq_client import generate_draft as groq_generate
from .trend_engine import compute_trends


def _load_style_samples(user_id: str, max_files: int = 3, max_chars: int = 6000) -> List[str]:
    files = list_style_files(user_id=user_id)
    samples: List[str] = []
    for obj in files[:max_files]:
        name = obj.get("name") or obj.get("path") or ""
        if not name:
            continue
        data = download_style_file(user_id=user_id, filename=name)
        if not data:
            continue
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            continue
        samples.append(text[:max_chars])
    return samples


def generate_and_save_draft(*, user_id: str, selected_item_ids: list[int] | None = None, temperature: float = 0.7, num_links: int = 5, num_trends: int = 3, include_intro: bool = True, include_links: bool = True, include_trends: bool = True) -> str:
    content_items = list_recent_content(user_id=user_id, limit=50)
    if selected_item_ids:
        id_set = set(selected_item_ids)
        content_items = [c for c in content_items if c.get("id") in id_set]
    if not content_items:
        return ""
    style_samples = _load_style_samples(user_id)
    trend_pairs = compute_trends(content_items)
    trend_terms = [t for t, _ in trend_pairs]
    draft_text = groq_generate(
        style_samples, 
        content_items, 
        creator_name="Creator", 
        temperature=temperature, 
        num_links=num_links, 
        trends=trend_terms, 
        num_trends=num_trends,
        include_intro=include_intro,
        include_links=include_links,
        include_trends=include_trends
    )
    if draft_text:
        save_draft(user_id, draft_text)
    return draft_text


