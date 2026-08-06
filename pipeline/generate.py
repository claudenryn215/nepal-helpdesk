"""Generate article drafts from knowledge-base entries or LLM verdicts."""
from __future__ import annotations

import re

import yaml

from common import load_affiliates, load_ads, load_kb, log, now_iso, slugify
from llm import LLMUnavailable, chat_json

TOKEN_RE = re.compile(r"\{\{(affiliate|ad):([^}|]+)(?:\|([^}]*))?\}\}")

DRAFT_PROMPT = """You are a technical writer for NepalHelpDesk, a mobile-first troubleshooting
site for Nepal. Write a clear, beginner-friendly how-to article.

Topic (from Nepali online communities):
{title}
Context:
{context}

Requirements:
1. Reply ONLY with JSON:
{{"title": "...", "description": "...", "keywords": [...], "summary": [{{"problem": "...", "cause": "...", "fix": "..."}}], "body": "markdown", "sources": ["https://..."]}}
2. summary must have 3-4 rows. Every cell under 160 characters. No "|" characters inside cells.
3. body is markdown with:
   - a "## Quick Answers" table (same rows as summary)
   - 4-6 numbered steps, each a heading exactly like "## Step 1: <name>" followed by numbered sub-steps or bullets
   - a "## Troubleshooting" table (problem / cause / fix)
   - a "## FAQ" section with "**Q:** ..." / "**A:** ..." pairs (3 questions)
   - include the exact marker {{ad:in-article-1}} after the first step and {{ad:in-article-2}} before the FAQ
   - include the exact marker {{affiliate:darax|q=<english product phrase>}} once, near the end
4. Steps must be factual and conservative. Do NOT invent phone numbers, fees, or URLs.
5. keywords: 4-6 English and Nepali (Devanagari) search phrases.
6. sources: only well-known official URLs (e.g. worldlink.com.np, esewa.com.np, khalti.com, nagarikapp.gov.np, register.com.np, daraz.com.np) relevant to the fix; if none apply, use [].
7. description: one sentence, 120-160 characters, containing the main search phrase.
8. Language: English body with occasional Nepali terms.
"""


def _affiliate_html(key: str, query: str) -> str:
    affiliates = load_affiliates()
    entry = affiliates.get(key)
    if not entry:
        return ""
    url = entry.get("url_template", "").replace("{q}", query.replace(" ", "+"))
    label = entry.get("label", "Buy")
    rel = entry.get("rel", "sponsored nofollow")
    return (
        '\n<div class="affiliate-box">\n'
        f'<p><strong>Related product check</strong></p>\n'
        f'<p><a href="{url}" rel="{rel}" target="_blank">{label}</a></p>\n'
        "</div>\n"
    )


def _ad_html(slot: str) -> str:
    ads = load_ads()
    slot_cfg = (ads.get("slots") or {}).get(slot)
    label = slot_cfg.get("label", f"Ad Slot {slot}") if slot_cfg else f"Ad Slot {slot}"
    height = slot_cfg.get("min_height_px", 90) if slot_cfg else 90
    return (
        f'\n<div class="ad-slot" style="min-height:{height}px">'
        f"{label} — advertising placeholder</div>\n"
    )


def replace_tokens(text: str) -> str:
    def _repl(match: re.Match) -> str:
        kind, name, rest = match.group(1), match.group(2), match.group(3)
        if kind == "affiliate":
            query = rest or name
            return _affiliate_html(name, query)
        if kind == "ad":
            return _ad_html(name)
        return ""

    return TOKEN_RE.sub(_repl, text)


def frontmatter_yaml(data: dict) -> str:
    out = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=200,
    )
    return f"---\n{out}---\n"


def kb_article(entry: dict) -> dict:
    """Render a knowledge-base entry into a draft article dict."""
    slug = slugify(entry.get("id", entry.get("title", "")))
    body_parts: list[str] = []

    rows = "".join(
        f"| {_esc(r['problem'])} | {_esc(r['cause'])} | {_esc(r['fix'])} |\n"
        for r in entry.get("summary", [])
    )
    body_parts.append("## Quick Answers\n\n| Problem | Common cause | Fix |\n| --- | --- | --- |\n" + rows)

    for i, step in enumerate(entry.get("steps", []), start=1):
        body_parts.append(f"## Step {i}: {step['title']}\n\n{step['body'].strip()}")
        if i == 1:
            body_parts.append("{{ad:in-article-1}}")

    if entry.get("troubleshooting"):
        t_rows = "".join(
            f"| {_esc(r['problem'])} | {_esc(r['cause'])} | {_esc(r['fix'])} |\n"
            for r in entry["troubleshooting"]
        )
        body_parts.append("## Troubleshooting\n\n| Problem | Cause | Fix |\n| --- | --- | --- |\n" + t_rows)

    if entry.get("affiliate") and entry["affiliate"] != "none":
        key, _, query = entry["affiliate"].partition("|")
        body_parts.append(f"{{{{affiliate:{key}|q={query}}}}}")
    body_parts.append("{{ad:in-article-2}}")

    if entry.get("faq"):
        faq_lines = ["## FAQ", ""]
        for item in entry["faq"]:
            faq_lines.append(f"**Q:** {item['q']}\n\n**A:** {item['a']}\n")
        body_parts.append("\n".join(faq_lines))

    return {
        "slug": slug,
        "frontmatter": {
            "title": entry["title"],
            "description": entry["description"],
            "keywords": entry.get("keywords", []),
            "tags": entry.get("tags", []),
            "niche": entry.get("niche", "general"),
            "sources": entry.get("sources", []),
            "summary": entry.get("summary", []),
        },
        "body": "\n\n".join(body_parts) + "\n",
    }


def llm_article(verified: dict) -> dict:
    """Ask the LLM to draft a full article; validates the structure."""
    try:
        result = chat_json(
            [
                {"role": "system", "content": DRAFT_PROMPT.format(
                    title=verified["title"], context=verified["rationale"])},
                {"role": "user", "content": "Write the article JSON now."},
            ],
            max_tokens=4000,
            temperature=0.5,
        )
    except (LLMUnavailable, ValueError) as exc:
        raise GenerationError(f"LLM draft failed: {exc}") from exc

    title = str(result.get("title", "")).strip()
    body = str(result.get("body", "")).strip()
    summary = result.get("summary", [])
    description = str(result.get("description", "")).strip()
    sources = [s for s in result.get("sources", []) if isinstance(s, str) and s.startswith("http")]

    if not (30 <= len(title) <= 150):
        raise GenerationError(f"bad title length: {title[:80]}")
    if len(body) < 400:
        raise GenerationError("draft body too short")
    if len(re.findall(r"^## Step \d+[.:]", body, flags=re.M)) < 3:
        raise GenerationError("fewer than 3 steps in draft")
    if not isinstance(summary, list) or len(summary) < 3:
        raise GenerationError("summary table missing")

    keywords = [k for k in result.get("keywords", []) if isinstance(k, str)][:8]
    slug = slugify(title)

    return {
        "slug": slug,
        "frontmatter": {
            "title": title,
            "description": description,
            "keywords": keywords,
            "tags": [],
            "niche": verified["niche"],
            "sources": sources,
            "summary": [
                {
                    "problem": str(r.get("problem", ""))[:200],
                    "cause": str(r.get("cause", ""))[:200],
                    "fix": str(r.get("fix", ""))[:200],
                }
                for r in summary
                if isinstance(r, dict)
            ],
        },
        "body": body,
    }


def _esc(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


class GenerationError(Exception):
    pass
