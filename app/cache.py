import json
import redis
from typing import Optional, Dict, Any
from app.config import get_settings

settings = get_settings()

# Redis client
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True
)


def get_cache_key(bbrefid: str, year: int) -> str:
    """Generate cache key for player stats"""
    return f"player_stats:{bbrefid}:{year}"


def get_cached_stats(bbrefid: str, year: int) -> Optional[Dict[str, Any]]:
    """Get stats from cache"""
    key = get_cache_key(bbrefid, year)
    cached = redis_client.get(key)

    if cached:
        return json.loads(cached)

    return None


def set_cached_stats(bbrefid: str, year: int, stats: Dict[str, Any]) -> None:
    """Set stats in cache with TTL"""
    key = get_cache_key(bbrefid, year)
    redis_client.setex(
        key,
        settings.cache_ttl,
        json.dumps(stats)
    )


def clear_cache(pattern: str = "player_stats:*") -> int:
    """Clear cache keys matching pattern"""
    keys = redis_client.keys(pattern)
    if keys:
        return redis_client.delete(*keys)
    return 0
