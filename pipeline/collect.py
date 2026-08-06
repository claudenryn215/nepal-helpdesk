"""Collect raw signals from Reddit, RSS feeds, and Google News RSS."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

from common import STATE_DIR, load_sources, log, now_iso, read_json, write_json

RAW_PATH = STATE_DIR / "raw_posts.jsonl"
SEEN_PATH = STATE_DIR / "seen_ids.json"
REDDIT_TOKEN_PATH = STATE_DIR / "reddit_token.json"

UA = {"User-Agent": "nepal-helpdesk/1.0 (community troubleshooting monitor)"}


def _reddit_headers() -> dict:
    """Return headers for Reddit; uses OAuth when credentials exist."""
    headers = dict(UA)
    client_id = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    username = os.environ.get("REDDIT_USERNAME", "")
    password = os.environ.get("REDDIT_PASSWORD", "")
    if not (client_id and client_secret and username and password):
        return headers

    cached = read_json(REDDIT_TOKEN_PATH, {})
    cached = cached if isinstance(cached, dict) else {}
    token = cached.get("access_token", "")
    if cached.get("expires_at", 0) > time.time() + 60:
        headers["Authorization"] = f"Bearer {token}"
        return headers

    try:
        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(client_id, client_secret),
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
            },
            headers={"User-Agent": UA["User-Agent"]},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        write_json(
            REDDIT_TOKEN_PATH,
            {
                "access_token": data["access_token"],
                "expires_at": time.time() + int(data.get("expires_in", 3600)),
            },
        )
        headers["Authorization"] = f"Bearer {data['access_token']}"
        log("reddit OAuth token refreshed")
    except (requests.RequestException, ValueError, KeyError) as exc:
        log(f"reddit OAuth failed (falling back to anonymous): {exc}")
        headers.pop("Authorization", None)
    return headers


def _dedupe_id(source: str, key: str) -> bool:
    seen = read_json(SEEN_PATH, {})
    if isinstance(seen, dict) and seen.get(f"{source}:{key}"):
        return False
    seen = seen if isinstance(seen, dict) else {}
    seen[f"{source}:{key}"] = now_iso()
    write_json(SEEN_PATH, seen)
    return True


def _append_post(post: dict) -> None:
    with open(RAW_PATH, "a", encoding="utf-8") as fh:
        fh.write(__import__("json").dumps(post, ensure_ascii=False) + "\n")


def _clean(text: str, limit: int = 400) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def collect_reddit(cfg: dict) -> int:
    base = cfg.get("base_url", "https://www.reddit.com")
    headers = _reddit_headers()
    count = 0

    for sub in cfg.get("subreddits", []):
        url = f"{base}/r/{sub}/new.json?limit={cfg.get('per_subreddit_new', 40)}"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code in (403, 429):
                log(f"Reddit rate-limited on r/{sub}; sleeping 30s")
                time.sleep(30)
                continue
            resp.raise_for_status()
            children = resp.json()["data"]["children"]
            for child in children:
                data = child.get("data", {})
                if data.get("stickied"):
                    continue
                key = data.get("id", "")
                if not key or not _dedupe_id("reddit", key):
                    continue
                _append_post(
                    {
                        "source": f"reddit/r/{sub}",
                        "id": key,
                        "title": data.get("title", ""),
                        "url": f"https://www.reddit.com{data.get('permalink', '')}",
                        "text": _clean(data.get("selftext", "")),
                        "score": int(data.get("score", 0) or 0),
                        "comments": int(data.get("num_comments", 0) or 0),
                        "created_utc": float(data.get("created_utc", 0) or 0),
                        "collected_at": now_iso(),
                    }
                )
                count += 1
        except (requests.RequestException, ValueError, KeyError) as exc:
            log(f"Reddit r/{sub} failed: {exc}")
        time.sleep(1.5)

    for keyword in cfg.get("search_keywords", []):
        url = f"{base}/search.json?q={requests.utils.quote(keyword)}&sort=new&limit={cfg.get('search_limit', 25)}&restrict_sr=&t=week"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code in (403, 429):
                time.sleep(5)
                continue
            resp.raise_for_status()
            children = resp.json()["data"]["children"]
            for child in children:
                data = child.get("data", {})
                key = data.get("id", "")
                if not key or not _dedupe_id("reddit-search", key):
                    continue
                _append_post(
                    {
                        "source": f"reddit-search:{keyword}",
                        "id": key,
                        "title": data.get("title", ""),
                        "url": f"https://www.reddit.com{data.get('permalink', '')}",
                        "text": _clean(data.get("selftext", "")),
                        "score": int(data.get("score", 0) or 0),
                        "comments": int(data.get("num_comments", 0) or 0),
                        "created_utc": float(data.get("created_utc", 0) or 0),
                        "collected_at": now_iso(),
                    }
                )
                count += 1
        except (requests.RequestException, ValueError, KeyError) as exc:
            log(f"Reddit search '{keyword}' failed: {exc}")
        time.sleep(1.5)

    return count


def collect_rss(feeds: list[dict]) -> int:
    count = 0
    for feed in feeds:
        name, url = feed.get("name", "feed"), feed.get("url", "")
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:20]:
                key = entry.get("id") or entry.get("link") or entry.get("title", "")
                if not key or not _dedupe_id(name, key):
                    continue
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                created = datetime(*published[:6], tzinfo=timezone.utc).timestamp() if published else 0
                _append_post(
                    {
                        "source": f"rss/{name}",
                        "id": key,
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "text": _clean(entry.get("summary", "")),
                        "score": 0,
                        "comments": 0,
                        "created_utc": created,
                        "collected_at": now_iso(),
                    }
                )
                count += 1
        except Exception as exc:  # feedparser is forgiving; still guard
            log(f"RSS {name} failed: {exc}")
    return count


def collect_google_news(cfg: dict) -> int:
    base = cfg.get("base_url", "https://news.google.com/rss/search")
    when = cfg.get("when", "7d")
    count = 0
    for keyword in cfg.get("keywords", []):
        query = f"{keyword} when:{when}"
        url = f"{base}?q={requests.utils.quote(query)}&hl=en&gl=NP&ceid=NP:en"
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[: cfg.get("limit", 15)]:
                key = entry.get("id") or entry.get("link") or entry.get("title", "")
                if not key or not _dedupe_id("gnews", key):
                    continue
                published = entry.get("published_parsed")
                created = datetime(*published[:6], tzinfo=timezone.utc).timestamp() if published else 0
                _append_post(
                    {
                        "source": f"gnews:{keyword}",
                        "id": key,
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "text": _clean(entry.get("summary", "")),
                        "score": 0,
                        "comments": 0,
                        "created_utc": created,
                        "collected_at": now_iso(),
                    }
                )
                count += 1
        except Exception as exc:
            log(f"Google News '{keyword}' failed: {exc}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="clear raw store before collecting")
    args = parser.parse_args()

    if args.reset and RAW_PATH.exists():
        RAW_PATH.unlink()
        log("cleared raw_posts.jsonl")

    cfg = load_sources()
    n = 0
    n += collect_reddit(cfg.get("reddit", {}))
    n += collect_rss(cfg.get("rss", []))
    n += collect_google_news(cfg.get("google_news", {}))
    log(f"collected {n} new posts")


if __name__ == "__main__":
    main()
