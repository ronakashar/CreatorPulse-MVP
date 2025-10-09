from typing import Optional


def markdown_to_html(md_text: str) -> str:
    try:
        import markdown  # type: ignore
    except Exception:
        # Minimal fallback: wrap in <pre>
        return f"<pre>{md_text}</pre>"
    return markdown.markdown(md_text, extensions=["extra", "sane_lists"])  # type: ignore


def safe_truncate(text: Optional[str], length: int = 240) -> str:
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[: max(0, length - 1)] + "…"


