"""
ClawSearch - Private Meta-Search API

A clean REST API wrapper around SearXNG for private, aggregated search.
No accounts, no tracking, no credit cards.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, List
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuration
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8888")
API_KEYS = os.getenv("CLAWSEARCH_API_KEYS", "").split(",")  # Comma-separated, empty = no auth
CACHE_TTL = int(os.getenv("CLAWSEARCH_CACHE_TTL", "300"))  # 5 minutes default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis client (lazy init)
_redis = None

def get_redis():
    """Get Redis client, lazy initialization."""
    global _redis
    if _redis is None:
        try:
            import redis
            _redis = redis.from_url(REDIS_URL, decode_responses=True)
            _redis.ping()  # Test connection
        except Exception as e:
            print(f"Redis not available, using in-memory cache: {e}")
            _redis = False  # Mark as unavailable
    return _redis if _redis else None

# Fallback in-memory cache
_memory_cache: dict = {}


app = FastAPI(
    title="ClawSearch",
    description="Private Meta-Search API. Aggregates Google, Bing, DuckDuckGo & more without tracking.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Models ====================

class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    url: str
    snippet: str = Field(alias="content", default="")
    engine: str = ""
    score: float = 0.0
    published: Optional[str] = Field(alias="publishedDate", default=None)
    
    class Config:
        populate_by_name = True


class SearchResponse(BaseModel):
    """Search API response."""
    query: str
    results: List[SearchResult]
    total: int
    cached: bool = False
    timestamp: str
    engines_used: List[str] = []
    suggestions: List[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    searxng: str
    redis: str
    version: str
    timestamp: str


# ==================== Auth ====================

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Optional API key verification."""
    if not API_KEYS or API_KEYS == [""]:
        return True  # No auth configured
    if x_api_key and x_api_key in API_KEYS:
        return True
    raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ==================== Cache ====================

def cache_key(query: str, **params) -> str:
    """Generate cache key from query and params."""
    key_str = f"clawsearch:{query}:{sorted(params.items())}"
    return hashlib.md5(key_str.encode()).hexdigest()


def get_cached(key: str) -> Optional[dict]:
    """Get from Redis cache, fallback to memory."""
    redis = get_redis()
    
    if redis:
        try:
            data = redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
    
    # Fallback to memory cache
    if key in _memory_cache:
        data, exp = _memory_cache[key]
        if datetime.now().timestamp() < exp:
            return data
        del _memory_cache[key]
    
    return None


def set_cached(key: str, data: dict):
    """Store in Redis cache, fallback to memory."""
    redis = get_redis()
    
    if redis:
        try:
            redis.setex(key, CACHE_TTL, json.dumps(data, default=str))
            return
        except Exception:
            pass
    
    # Fallback to memory cache
    _memory_cache[key] = (data, datetime.now().timestamp() + CACHE_TTL)


# ==================== SearXNG Client ====================

async def search_searxng(
    query: str,
    categories: str = "general",
    engines: Optional[str] = None,
    time_range: Optional[str] = None,
    language: str = "en",
    page: int = 1,
) -> dict:
    """Query SearXNG and return results."""
    
    params = {
        "q": query,
        "format": "json",
        "categories": categories,
        "language": language,
        "pageno": page,
    }
    
    if engines:
        params["engines"] = engines
    if time_range:
        params["time_range"] = time_range
    
    url = f"{SEARXNG_URL}/search?{urlencode(params)}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"SearXNG unavailable: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"SearXNG error: {e}")


# ==================== API Endpoints ====================

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to docs."""
    return {"message": "ClawSearch API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and SearXNG health."""
    searxng_status = "unknown"
    redis_status = "unknown"
    
    # Check SearXNG
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{SEARXNG_URL}/healthz")
            searxng_status = "healthy" if resp.status_code == 200 else "degraded"
    except Exception:
        searxng_status = "unreachable"
    
    # Check Redis
    redis = get_redis()
    if redis:
        try:
            redis.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "degraded"
    else:
        redis_status = "disabled (using memory)"
    
    overall = "healthy" if searxng_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall,
        searxng=searxng_status,
        redis=redis_status,
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    engines: Optional[str] = Query(None, description="Comma-separated engines (google,bing,duckduckgo)"),
    freshness: Optional[str] = Query(None, description="Time filter: day, week, month, year"),
    lang: str = Query("en", description="Language code"),
    page: int = Query(1, ge=1, le=10, description="Page number"),
    _auth: bool = Depends(verify_api_key),
):
    """
    General web search.
    
    Aggregates results from multiple search engines.
    """
    # Check cache
    ck = cache_key(q, engines=engines, freshness=freshness, lang=lang, page=page, cat="general")
    cached = get_cached(ck)
    if cached:
        cached["cached"] = True
        return SearchResponse(**cached)
    
    # Query SearXNG
    data = await search_searxng(
        query=q,
        categories="general",
        engines=engines,
        time_range=freshness,
        language=lang,
        page=page,
    )
    
    # Build response
    results = [SearchResult(**r) for r in data.get("results", [])]
    engines_used = list(set(r.engine for r in results if r.engine))
    
    response = {
        "query": q,
        "results": [r.model_dump() for r in results],  # Convert to dicts for caching
        "total": data.get("number_of_results", len(results)),
        "cached": False,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "engines_used": engines_used,
        "suggestions": data.get("suggestions", []),
    }
    
    set_cached(ck, response)
    return SearchResponse(**response)


@app.get("/news", response_model=SearchResponse)
async def news_search(
    q: str = Query(..., description="News search query", min_length=1),
    freshness: str = Query("day", description="Time filter: day, week, month"),
    lang: str = Query("en", description="Language code"),
    page: int = Query(1, ge=1, le=10),
    _auth: bool = Depends(verify_api_key),
):
    """
    News search.
    
    Returns recent news articles from multiple sources.
    """
    ck = cache_key(q, freshness=freshness, lang=lang, page=page, cat="news")
    cached = get_cached(ck)
    if cached:
        cached["cached"] = True
        return SearchResponse(**cached)
    
    data = await search_searxng(
        query=q,
        categories="news",
        time_range=freshness,
        language=lang,
        page=page,
    )
    
    results = [SearchResult(**r) for r in data.get("results", [])]
    engines_used = list(set(r.engine for r in results if r.engine))
    
    response = {
        "query": q,
        "results": [r.model_dump() for r in results],
        "total": data.get("number_of_results", len(results)),
        "cached": False,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "engines_used": engines_used,
        "suggestions": data.get("suggestions", []),
    }
    
    set_cached(ck, response)
    return SearchResponse(**response)


@app.get("/tech", response_model=SearchResponse)
async def tech_search(
    q: str = Query(..., description="Tech/IT search query", min_length=1),
    freshness: Optional[str] = Query(None, description="Time filter"),
    page: int = Query(1, ge=1, le=10),
    _auth: bool = Depends(verify_api_key),
):
    """
    Tech & IT search.
    
    Searches GitHub, StackOverflow, HackerNews, and tech news.
    """
    ck = cache_key(q, freshness=freshness, page=page, cat="tech")
    cached = get_cached(ck)
    if cached:
        cached["cached"] = True
        return SearchResponse(**cached)
    
    data = await search_searxng(
        query=q,
        categories="it",
        engines="github,stackoverflow,hackernews,google",
        time_range=freshness,
        page=page,
    )
    
    results = [SearchResult(**r) for r in data.get("results", [])]
    engines_used = list(set(r.engine for r in results if r.engine))
    
    response = {
        "query": q,
        "results": [r.model_dump() for r in results],
        "total": data.get("number_of_results", len(results)),
        "cached": False,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "engines_used": engines_used,
        "suggestions": data.get("suggestions", []),
    }
    
    set_cached(ck, response)
    return SearchResponse(**response)


@app.get("/images")
async def image_search(
    q: str = Query(..., description="Image search query", min_length=1),
    page: int = Query(1, ge=1, le=10),
    _auth: bool = Depends(verify_api_key),
):
    """
    Image search.
    
    Returns image results from multiple engines.
    """
    data = await search_searxng(
        query=q,
        categories="images",
        page=page,
    )
    
    # Image results have different structure
    images = []
    for r in data.get("results", []):
        images.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "thumbnail": r.get("thumbnail", r.get("img_src", "")),
            "source": r.get("source", ""),
            "engine": r.get("engine", ""),
        })
    
    return {
        "query": q,
        "images": images,
        "total": len(images),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ==================== Run ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
