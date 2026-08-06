"""Generate idempotent seed comments for published articles (D1 seed SQL)."""
from __future__ import annotations

import hashlib

from common import STATE_DIR, log, now_ts, read_json, write_json

PUBLISHED_PATH = STATE_DIR / "published.json"
SEEDED_PATH = STATE_DIR / "seeded.json"
SEED_SQL_PATH = STATE_DIR / "seed_comments.sql"

MIN_PER_POST = 2
MAX_PER_POST = 4

NAMES = [
    "Sujan Rai",
    "Asmita Joshi",
    "Krishna Poudel",
    "Bina Shrestha",
    "Dipesh Tamang",
    "Manisha K.C.",
    "Ujjwal Bhattarai",
    "Pooja Thapa",
    "Suresh Limbu",
    "Nisha Basnet",
    "Rahul Shah",
    "Sunita Gurung",
    "Aayush Karki",
    "Pratima Adhikari",
    "Nabin Maharjan",
]

NICHE_POOL: dict[str, list[str]] = {
    "isp": [
        "Same problem here since last week. Step 2 fixed it for me, thank you!",
        "My WorldLink router was doing exactly this. Followed the guide and it worked in 5 minutes.",
        "Worked on my Vianet connection too. Shared this with my brother who had the same issue.",
        "Reset worked but I had to redo my WiFi password. Worth mentioning.",
        "Thanks for this! The support line kept telling me to restart, this actually explains why.",
        "Tried it on my Subisu router, all good now. Bookmarked this page.",
    ],
    "e-gov": [
        "Finally got my Nagarik App working after a week of trying. Thank you!",
        "The date format was the issue all along. Can't believe it took me this long.",
        "This worked for my mum's phone too. Sharing it with everyone in the family group chat.",
        "OTP never arrived, your workaround sorted it. Appreciate the clear steps.",
        "Was stuck on this page for days, went through the steps twice and it worked.",
        "Worked perfectly on my new phone. Much clearer than the official instructions.",
    ],
    "fintech": [
        "eSewa support never explained it this clearly. Fixed in 2 minutes.",
        "Been stuck on this since last week. Easy to follow steps, worked on the first try.",
        "Khalti had the same issue for me. The fix here applies to both apps.",
        "Great guide. Balance updated right after the steps. Thanks a lot!",
        "Merchant setup was confusing until I followed this. Payout question also cleared up.",
        "Simple and straight to the point. Worked like a charm.",
    ],
    "ecommerce": [
        "As a new seller this was super helpful. The payout question is cleared up now.",
        "The Daraz dashboard changed last month, good to see an updated guide.",
        "Listing kept failing on my phone. Desktop steps in here fixed it.",
        "Thanks, got my first payout sorted. Explains things support never answers.",
        "Very practical guide for small sellers like me. Keep posting these!",
    ],
    "general": [
        "This solved my problem too. Thanks for writing it up.",
        "Finally a guide in simple language, not jargon. Bookmarked for later.",
        "Worked on my phone. Two minutes and done.",
        "Good one. Half the advice online is copy-paste, this one is actually tested.",
        "Had the same issue after an update. Fixed now, appreciate it.",
    ],
}

GENERIC_POOL = [
    "Same thing happened to me, this fixed it. Thanks!",
    "Easy to follow, worked on the first attempt. Bookmarked.",
    "Finally a clear explanation in simple language. Thank you.",
    "Shared this in a WhatsApp group for my office, a few people said it helped.",
    "Worked for me. Took a couple of tries but the guide was right.",
]

ALL_POOL = NICHE_POOL["general"] + GENERIC_POOL


def _pick(pool: list[str], key: str) -> str:
    idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(pool)
    return pool[idx]


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _iso(ts: float) -> str:
    return __import__("datetime").datetime.fromtimestamp(ts, __import__("datetime").timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )


def main() -> None:
    published = read_json(PUBLISHED_PATH, {})
    if not isinstance(published, dict) or not published:
        log("no published articles to seed")
        return

    seeded = read_json(SEEDED_PATH, [])
    seeded = seeded if isinstance(seeded, list) else []

    now = now_ts()
    rows: list[str] = []

    for slug, meta in sorted(published.items()):
        if slug in seeded:
            continue
        if not isinstance(meta, dict):
            continue
        niche = str(meta.get("niche", "general"))
        pub_ts = float(meta.get("published_ts", 0) or 0)
        if pub_ts <= 0:
            continue

        pool = NICHE_POOL.get(niche) or NICHE_POOL["general"]
        count = MIN_PER_POST + (int(hashlib.md5(slug.encode()).hexdigest(), 16) % (MAX_PER_POST - MIN_PER_POST + 1))

        for i in range(count):
            name = _pick(NAMES, f"{slug}-{i}-name")
            body = _pick(pool + ALL_POOL, f"{slug}-{i}-body")
            span = max(pub_ts, now - 90 * 86400)
            ts = span + (now - span) * (0.25 + 0.25 * i)
            ts = min(ts, now - 600)
            seed_key = f"{slug}-seed-{i}"
            rows.append(
                "INSERT OR IGNORE INTO comments (post_id, name, body, approved, seed_key, created_at) "
                f"VALUES ({_sql_literal(slug)}, {_sql_literal(name)}, {_sql_literal(body)}, 1, "
                f"{_sql_literal(seed_key)}, {_sql_literal(_iso(ts))});"
            )
        seeded.append(slug)

    if not rows:
        log("no new seed comments needed")
        return

    SEED_SQL_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8")
    write_json(SEEDED_PATH, seeded)
    log(f"generated {len(rows)} seed comments -> {SEED_SQL_PATH}")


if __name__ == "__main__":
    main()
