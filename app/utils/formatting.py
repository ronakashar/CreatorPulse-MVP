from typing import Optional
import difflib


def markdown_to_html(md_text: str) -> str:
    try:
        import markdown  # type: ignore
    except Exception:
        # Minimal fallback: wrap in <pre>
        return f"<pre>{md_text}</pre>"
    return markdown.markdown(md_text, extensions=["extra", "sane_lists"])  # type: ignore


def inject_tracking(html: str, *, user_id: str | None = None, draft_id: int | None = None, api_url: str | None = None) -> str:
    import re
    base = api_url or ""
    q = []
    if user_id:
        q.append(f"user={user_id}")
    if draft_id is not None:
        q.append(f"draft={draft_id}")
    qs = ("?" + "&".join(q)) if q else ""
    
    # Wrap links with click tracking
    def wrap_link(match):
        url = match.group(1)
        return f'<a href="{base}/email-click{qs}&url={url}" target="_blank">{match.group(2)}</a>'
    
    # Wrap markdown-style links [text](url)
    html = re.sub(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', wrap_link, html)
    
    # Add open tracking pixel
    pixel_url = f"{base}/email-open{qs}" if base else f"/email-open{qs}"
    pixel = f"<img src=\"{pixel_url}\" width=\"1\" height=\"1\" style=\"display:none\" alt=\"\" />"
    return html + pixel


def safe_truncate(text: Optional[str], length: int = 240) -> str:
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[: max(0, length - 1)] + "…"


def unified_diff(a: str, b: str, *, context: int = 2) -> str:
    a_lines = (a or "").splitlines()
    b_lines = (b or "").splitlines()
    diff = difflib.unified_diff(a_lines, b_lines, fromfile="generated", tofile="edited", n=context)
    return "\n".join(diff)


