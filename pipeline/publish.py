"""Publish drafts into the Astro content collection and update state."""
from __future__ import annotations

import re
import time

from common import (
    SITE_CONTENT,
    STATE_DIR,
    load_kb,
    log,
    now_iso,
    now_ts,
    read_json,
    slugify,
    write_json,
)
from generate import GenerationError, frontmatter_yaml, kb_article, llm_article, replace_tokens

DRAFTS_PATH = STATE_DIR / "drafts.json"
VERIFIED_PATH = STATE_DIR / "verified.json"
PUBLISHED_PATH = STATE_DIR / "published.json"
PENDING_PATH = STATE_DIR / "pending.json"

MAX_NEW_PER_RUN = 4
KB_REFRESH_DAYS = 90
NEW_ARTICLE_COOLDOWN_HOURS = 24


def _frontmatter_for(article: dict, verified: dict, now: str, is_new: bool) -> dict:
    fm = dict(article["frontmatter"])
    base = {
        "title": fm["title"],
        "description": fm["description"],
        "publishedAt": now,
        "lastVerified": now,
        "confidence": "kb" if verified["confidence"] == "kb" else "high",
        "niche": fm["niche"],
        "keywords": fm["keywords"],
        "tags": fm["tags"],
        "summary": fm["summary"],
        "sources": fm["sources"],
        "related": [],
        "trendingScore": round(float(verified.get("score", 50)), 1),
    }
    if not is_new:
        base["updatedAt"] = now
    return base


def _write_article(slug: str, frontmatter: dict, body: str) -> str:
    content = frontmatter_yaml(frontmatter) + "\n" + replace_tokens(body).strip() + "\n"
    path = SITE_CONTENT / f"{slug}.md"
    path.write_text(content, encoding="utf-8")
    return str(path)


def _attach_related(limit: int = 2) -> None:
    published = read_json(PUBLISHED_PATH, {})
    if not isinstance(published, dict):
        return
    for slug, meta in list(published.items()):
        if not isinstance(meta, dict):
            continue
        path = SITE_CONTENT / f"{slug}.md"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        niche_match = re.search(r"^niche:\s*(\S+)", text, flags=re.M)
        niche = niche_match.group(1) if niche_match else "general"
        candidates = [
            other
            for other, other_meta in published.items()
            if other != slug
            and isinstance(other_meta, dict)
            and other_meta.get("niche") == niche
            and other_meta.get("published_at")
        ]
        related = [c for c in candidates[:limit] if c != slug][:limit]
        if re.search(r"^related:\s*\[\]", text, flags=re.M):
            updated = re.sub(
                r"^related:\s*\[\]$",
                "related: [" + ", ".join(related) + "]" if related else "related: []",
                text,
                flags=re.M,
            )
            path.write_text(updated, encoding="utf-8")


def main() -> None:
    verified = read_json(VERIFIED_PATH, [])
    if not verified:
        log("nothing to publish")
        return

    published = read_json(PUBLISHED_PATH, {})
    published = published if isinstance(published, dict) else {}
    pending = read_json(PENDING_PATH, [])
    pending = pending if isinstance(pending, list) else []

    drafts: dict = {}
    now = now_iso()
    ts = now_ts()
    new_count = 0
    refreshed = 0
    skip_reason: dict[str, str] = {}

    for item in verified:
        topic_id = item["topic_id"]
        if item["generation"] == "pending":
            pending.append(
                {
                    "topic_id": topic_id,
                    "title": item.get("title", ""),
                    "niche": item.get("niche"),
                    "confidence": item.get("confidence"),
                    "rationale": item.get("rationale", ""),
                    "urls": item.get("urls", []),
                    "created_at": now,
                }
            )
            continue

        try:
            if item["generation"] == "kb":
                article = kb_article(item["kb_entry"])
            else:
                article = llm_article(item)
        except GenerationError as exc:
            log(f"[{topic_id}] generation failed -> pending: {exc}")
            pending.append(
                {
                    "topic_id": topic_id,
                    "title": item.get("title", ""),
                    "niche": item.get("niche"),
                    "confidence": item.get("confidence"),
                    "rationale": f"generation failed: {exc}",
                    "urls": item.get("urls", []),
                    "created_at": now,
                }
            )
            continue

        slug = article["slug"]
        existing = published.get(slug)

        if existing and isinstance(existing, dict):
            last_verified = float(existing.get("last_verified_ts", 0) or 0)
            if now_ts() - last_verified < KB_REFRESH_DAYS * 86400:
                skip_reason[slug] = "already published and recently verified"
                continue
            refreshed += 1
            is_new = False
            frontmatter = _frontmatter_for(article, item, now, is_new=False)
            frontmatter["publishedAt"] = existing.get("published_at", now)
        else:
            if new_count >= MAX_NEW_PER_RUN:
                skip_reason[slug] = "new-article cap reached for this run"
                continue
            if existing:
                pub_ts = float(existing.get("published_ts", 0) or 0)
                if now_ts() - pub_ts < NEW_ARTICLE_COOLDOWN_HOURS * 3600:
                    skip_reason[slug] = "published too recently (cooldown)"
                    continue
            new_count += 1
            is_new = True
            frontmatter = _frontmatter_for(article, item, now, is_new=True)

        path = _write_article(slug, frontmatter, article["body"])
        published[slug] = {
            "niche": frontmatter["niche"],
            "published_at": frontmatter["publishedAt"],
            "published_ts": ts,
            "last_verified_at": now,
            "last_verified_ts": ts,
            "path": str(path),
        }
        log(f"{'published' if is_new else 'refreshed'} article: {slug}")

    write_json(PUBLISHED_PATH, published)
    write_json(PENDING_PATH, pending)
    _attach_related()

    summary = f"publish done: {new_count} new, {refreshed} refreshed"
    if skip_reason:
        summary += f", skipped {len(skip_reason)}: " + "; ".join(sorted(set(skip_reason.values())))
    log(summary)


if __name__ == "__main__":
    main()
