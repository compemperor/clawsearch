# ClawSearch 🔍🦀

**Private Meta-Search API** — Aggregate Google, Bing, DuckDuckGo & more without accounts, tracking, or credit cards.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ghcr.io%2Fcompemperor%2Fclawsearch-blue)](https://github.com/compemperor/clawsearch/pkgs/container/clawsearch)
[![Release](https://img.shields.io/github/v/release/compemperor/clawsearch)](https://github.com/compemperor/clawsearch/releases)

## Why ClawSearch?

- **No accounts required** — Self-host, own your searches
- **No tracking** — Your queries stay private
- **No credit cards** — Unlike Brave API, Google API, etc.
- **Aggregated results** — Best of multiple search engines
- **Clean REST API** — Simple JSON responses
- **Docker ready** — One command to deploy

## Quick Start

ClawSearch requires SearXNG + Redis. Use Docker Compose:

**Option 1: Clone repo**
```bash
git clone https://github.com/compemperor/clawsearch.git
cd clawsearch
docker compose up -d
```

**Option 2: Curl files directly**
```bash
mkdir clawsearch && cd clawsearch
curl -sLO https://raw.githubusercontent.com/compemperor/clawsearch/main/docker-compose.yml
mkdir -p searxng
curl -sL https://raw.githubusercontent.com/compemperor/clawsearch/main/searxng/settings.yml -o searxng/settings.yml
docker compose up -d
```

**Test:**
```bash
curl "http://localhost:8000/search?q=hello+world"
```

**Add skill to OpenClaw:**
```bash
mkdir -p ~/.openclaw/workspace/skills/clawsearch
curl -sL https://raw.githubusercontent.com/compemperor/clawsearch/main/skill/SKILL.md \
  -o ~/.openclaw/workspace/skills/clawsearch/SKILL.md
```

## API Endpoints

### General Search
```bash
GET /search?q=your+query
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `q` | Search query (required) | - |
| `engines` | Comma-separated: google,bing,duckduckgo | all |
| `freshness` | Time filter: day, week, month, year | none |
| `lang` | Language code | en |
| `page` | Page number (1-10) | 1 |

### News Search
```bash
GET /news?q=breaking+news
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `q` | News query (required) | - |
| `freshness` | Time filter: day, week, month | day |
| `lang` | Language code | en |
| `page` | Page number | 1 |

### Tech Search
```bash
GET /tech?q=rust+programming
```
Searches GitHub, StackOverflow, HackerNews, and tech blogs.

### Image Search
```bash
GET /images?q=cats
```

### Health Check
```bash
GET /health
```

## Response Format

```json
{
  "query": "your search",
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "snippet": "Description text...",
      "engine": "google",
      "score": 1.5,
      "published": "2026-02-01T12:00:00"
    }
  ],
  "total": 100,
  "cached": false,
  "timestamp": "2026-02-01T17:00:00Z",
  "engines_used": ["google", "bing", "duckduckgo"],
  "suggestions": ["related search", "another suggestion"]
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_URL` | SearXNG backend URL | http://localhost:8888 |
| `CLAWSEARCH_API_KEYS` | Comma-separated API keys (empty = no auth) | "" |
| `CLAWSEARCH_CACHE_TTL` | Cache duration in seconds | 300 |

### API Authentication

Optional API key authentication:

```bash
# Set keys in docker-compose or environment
export CLAWSEARCH_API_KEYS="key1,key2,key3"

# Use in requests
curl -H "X-API-Key: key1" "http://localhost:8000/search?q=test"
```

## Deployment

### Docker Compose (Recommended)

```bash
docker compose up -d
```

This starts:
- **ClawSearch API** on port 8000
- **SearXNG** (internal, not exposed)

### Manual Setup

```bash
# 1. Start SearXNG
docker run -d -p 8888:8080 searxng/searxng

# 2. Install ClawSearch
pip install -r requirements.txt

# 3. Run
SEARXNG_URL=http://localhost:8888 uvicorn clawsearch.main:app --host 0.0.0.0 --port 8000
```

### Architecture

Redis caching is included by default for better performance.

```
ClawSearch API ─► SearXNG ─► [Google, Bing, DDG]
      │              │
      └──── Redis ◄──┘
```

## Customization

### Enable/Disable Search Engines

Edit `searxng/settings.yml`:

```yaml
engines:
  - name: google
    disabled: false
    
  - name: bing
    disabled: false
    
  - name: yahoo
    disabled: true  # Disable slow engines
```

### Add Rate Limiting

Use a reverse proxy (nginx/Caddy) with rate limiting, or add FastAPI middleware.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Your App      │────▶│   ClawSearch    │────▶│   SearXNG    │
│                 │     │   (FastAPI)     │     │  (Aggregator)│
└─────────────────┘     └─────────────────┘     └──────┬───────┘
                                                       │
                              ┌────────────────────────┼────────────────────────┐
                              ▼                        ▼                        ▼
                         ┌─────────┐              ┌─────────┐              ┌─────────┐
                         │ Google  │              │  Bing   │              │   DDG   │
                         └─────────┘              └─────────┘              └─────────┘
```

## Use Cases

- **Market Intelligence** — Monitor trends, news, competitors
- **Research Automation** — Aggregate sources without API limits
- **AI Agents** — Private search for LLM applications
- **Privacy-focused apps** — No user tracking

## Limitations

- **Rate limits** — Upstream engines may rate-limit heavy usage
- **CAPTCHAs** — Google/Bing may challenge from datacenter IPs
- **Freshness** — Results depend on engine indexing speed

## Contributing

PRs welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Add tests if applicable
4. Submit PR

## License

MIT License — use it however you want.

---

Made with 🦀 by [compemperor](https://github.com/compemperor)
