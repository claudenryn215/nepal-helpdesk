"""Shared helpers for the NepalHelpDesk pipeline."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT / "pipeline"
SITE_CONTENT = ROOT / "site" / "src" / "content" / "articles"
STATE_DIR = PIPELINE_DIR / "state"
CONFIG_DIR = PIPELINE_DIR / "config"
KB_DIR = PIPELINE_DIR / "knowledge" / "kb"

STATE_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_yaml(path: Path) -> dict:
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_affiliates() -> dict:
    return load_yaml(CONFIG_DIR / "affiliates.yml").get("affiliates", {})


def load_ads() -> dict:
    return load_yaml(CONFIG_DIR / "ads.yml")


def load_sources() -> dict:
    return load_yaml(CONFIG_DIR / "sources.yml")


def load_niches() -> dict:
    return load_yaml(CONFIG_DIR / "niches.yml")


def load_kb() -> list[dict]:
    entries: list[dict] = []
    for path in sorted(KB_DIR.glob("*.yml")):
        entries.extend(load_yaml(path) or [])
    return entries


def slugify(text: str, max_len: int = 60) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    return text[:max_len].rstrip("-") or "topic"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def now_ts() -> float:
    return time.time()


def read_json(path: Path, default: object = None) -> object:
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: Path, data: object) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def env_flag(name: str, default: bool = False) -> bool:
    val = os.environ.get(name, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


def published_slugs() -> set[str]:
    if not SITE_CONTENT.exists():
        return set()
    return {p.stem for p in SITE_CONTENT.glob("*.md")}


def token_overlap(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    set_a, set_b = set(a), set(b)
    return len(set_a & set_b) / max(1.0, float(min(len(set_a), len(set_b))))


def log_exit(msg: str, code: int = 0) -> None:
    log(msg)
    sys.exit(code)
