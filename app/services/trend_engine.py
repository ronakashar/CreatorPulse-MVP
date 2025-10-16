from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import re


_STOPWORDS = set(
    "the a an and or for to of in on at by with from is are was were be been being this that those these it its as about into your you our we their his her they i".split()
)


def _tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s#]", " ", text)
    tokens = [t for t in text.split() if t and t not in _STOPWORDS]
    return tokens


def _extract_terms(item: Dict) -> List[str]:
    title = item.get("title", "") or ""
    summary = item.get("summary", "") or ""
    tokens = _tokenize(title) + _tokenize(summary)
    # Keep hashtags and long keywords
    terms = [t for t in tokens if t.startswith("#") or len(t) >= 4]
    return terms


def compute_trends(items: List[Dict], now: datetime | None = None) -> List[Tuple[str, float]]:
    """Compute simple spike trends from recent content items.

    Heuristic:
    - Split into two windows: last 48h (recent) vs prior 5 days (baseline)
    - Score(term) = freq_recent - 0.5 * freq_baseline
    - Return top terms with positive scores
    """
    if not items:
        return []
    now = now or datetime.now(timezone.utc)
    recent_cut = now - timedelta(hours=48)
    baseline_cut = now - timedelta(days=7)

    recent_counter: Counter[str] = Counter()
    baseline_counter: Counter[str] = Counter()

    for it in items:
        created_at = it.get("created_at")
        # Parse timestamp and make timezone-aware
        try:
            if isinstance(created_at, str):
                # Handle both ISO format with Z and without
                if created_at.endswith('Z'):
                    dt = datetime.fromisoformat(created_at[:-1] + '+00:00')
                elif '+' in created_at:
                    dt = datetime.fromisoformat(created_at)
                else:
                    # Assume UTC if no timezone info
                    dt = datetime.fromisoformat(created_at)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = None
        except Exception:
            dt = None
            
        terms = _extract_terms(it)
        if dt and dt >= recent_cut:
            recent_counter.update(terms)
        elif dt and dt >= baseline_cut:
            baseline_counter.update(terms)
        else:
            # Out of window: treat as baseline light
            baseline_counter.update(terms)

    scores: Dict[str, float] = {}
    all_terms = set(list(recent_counter.keys()) + list(baseline_counter.keys()))
    for term in all_terms:
        r = recent_counter.get(term, 0)
        b = baseline_counter.get(term, 0)
        score = float(r) - 0.5 * float(b)
        if score > 0:
            scores[term] = score

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:10]



