# OmniRoute — the free AI gateway (self-hosted on free cloud tiers)

OmniRoute is a free, MIT-licensed AI gateway that aggregates 90+ free LLM
providers behind one OpenAI-compatible endpoint, with automatic fallback
("Combos"), quota-aware routing, and token compression.

It is the LLM brain of NepalHelpDesk: the pipeline calls one URL, and
OmniRoute decides which free provider serves the request.

## Where to host it (all $0)

1. **Cloudflare Workers free tier (recommended)** — 100,000 requests/day,
   unlimited upstream I/O, same account as the Pages site.
   Deploy with the Wrangler CLI (see below).
2. **Fly.io free allowance** — the OmniRoute repo ships `fly.toml`;
   `fly launch` then `fly deploy`.
3. **Deno Deploy free tier** — supported by the OmniRoute project.

## Deploy to Cloudflare Workers

```bash
# 1. Install the gateway
npm install -g omniroute

# 2. Deploy as a Worker (wrangler)
wrangler deploy src/worker.ts --name omniroute-ai --compatibility-date 2026-01-01
```

> Note: `wrangler deploy` uploads the worker bundle. The exact entry file
> depends on the current OmniRoute release; check the project README
> (`github.com/diegosouzapw/OmniRoute`) — the maintainers publish a
> Workers-compatible build. If the bundle ever exceeds the 3 MB free-tier
> limit, use Fly.io or Deno Deploy instead (same $0).

## Configure the "Combo" fallback chain

In the OmniRoute dashboard (`https://omniroute-ai.<your-subdomain>.workers.dev`):

1. Sign in with the password you set at deploy time.
2. **Providers** → add your free keys:
   - Google AI Studio (Gemini) API key
   - GroqCloud API key
   - (optional) OpenRouter key
3. **Combos** → create a combo named `free` with priority order:
   1. Gemini Flash (your key)
   2. Groq Llama 3.3 70B (your key)
   3. Built-in no-auth free provider pools (need no keys)
4. **Endpoints** → create an API key for the pipeline.

## Point the pipeline at it

GitHub Actions secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
| --- | --- |
| `OMNIROUTE_BASE_URL` | `https://omniroute-ai.<subdomain>.workers.dev/v1` |
| `OMNIROUTE_API_KEY` | key created in the dashboard |
| `OMNIROUTE_MODEL` | `combo/free` (the combo name) |

The pipeline also accepts `GROQ_API_KEY` and `GEMINI_API_KEY` as direct
fallbacks, so content keeps flowing even if the Worker is unreachable.

## Watchdog

Provider health is recorded in `pipeline/state/provider-health.json`.
A provider failing 3 times in a row is skipped for 24 hours automatically.
