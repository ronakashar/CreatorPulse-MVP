import os
from typing import List, Dict, Any

from tenacity import retry, stop_after_attempt, wait_exponential


def _build_prompt(creator_name: str, style_samples: List[str], content_items: List[Dict[str, Any]], trends: List[str] | None = None, num_trends: int = 3, include_intro: bool = True, include_links: bool = True, include_trends: bool = True) -> str:
    style_text = "\n\n".join(style_samples[:3]) if style_samples else ""
    curated_lines = []
    for item in content_items[:12]:
        curated_lines.append(f"- {item.get('title','')} — {item.get('url','')}")
    curated_block = "\n".join(curated_lines)
    trends = trends or []
    trends_lines = "\n".join([f"- {t}" for t in trends[: max(0, num_trends)]])
    
    sections = []
    if include_intro:
        sections.append("Include: Intro")
    if include_links:
        sections.append("Curated Links")
    if include_trends:
        sections.append("Trends to Watch")
    
    prompt = f"""
You are writing a curated newsletter for {creator_name}.
Use their writing style from samples and summarize top 5 insights.
Include: {', '.join(sections)}.
Return markdown text.

STYLE SAMPLES (verbatim):
{style_text}

CONTENT CANDIDATES (title and URL):
{curated_block}

TRENDS TO CONSIDER (optional):
{trends_lines}
""".strip()
    return prompt


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def generate_draft(style_samples: List[str], content_items: List[Dict[str, Any]], creator_name: str = "the creator", temperature: float = 0.7, num_links: int = 5, trends: List[str] | None = None, num_trends: int = 3, include_intro: bool = True, include_links: bool = True, include_trends: bool = True) -> str:
    import time
    start_time = time.time()
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback simple draft for local dev without key
        top_lines = "\n".join([f"- [{c.get('title','link')}]({c.get('url','')})" for c in content_items[: max(1, num_links)]])
        trends_lines = "\n".join([f"- {t}" for t in (trends or [])[: max(0, num_trends)]])
        return f"""
### Intro
Here's your curated daily pulse, tailored to your style.

### Curated Links
{top_lines}

### Trends to Watch
{trends_lines if trends_lines else '- AI-assisted creation workflows\n- Platform algorithm shifts\n- Audience retention strategies'}
""".strip()

    try:
        # Lazy import to avoid hard dependency when key missing
        from groq import Groq
    except Exception:
        # If groq SDK not available, return fallback
        top_lines = "\n".join([f"- [{c.get('title','link')}]({c.get('url','')})" for c in content_items[:5]])
        return f"""
### Intro
Here's your curated daily pulse, tailored to your style.

### Curated Links
{top_lines}

### Trends to Watch
- AI-assisted creation workflows
- Platform algorithm shifts
- Audience retention strategies
""".strip()

    client = Groq(api_key=api_key)
    prompt = _build_prompt(creator_name, style_samples, content_items, trends=trends, num_trends=num_trends, include_intro=include_intro, include_links=include_links, include_trends=include_trends)

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert newsletter writer who produces concise, insightful curation in clean Markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=max(0.0, min(1.0, temperature)),
        max_tokens=1200,
    )
    text = completion.choices[0].message.content
    
    # Track analytics
    generation_time_ms = int((time.time() - start_time) * 1000)
    tokens_used = completion.usage.total_tokens if completion.usage else 0
    
    # Calculate cost (rough estimate: $0.00059 per 1K tokens for Llama 3.1 8B)
    cost_cents = int((tokens_used / 1000) * 0.00059 * 100)
    
    try:
        from services.analytics_service import track_api_call, track_draft_generation
        from services.supabase_client import get_current_user
        import streamlit as st
        
        user = get_current_user()
        if user:
            current_workspace = st.session_state.get("current_workspace")
            workspace_id = current_workspace["workspace_id"] if current_workspace else None
            
            if workspace_id:
                track_api_call(
                    user_id=user["id"],
                    workspace_id=workspace_id,
                    api_provider="groq",
                    endpoint="chat_completions",
                    tokens_used=tokens_used,
                    cost_cents=cost_cents
                )
                
                track_draft_generation(
                    user_id=user["id"],
                    workspace_id=workspace_id,
                    draft_length=len(text),
                    sources_used=len(content_items),
                    generation_time_ms=generation_time_ms
                )
    except Exception:
        # Analytics tracking is optional, don't fail the main function
        pass
    
    return text


