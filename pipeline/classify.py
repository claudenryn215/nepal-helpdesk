"""Classify raw posts into niches and compute trending topic clusters."""
from __future__ import annotations

import math
import re
import time
from collections import Counter
from datetime import datetime, timezone

from common import (
    STATE_DIR,
    load_niches,
    load_sources,
    log,
    published_slugs,
    read_json,
    slugify,
    token_overlap,
    write_json,
)

RAW_PATH = STATE_DIR / "raw_posts.jsonl"
TRENDING_PATH = STATE_DIR / "trending.json"
PUBLISHED_PATH = STATE_DIR / "published.json"

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on", "for",
    "and", "or", "but", "with", "my", "me", "i", "not", "no", "how", "what",
    "why", "can", "cant", "do", "does", "did", "get", "got", "it", "this",
    "that", "help", "please", "need", "anyone", "someone", "hi", "hello",
}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def _niche_of(title: str, text: str, niches_cfg: dict, keywords_by_niche: dict) -> str:
    blob = " ".join([title, text]).lower()
    scores = {}
    for niche, data in keywords_by_niche.items():
        scores[niche] = sum(1 for kw in data if kw in blob)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def _is_excluded(title: str, text: str, exclude_terms: list[str]) -> bool:
    blob = f"{title} {text}".lower()
    return any(term in blob for term in exclude_terms)


def _cluster_posts(posts: list[dict], keywords_by_niche: dict) -> list[dict]:
    clusters: list[dict] = []
    for post in posts:
        title_tokens = set(_tokens(post["title"]))
        blob = f"{post['title']} {post['text']}".lower()
        matched = {kw for kw in sum(keywords_by_niche.values(), []) if kw in blob}
        placed = False
        for cluster in clusters:
            cluster_keywords = set(cluster["keywords"])
            shared = matched & cluster_keywords
            title_overlap = token_overlap(list(title_tokens), list(cluster["title_tokens"]))
            if len(shared) >= 2 or title_overlap >= 0.4:
                cluster["keywords"] = sorted(cluster_keywords | matched)
                cluster["title_tokens"] = sorted(set(cluster["title_tokens"]) | title_tokens)
                cluster["posts"].append(post)
                placed = True
                break
        if not placed:
            clusters.append(
                {
                    "keywords": sorted(matched),
                    "title_tokens": sorted(title_tokens),
                    "posts": [post],
                }
            )
    return clusters


def _score_cluster(cluster: dict, cfg: dict, now: float) -> float:
    posts = cluster["posts"]
    mentions = len(posts)
    half_life = cfg.get("recency_half_life_hours", 72) * 3600
    newest = max(p["created_utc"] or 0 for p in posts)
    age = max(0.0, now - newest)
    recency = math.exp(-age / half_life)
    avg_engagement = sum(p["score"] + 2 * p["comments"] for p in posts) / mentions
    engagement = math.log1p(avg_engagement) / 8.0
    mention_score = min(1.0, mentions / cfg.get("min_mentions", 2))
    score = (
        cfg.get("engagement_weight", 0.4) * engagement
        + cfg.get("mention_weight", 0.35) * mention_score
        + cfg.get("recency_weight", 0.25) * recency
    )
    return score


def _dedupe_against_site(title: str) -> bool:
    """True when a similar article already exists on the site (or is queued)."""
    tokens = set(_tokens(title))
    for slug in published_slugs():
        if token_overlap(tokens, set(slug.split("-"))) >= 0.6:
            return True
    pub = read_json(PUBLISHED_PATH, {})
    if isinstance(pub, dict):
        for slug, meta in pub.items():
            if isinstance(meta, dict) and token_overlap(tokens, set(slug.split("-"))) >= 0.6:
                return True
    return False


def main() -> None:
    if not RAW_PATH.exists():
        log("no raw posts yet — run collect.py first")
        return

    now = time.time()
    week_ago = now - 7 * 86400
    niches_cfg = load_niches()
    sources_cfg = load_sources()

    keywords_by_niche = {
        niche: [kw.lower() for kw in data.get("keywords", [])]
        for niche, data in niches_cfg.get("niches", {}).items()
    }
    exclude_terms = niches_cfg.get("exclude_terms", [])
    trend_cfg = niches_cfg.get("trending", {})

    posts = []
    with open(RAW_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                post = __import__("json").loads(line)
            except ValueError:
                continue
            created = float(post.get("created_utc", 0) or 0)
            if created and created < week_ago:
                continue
            post["_created"] = created if created else now
            posts.append(post)

    if not posts:
        log("no posts in the 7-day window")
        write_json(TRENDING_PATH, [])
        return

    candidates = [
        p for p in posts
        if not _is_excluded(p["title"], p["text"], exclude_terms)
        and not _dedupe_against_site(p["title"])
    ]
    for p in candidates:
        p["niche"] = _niche_of(p["title"], p["text"], niches_cfg, keywords_by_niche)

    clusters = _cluster_posts(candidates, keywords_by_niche)
    scored: list[dict] = []
    for cluster in clusters:
        if len(cluster["posts"]) < trend_cfg.get("min_mentions", 2):
            continue
        cluster["score"] = _score_cluster(cluster, trend_cfg, now)
        cluster["niche"] = Counter(p["niche"] for p in cluster["posts"]).most_common(1)[0][0]
        cluster["posts"].sort(key=lambda p: p["_created"], reverse=True)
        top = cluster["posts"][0]
        cluster["title_hint"] = re.sub(r"\s+", " ", top["title"]).strip()[:110]
        cluster["urls"] = [p["url"] for p in cluster["posts"][:5]]
        scored.append(cluster)

    scored.sort(key=lambda c: c["score"], reverse=True)
    top = scored[: trend_cfg.get("top_n", 5)]

    result = []
    for i, cluster in enumerate(top):
        result.append(
            {
                "topic_id": f"topic-{int(now)}-{i}",
                "niche": cluster["niche"],
                "score": round(cluster["score"], 4),
                "mentions": len(cluster["posts"]),
                "keywords": cluster["keywords"][:12],
                "title_hint": cluster["title_hint"],
                "urls": cluster["urls"],
                "found_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )

    write_json(TRENDING_PATH, result)
    log(f"classified {len(posts)} posts, {len(scored)} clusters, top {len(result)} trending")


if __name__ == "__main__":
    main()
