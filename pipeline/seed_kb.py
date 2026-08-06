"""Seed the site with articles rendered from the verified knowledge base.
Run once at setup; afterwards the pipeline keeps the site fresh."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from common import SITE_CONTENT, load_kb, log, read_json, write_json, STATE_DIR
from generate import frontmatter_yaml, kb_article, replace_tokens

PUBLISHED_PATH = STATE_DIR / "published.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="overwrite existing seeded articles")
    args = parser.parse_args()

    kb = load_kb()
    published = read_json(PUBLISHED_PATH, {})
    published = published if isinstance(published, dict) else {}
    now = datetime.now(timezone.utc)
    written = 0

    for i, entry in enumerate(kb):
        article = kb_article(entry)
        slug = article["slug"]
        path = SITE_CONTENT / f"{slug}.md"
        if path.exists() and not args.refresh:
            log(f"skip (exists): {slug}")
            continue

        published_at = (now - timedelta(days=len(kb) - i)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        last_verified = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        fm = dict(article["frontmatter"])
        fm.update(
            {
                "publishedAt": published_at,
                "lastVerified": last_verified,
                "confidence": "kb",
                "related": [],
                "trendingScore": 60.0,
            }
        )
        content = frontmatter_yaml(fm) + "\n" + replace_tokens(article["body"]).strip() + "\n"
        path.write_text(content, encoding="utf-8")
        published[slug] = {
            "niche": fm["niche"],
            "published_at": published_at,
            "published_ts": now.timestamp(),
            "last_verified_at": last_verified,
            "last_verified_ts": now.timestamp(),
            "path": str(path),
        }
        log(f"seeded: {slug}")
        written += 1

    write_json(PUBLISHED_PATH, published)
    log(f"seed complete: {written} articles written, {len(kb)} in KB")


if __name__ == "__main__":
    main()
