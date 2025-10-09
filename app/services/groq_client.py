import os
from typing import List, Dict, Any

from tenacity import retry, stop_after_attempt, wait_exponential


def _build_prompt(creator_name: str, style_samples: List[str], content_items: List[Dict[str, Any]]) -> str:
    style_text = "\n\n".join(style_samples[:3]) if style_samples else ""
    curated_lines = []
    for item in content_items[:12]:
        curated_lines.append(f"- {item.get('title','')} — {item.get('url','')}")
    curated_block = "\n".join(curated_lines)
    prompt = f"""
You are writing a curated newsletter for {creator_name}.
Use their writing style from samples and summarize top 5 insights.
Include: Intro, Curated Links, Trends to Watch.
Return markdown text.

STYLE SAMPLES (verbatim):
{style_text}

CONTENT CANDIDATES (title and URL):
{curated_block}
""".strip()
    return prompt


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def generate_draft(style_samples: List[str], content_items: List[Dict[str, Any]], creator_name: str = "the creator", temperature: float = 0.7, num_links: int = 5) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback simple draft for local dev without key
        top_lines = "\n".join([f"- [{c.get('title','link')}]({c.get('url','')})" for c in content_items[: max(1, num_links)]])
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
    prompt = _build_prompt(creator_name, style_samples, content_items)

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
    return text


