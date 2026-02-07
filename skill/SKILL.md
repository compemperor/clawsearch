---
name: clawsearch
description: Private meta-search API. Aggregate Google, Bing, DuckDuckGo without accounts, tracking, or API keys.
homepage: https://github.com/compemperor/clawsearch
metadata:
  openclaw:
    emoji: "🔍"
    requires:
      bins: ["docker"]
    install:
      - id: docker
        kind: shell
        command: "git clone https://github.com/compemperor/clawsearch && cd clawsearch && docker compose up -d"
        label: "Deploy ClawSearch (Docker Compose)"
---

# ClawSearch Skill 🔍

Private meta-search API for AI agents.

## Quick Deploy

ClawSearch requires SearXNG + Redis. Use Docker Compose:

**Option 1: Clone repo**
```bash
git clone https://github.com/compemperor/clawsearch
cd clawsearch
docker compose up -d
```

**Option 2: Curl files**
```bash
mkdir clawsearch && cd clawsearch
curl -sLO https://raw.githubusercontent.com/compemperor/clawsearch/main/docker-compose.yml
curl -sLO https://raw.githubusercontent.com/compemperor/clawsearch/main/Dockerfile
curl -sL https://raw.githubusercontent.com/compemperor/clawsearch/main/searxng/settings.yml -o searxng/settings.yml --create-dirs
docker compose up -d
```

API available at `http://localhost:8000`

## Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/search` | Web search | `/search?q=hello` |
| `/news` | News articles | `/news?q=AI&freshness=day` |
| `/tech` | Tech content | `/tech?q=rust` |
| `/images` | Image search | `/images?q=cats` |
| `/health` | Health check | `/health` |

## Usage

```bash
# General search
curl "http://localhost:8000/search?q=your+query"

# News (last 24h)
curl "http://localhost:8000/news?q=topic&freshness=day"

# Tech (GitHub, HN, StackOverflow)
curl "http://localhost:8000/tech?q=fastapi"
```

## Parameters

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query (required) |
| `engines` | string | `google,bing,duckduckgo` |
| `freshness` | string | `day`, `week`, `month`, `year` |
| `lang` | string | Language code (default: `en`) |
| `page` | int | Page number (1-10) |

## Response

```json
{
  "query": "your search",
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "snippet": "Description...",
      "engine": "google"
    }
  ],
  "total": 100,
  "cached": false,
  "timestamp": "2026-02-01T17:00:00Z",
  "engines_used": ["google", "bing"],
  "suggestions": ["related search"]
}
```

## Why ClawSearch?

- **No API keys** — Self-hosted
- **No tracking** — Private by design
- **No rate limits** — You control infra
- **No credit cards** — Unlike Brave/Google APIs
- **Aggregated** — Multiple search engines

## Full Documentation

https://github.com/compemperor/clawsearch
