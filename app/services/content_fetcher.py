from typing import List, Dict, Any

from .supabase_client import list_sources, save_content_items


def _normalize_twitter(value: str) -> str:
    v = (value or "").strip()
    if v.startswith("http"):
        v = v.replace("https://x.com/", "").replace("http://x.com/", "")
        v = v.replace("https://twitter.com/", "").replace("http://twitter.com/", "")
        v = v.split("/")[0]
    if v.startswith("@"):
        v = v[1:]
    return v


def _fetch_twitter(handle_or_url: str) -> List[Dict[str, Any]]:
    handle = _normalize_twitter(handle_or_url)
    items: List[Dict[str, Any]] = []

    # Primary: snscrape
    try:
        import snscrape.modules.twitter as sntwitter  # type: ignore
        for i, tweet in enumerate(sntwitter.TwitterUserScraper(handle).get_items()):
            if i >= 10:
                break
            items.append({
                "title": getattr(tweet, "content", "Tweet"),
                "url": f"https://x.com/{handle}/status/{getattr(tweet, 'id', '')}",
                "summary": getattr(tweet, "content", ""),
            })
    except Exception:
        pass

    if items:
        return items

    # Fallback: try multiple Nitter RSS mirrors
    nitter_hosts = [
        "https://nitter.net",
        "https://nitter.poast.org",
        "https://nitter.fdn.fr",
        "https://ntrqq.com",
    ]
    for host in nitter_hosts:
        try:
            import feedparser  # type: ignore
            rss = f"{host}/{handle}/rss"
            feed = feedparser.parse(rss)
            if getattr(feed, "entries", None):
                for e in feed.entries[:10]:
                    items.append({
                        "title": getattr(e, "title", "Tweet"),
                        "url": getattr(e, "link", ""),
                        "summary": getattr(e, "summary", ""),
                    })
                break
        except Exception:
            continue

    # Last-resort fallback: fetch Nitter HTML via r.jina.ai proxy and parse status IDs
    if not items:
        try:
            import re
            import requests  # type: ignore
            nitter_hosts = [
                "nitter.net",
                "nitter.poast.org",
                "nitter.fdn.fr",
                "ntrqq.com",
            ]
            status_ids = []
            for host in nitter_hosts:
                proxy_url = f"https://r.jina.ai/http://{host}/{handle}"
                resp = requests.get(proxy_url, timeout=10)
                if resp.status_code >= 400:
                    continue
                found = re.findall(r"status/(\d+)", resp.text)
                if found:
                    status_ids = list(dict.fromkeys(found))  # dedupe, preserve order
                    break
            for sid in status_ids[:10]:
                items.append({
                    "title": "Tweet",
                    "url": f"https://x.com/{handle}/status/{sid}",
                    "summary": "",
                })
        except Exception:
            pass

    return items


def _fetch_youtube(channel_url: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    # Accept channel feed URLs directly
    if "feeds/videos.xml" in channel_url:
        try:
            import feedparser  # type: ignore
            feed = feedparser.parse(channel_url)
            for e in feed.entries[:10]:
                items.append({
                    "title": getattr(e, "title", "Video"),
                    "url": getattr(e, "link", ""),
                    "summary": getattr(e, "summary", ""),
                })
            return items
        except Exception:
            return items

    # Otherwise, try yt_dlp on channel/@handle URLs
    try:
        import yt_dlp  # type: ignore
    except Exception:
        return items
    ydl_opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    url = channel_url
    if "youtube.com/@" in url and "/videos" not in url:
        url = url.rstrip("/") + "/videos"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(url, download=False)
            entries = info.get("entries", []) if isinstance(info, dict) else []
            for e in entries[:10]:
                video_id = e.get("id") or e.get("url")
                items.append({
                    "title": e.get("title", "Video"),
                    "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else e.get("webpage_url", ""),
                    "summary": e.get("description", ""),
                })
    except Exception:
        pass
    return items


def _fetch_rss(feed_url: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    try:
        import feedparser  # type: ignore
    except Exception:
        return items
    try:
        feed = feedparser.parse(feed_url)
        for e in feed.entries[:10]:
            items.append({
                "title": getattr(e, "title", "Article"),
                "url": getattr(e, "link", ""),
                "summary": getattr(e, "summary", ""),
            })
    except Exception:
        pass
    return items


def fetch_all_sources(*, user_id: str, workspace_id: str = None) -> int:
    sources = list_sources(user_id=user_id, workspace_id=workspace_id)
    collected: List[Dict[str, Any]] = []
    for s in sources:
        stype = s.get("source_type")
        sval = s.get("source_value", "")
        boost_factor = s.get("boost_factor", 1.0)
        subitems: List[Dict[str, Any]] = []
        if stype == "twitter":
            subitems = _fetch_twitter(sval)
        elif stype == "youtube":
            subitems = _fetch_youtube(sval)
        elif stype == "rss":
            subitems = _fetch_rss(sval)
        
        # Apply boost factor by duplicating items
        boosted_items = []
        for it in subitems:
            it["source_id"] = s.get("id")
            it["workspace_id"] = workspace_id
            # Duplicate items based on boost factor
            num_copies = max(1, int(boost_factor))
            for _ in range(num_copies):
                boosted_items.append(dict(it))
        
        collected.extend(boosted_items)

    return save_content_items(user_id=user_id, items=collected, workspace_id=workspace_id)


