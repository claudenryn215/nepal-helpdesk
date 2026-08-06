# Operator Handbook

Everything you need to run NepalHelpDesk hands-free — setup, secrets,
monitoring, upgrades, and monetization.

## 1. One-time setup (≈15 minutes)

### 1.1 Push the repo to GitHub
```bash
git init -b main
git add -A
git commit -m "initial: NepalHelpDesk site + pipeline"
gh repo create nepal-helpdesk --public --source=. --push
```
(GitHub Actions free tier applies to public repos.)

### 1.2 Free API keys
| Key | Where | Free limits (2026) | Needed? |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | aistudio.google.com → Get API key | Flash: ~10–15 req/min, 1,500 req/day | Optional but recommended |
| `GROQ_API_KEY` | console.groq.com | Llama 3.3 70B: 30 req/min, 1,000 req/day | Optional |
| `REDDIT_CLIENT_ID/SECRET/USERNAME/PASSWORD` | reddit.com/prefs/apps → create a "script" app | 100 req/min | Optional — Reddit anonymously is often 403-blocked |

No keys at all is fine: the pipeline still publishes from the verified
knowledge base; Reddit is skipped; everything else (RSS, Google News) works.

### 1.3 Deploy the OmniRoute gateway
Follow `omniroute/README.md`. Deploy to Cloudflare Workers free tier, create
a `combo/free` with your keys first and free pools last.

### 1.4 Add GitHub secrets
Settings → Secrets and variables → Actions:
`OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY`, `OMNIROUTE_MODEL`
(+ `GROQ_API_KEY`, `GEMINI_API_KEY`, Reddit creds as available).

### 1.5 Connect Cloudflare Pages
- Dashboard → Workers & Pages → Create → Pages → connect the GitHub repo
- Build command: `cd site && npm ci --no-audit --no-fund && npm run build`
- Output directory: `site/dist`
- The site is live at `<project>.pages.dev` after the first build.

## 2. Day-to-day operations (hands-free)

- **Every 6 hours**: GitHub Actions runs the pipeline → new verified guides
  are committed → Cloudflare Pages rebuilds automatically.
- **First run**: trigger manually via Actions → "Content Pipeline" →
  Run workflow (or `python pipeline/pipeline.py` locally).

### 2.1 The confidence gate
| Verdict | What happens |
| --- | --- |
| `kb` | Article rendered from the verified knowledge base → published |
| `high` | LLM-verified article → published |
| `medium` / `reject` | Moved to `pipeline/state/pending.json` → never auto-published |

You can review pending topics anytime:
```bash
python3 - << 'EOF'
import json
for p in json.load(open('pipeline/state/pending.json')):
    print(f"[{p['confidence']}] {p['title']} — {p['rationale'][:80]}")
EOF
```
If a topic deserves a permanent guide, add it to the knowledge base
(see section 3) and run `python pipeline/seed_kb.py` once.

### 2.2 Re-verification
Articles older than 90 days are automatically refreshed on the next
pipeline run (updated `lastVerified` + `updatedAt`).

### 2.3 Rate-limit resilience
- LLM calls go through OmniRoute's combo chain (Gemini → Groq → free pools).
- Direct `GROQ_API_KEY` / `GEMINI_API_KEY` are fallbacks if the Worker is down.
- Failed providers are auto-skipped for 24 h (see `state/provider-health.json`).
- If ALL LLMs fail: the pipeline publishes nothing new (except KB refreshes)
  but never breaks — pending topics wait in the queue.

## 3. Growing the knowledge base

The KB is the accuracy backbone. Add a YAML entry to any file in
`pipeline/knowledge/kb/` (or a new `*.yml`), then run
`python pipeline/seed_kb.py` and commit.

Entry fields: `id`, `niche`, `title`, `description`, `keywords` (EN + Nepali),
`tags`, `sources` (official URLs), `summary` (3 rows: problem/cause/fix),
`steps` (title + body with numbered sub-steps), `troubleshooting`,
`faq`, `affiliate` (e.g. `darax|router`, or `none`).

Rules: only write what you can verify from official sources; every step
must be conservative; no invented phone numbers or fees.

## 4. Upgrade to a free .com.np domain (recommended)

Nepali citizens get free `.com.np` domains (Nepal-only SEO advantage):

1. Pick a name and prepare a citizenship scan (front+back, clearly legible).
2. Create an account at `register.com.np` (Mercantile — the only .np registrar).
3. Apply with two nameservers from a hosting provider (e.g. Cloudflare DNS:
   `ava1.ns.cloudflare.com` / `ava2.ns.cloudflare.com`).
4. Wait 1–3 business days for manual approval.
5. In Cloudflare: add the zone, then in Pages → Custom domains → add
   `nepalhelpdesk.com.np`.
6. Update `site/astro.config.mjs` `site:` URL, `site/public/robots.txt`,
   `site/src/config.ts` `SITE.url`, and this handbook's references.

## 5. Monetization

### Affiliates (placeholders today)
- Edit `pipeline/config/affiliates.yml`: replace the `darax` URL template
  with your real Daraz Affiliate link, keeping `{q}` for keyword links.
- Articles using `{{affiliate:darax|q=...}}` then point at your tags.
- Same pattern for Brother-Mart / Nest Nepal.

### Ads
- Flip `enabled: true` in `pipeline/config/ads.yml`.
- Paste your network snippet (e.g. AdSense) into
  `site/src/components/AdSlot.astro` — the placeholder divs already have the
  right classes and heights.
- Rebuild site → deploy. (Until AdSense approval, placeholders keep layout.)

## 6. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `403` from Reddit | Create the free script app + creds (1.2). Reddit blocks anonymous traffic. |
| Pipeline failed in Actions | Read the run logs; re-run via `workflow_dispatch`. |
| LLM providers all failing | Check `state/provider-health.json`; keys valid? OmniRoute Worker up? |
| Pages build failing | Run `python pipeline/pipeline.py --build-check` locally to reproduce. |
| No new articles for days | Normal if nothing trending passes the confidence gate; check `pending.json`. |
| Articles stale | Re-verification runs every pipeline cycle; wait ≤90 days or run manually. |

## 7. Costs

Everything runs on free tiers: GitHub Actions (public repo), Cloudflare
Pages + Workers, Gemini/Groq free API tiers, Reddit (free OAuth), RSS.
There is no billing step anywhere. The only potential future cost is a
paid LLM tier if you choose reliability guarantees over free tier pooling.
