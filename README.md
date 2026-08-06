# NepalHelpDesk.np

A 100% free, fully automated troubleshooting help desk for Nepal.
Monitors Nepali online communities, verifies solutions, and publishes
SEO-ready step-by-step articles to a mobile-first static site — with no
manual writing or management.

## How it works

```
GitHub Actions (every 6 h, free)
  collect.py   → Reddit JSON (optional OAuth) + Nepali RSS + Google News RSS
  classify.py  → niche match, trending score, dedupe
  verify.py    → confidence gate: knowledge base + LLM verdicts
  generate.py  → articles from KB or LLM (OmniRoute gateway)
  publish.py   → markdown → repo → Cloudflare Pages auto-deploys
```

- **Site**: Astro 5 static site (mobile-first, JSON-LD HowTo/FAQ, sitemap, search)
- **LLM**: OmniRoute gateway (free, on Cloudflare Workers) → Gemini/Groq/free pools
- **Cost**: $0 — GitHub Actions free minutes, Cloudflare Pages free, free LLM tiers
- **Accuracy**: curated knowledge base + confidence gate; only `high`/`kb`
  confidence auto-publishes; `medium`/`reject` lands in a pending queue

## Quick start (local)

```bash
python3 -m pip install -r pipeline/requirements.txt
python3 pipeline/seed_kb.py          # seed initial articles from the KB
python3 pipeline/pipeline.py --dry-run   # test monitoring + classification
cd site && npm install && npm run build  # build the site
```

## Deploy (one-time, ~15 min)

1. Push this repo to GitHub (public).
2. Create a free Google AI Studio key and GroqCloud key.
3. Deploy OmniRoute to Cloudflare Workers — see `omniroute/README.md`.
4. Connect the repo to Cloudflare Pages:
   - Framework preset: **Astro**
   - Build command: `cd site && npm ci --no-audit --no-fund && npm run build`
   - Output directory: `site/dist`
5. Add secrets in GitHub → see `omniroute/README.md` for the table.

That's it. The cron job runs the pipeline every 6 hours and the site
updates itself.

## Layout

```
site/          Astro website (pages, components, styles, content)
pipeline/      Python automation (collect, classify, verify, generate, publish)
  knowledge/   verified knowledge base (YAML, human-curated seed)
  config/      sources, niches, affiliates, ads
  state/       runtime state (seen posts, trending, pending, published)
omniroute/     gateway deploy guide
docs/          handbook: operations, .com.np upgrade, monetization
```

## Monetization hooks

- Affiliate placeholders (`{{affiliate:darax|q=...}}`) render as sponsored
  links — swap the URL templates in `pipeline/config/affiliates.yml` for
  real program links (Daraz Affiliate, Brother-Mart, Nest Nepal).
- Ad slots (`{{ad:in-article-1}}`) render as styled placeholders — flip
  `enabled: true` in `pipeline/config/ads.yml` and drop in your AdSense
  snippet at `site/src/components/AdSlot.astro` when ready.
