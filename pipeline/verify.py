"""Confidence gate: match topics against the knowledge base; otherwise ask
the LLM for a verified verdict (high / medium / reject)."""
from __future__ import annotations

import argparse

from common import STATE_DIR, load_kb, log, read_json, token_overlap, write_json
from llm import LLMUnavailable, available as llm_available, chat_json

TRENDING_PATH = STATE_DIR / "trending.json"
VERIFIED_PATH = STATE_DIR / "verified.json"

VERIFIER_PROMPT = """You are the accuracy verifier for a Nepali tech troubleshooting website.

A trending community topic is described below. Decide whether we can publish a
verified how-to article about it. Rules:
- "high" only when the fix is standard, stable, and you are confident it works
  (e.g. restart router, clear cache, official portal steps). Do not hallucinate
  phone numbers, prices, or URLs you are not sure about.
- "medium" when the topic is real and fixable but details vary.
- "reject" when the topic is not a technical problem, is about a private
  business matter, or you cannot produce reliable steps.

Respond ONLY with JSON:
{"confidence": "high"|"medium"|"reject", "title": "...", "description": "...", "keywords": ["..."], "rationale": "..."}

Topic niche: {niche}
Community posts:
{titles}
"""


def _kb_entry_match(topic: dict, kb: list[dict]) -> dict | None:
    topic_tokens = [w for w in topic.get("keywords", [])]
    best: dict | None = None
    best_score = 0.0
    for entry in kb:
        entry_tokens = list(entry.get("keywords", [])) + list(entry.get("tags", []))
        entry_tokens += [w for w in entry.get("title", "").lower().replace("-", " ").split() if len(w) > 3]
        score = token_overlap(topic_tokens, entry_tokens)
        title_hint = topic.get("title_hint", "")
        if any(kw in title_hint.lower() for kw in entry.get("keywords", [])[:6]):
            score += 0.3
        if score > best_score:
            best_score = score
            best = entry
    if best and best_score >= 0.5:
        return best
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true", help="never call the LLM (KB matches only)")
    args = parser.parse_args()

    trending = read_json(TRENDING_PATH, [])
    if not trending:
        log("no trending topics to verify")
        write_json(VERIFIED_PATH, [])
        return

    kb = load_kb()
    use_llm = llm_available() and not args.no_llm
    if not use_llm:
        log("LLM unavailable — KB matches only; everything else goes to pending")

    verified = []
    for topic in trending:
        kb_entry = _kb_entry_match(topic, kb)
        if kb_entry:
            verified.append(
                {
                    "topic_id": topic["topic_id"],
                    "niche": topic["niche"],
                    "confidence": "kb",
                    "generation": "kb",
                    "kb_entry": kb_entry,
                    "title": kb_entry["title"],
                    "description": kb_entry["description"],
                    "keywords": kb_entry["keywords"],
                    "urls": topic["urls"],
                    "rationale": "Matches verified knowledge-base entry: " + kb_entry["id"],
                }
            )
            log(f"[{topic['topic_id']}] KB match -> {kb_entry['id']}")
            continue

        if not use_llm:
            verified.append(
                {
                    "topic_id": topic["topic_id"],
                    "niche": topic["niche"],
                    "confidence": "reject",
                    "generation": "pending",
                    "kb_entry": None,
                    "title": topic["title_hint"],
                    "description": "",
                    "keywords": topic["keywords"],
                    "urls": topic["urls"],
                    "rationale": "No KB match and LLM unavailable — queued for later review",
                }
            )
            continue

        titles = "\n".join(f"- {t}" for t in [topic["title_hint"]])
        try:
            verdict = chat_json(
                [
                    {
                        "role": "system",
                        "content": VERIFIER_PROMPT.format(
                            niche=topic["niche"], titles=titles
                        ),
                    },
                    {"role": "user", "content": "Produce the JSON verdict."},
                ],
                max_tokens=600,
                temperature=0.2,
            )
        except (LLMUnavailable, ValueError) as exc:
            log(f"[{topic['topic_id']}] LLM verification failed: {exc}")
            verified.append(
                {
                    "topic_id": topic["topic_id"],
                    "niche": topic["niche"],
                    "confidence": "reject",
                    "generation": "pending",
                    "kb_entry": None,
                    "title": topic["title_hint"],
                    "description": "",
                    "keywords": topic["keywords"],
                    "urls": topic["urls"],
                    "rationale": "LLM verification failed — queued for later review",
                }
            )
            continue

        confidence = verdict.get("confidence")
        if confidence not in ("high", "medium", "reject"):
            confidence = "reject"
        verified.append(
            {
                "topic_id": topic["topic_id"],
                "niche": topic["niche"],
                "confidence": confidence,
                "generation": "llm" if confidence == "high" else "pending",
                "kb_entry": None,
                "title": verdict.get("title", topic["title_hint"]),
                "description": verdict.get("description", ""),
                "keywords": [k for k in verdict.get("keywords", []) if isinstance(k, str)],
                "urls": topic["urls"],
                "rationale": verdict.get("rationale", ""),
            }
        )
        log(f"[{topic['topic_id']}] LLM verdict -> {confidence}")

    write_json(VERIFIED_PATH, verified)
    log(f"verified {len(verified)} topics "
        f"({sum(1 for v in verified if v['confidence'] == 'kb')} kb, "
        f"{sum(1 for v in verified if v['confidence'] == 'high')} high, "
        f"{sum(1 for v in verified if v['confidence'] == 'medium')} medium, "
        f"{sum(1 for v in verified if v['confidence'] == 'reject')} reject)")


if __name__ == "__main__":
    main()
