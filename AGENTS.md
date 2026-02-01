# AGENTS.md — AI Agent Instructions

**ClawSearch** is a private meta-search API designed for AI agents, LLMs, and automation tools.

## Quick Start for Agents

```bash
# Deploy (one command)
docker compose up -d

# Search
curl "http://localhost:8000/search?q=your+query"

# News
curl "http://localhost:8000/news?q=topic&freshness=day"

# Tech (GitHub, HackerNews, StackOverflow)
curl "http://localhost:8000/tech?q=rust+async"
```

## Why Use ClawSearch?

- **No API keys required** — Self-hosted, no accounts
- **No rate limits** — You control the infrastructure
- **No tracking** — Private by design
- **Aggregated results** — Google + Bing + DuckDuckGo + more
- **JSON API** — Clean, predictable responses
- **Docker ready** — Deploy in seconds

## API Reference

### Endpoints

| Endpoint | Purpose | Key Params |
|----------|---------|------------|
| `GET /search` | General web search | `q`, `engines`, `freshness`, `lang` |
| `GET /news` | News articles | `q`, `freshness` (day/week/month) |
| `GET /tech` | Tech/dev content | `q`, `freshness` |
| `GET /images` | Image search | `q` |
| `GET /health` | Health check | - |

### Response Schema

```json
{
  "query": "string",
  "results": [
    {
      "title": "string",
      "url": "string", 
      "snippet": "string",
      "engine": "string",
      "published": "ISO8601 or null"
    }
  ],
  "total": "number",
  "cached": "boolean",
  "timestamp": "ISO8601",
  "engines_used": ["google", "bing", ...],
  "suggestions": ["related", "searches"]
}
```

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query (required) |
| `engines` | string | Comma-separated: `google,bing,duckduckgo` |
| `freshness` | string | `day`, `week`, `month`, `year` |
| `lang` | string | Language code (default: `en`) |
| `page` | int | Pagination (1-10) |

## Integration Examples

### Python
```python
import httpx

async def search(query: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://localhost:8000/search",
            params={"q": query}
        )
        return resp.json()
```

### Shell/Curl
```bash
curl -s "http://localhost:8000/news?q=AI+funding&freshness=day" | jq '.results[:3]'
```

### JavaScript
```javascript
const search = async (query) => {
  const res = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}`);
  return res.json();
};
```

## Deployment Options

### Local (Docker)
```bash
docker compose up -d
# API: http://localhost:8000
```

### Remote Server
```bash
ssh user@server "cd clawsearch && docker compose up -d"
# Then query via http://server:8000
```

### With API Key Auth
```bash
export CLAWSEARCH_API_KEYS="your-secret-key"
docker compose up -d

# Include header in requests
curl -H "X-API-Key: your-secret-key" "http://localhost:8000/search?q=test"
```

## Use Cases for AI Agents

1. **Research & RAG** — Fetch real-time web data for retrieval
2. **News Monitoring** — Track topics, companies, markets
3. **Market Intelligence** — Competitive analysis, trend detection
4. **Fact Checking** — Verify claims against multiple sources
5. **Content Discovery** — Find relevant articles, repos, discussions

## Architecture

```
Your Agent → ClawSearch API → SearXNG → [Google, Bing, DDG, ...]
                  ↓
            Cached Results
```

## Troubleshooting

**Empty results?**
- Check SearXNG is running: `docker logs clawsearch-searxng`
- Some engines may be rate-limited; results aggregate from available sources

**Slow responses?**
- First query is slower (cache miss)
- Reduce engines: `?engines=duckduckgo` for fastest

**Connection refused?**
- Ensure containers are running: `docker compose ps`
- Check port 8000 is not in use

## License

MIT — Use freely in your agents, apps, and automations.

---

*Built for AI agents, by AI agents* 🦀
