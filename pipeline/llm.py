"""LLM client with a provider fallback chain.

Primary: OmniRoute gateway (self-hosted on Cloudflare Workers, free tier).
Fallbacks: Groq free tier, then Gemini free tier (OpenAI-compatible endpoint).
All calls are OpenAI-compatible chat completions.

Provider health is tracked in state/provider-health.json; a provider that
fails 3 times in a row is skipped for 24 hours.
"""
from __future__ import annotations

import json
import os
import time

import requests

from common import STATE_DIR, log, read_json, write_json

HEALTH_PATH = STATE_DIR / "provider-health.json"
SKIP_HOURS = 24
MAX_FAILURES = 3
TIMEOUT = 120


def _providers() -> list[dict]:
    return [
        {
            "name": "omniroute",
            "base": os.environ.get("OMNIROUTE_BASE_URL", "").rstrip("/"),
            "key": os.environ.get("OMNIROUTE_API_KEY", ""),
            "model": os.environ.get("OMNIROUTE_MODEL", "auto/best-free"),
        },
        {
            "name": "groq",
            "base": "https://api.groq.com/openai/v1",
            "key": os.environ.get("GROQ_API_KEY", ""),
            "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        },
        {
            "name": "gemini",
            "base": "https://generativelanguage.googleapis.com/v1beta/openai",
            "key": os.environ.get("GEMINI_API_KEY", ""),
            "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        },
    ]


def _health() -> dict:
    data = read_json(HEALTH_PATH, {})
    return data if isinstance(data, dict) else {}


def _save_health(data: dict) -> None:
    write_json(HEALTH_PATH, data)


def _provider_blocked(provider: str, health: dict) -> bool:
    entry = health.get(provider) or {}
    skip_until = entry.get("skip_until", 0)
    return skip_until > time.time()


def _record_failure(provider: str, health: dict) -> None:
    entry = health.get(provider) or {}
    entry["failures"] = entry.get("failures", 0) + 1
    entry["last_fail"] = int(time.time())
    if entry["failures"] >= MAX_FAILURES:
        entry["skip_until"] = int(time.time()) + SKIP_HOURS * 3600
        log(f"LLM provider '{provider}' skipped for {SKIP_HOURS}h (3+ failures)")
    health[provider] = entry
    _save_health(health)


def _record_success(provider: str, health: dict) -> None:
    entry = health.get(provider)
    if entry:
        entry["failures"] = 0
        entry.pop("skip_until", None)
        health[provider] = entry
        _save_health(health)


def available() -> bool:
    return any(p["key"] for p in _providers() if p["base"])


def chat(
    messages: list[dict],
    *,
    json_mode: bool = False,
    max_tokens: int = 1500,
    temperature: float = 0.4,
) -> str:
    """Send a chat completion through the first healthy provider. Raises
    LLMUnavailable when every provider fails."""
    health = _health()
    last_error = "no providers configured"

    for provider in _providers():
        if not provider["key"] or not provider["base"]:
            continue
        if _provider_blocked(provider["name"], health):
            continue
        try:
            payload: dict = {
                "model": provider["model"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            resp = requests.post(
                f"{provider['base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider['key']}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=TIMEOUT,
            )
            if resp.status_code in (429, 500, 502, 503, 504):
                last_error = f"{provider['name']} HTTP {resp.status_code}"
                _record_failure(provider["name"], health)
                time.sleep(2)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            _record_success(provider["name"], health)
            return content
        except (requests.RequestException, KeyError, ValueError, IndexError) as exc:
            last_error = f"{provider['name']}: {exc}"
            _record_failure(provider["name"], health)

    raise LLMUnavailable(f"all LLM providers failed ({last_error})")


def chat_json(messages: list[dict], **kwargs) -> dict:
    raw = chat(messages, json_mode=True, **kwargs)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            raise LLMUnavailable(f"non-JSON response from LLM: {raw[:200]}")
        data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise LLMUnavailable("LLM returned non-object JSON")
    return data


class LLMUnavailable(Exception):
    pass
