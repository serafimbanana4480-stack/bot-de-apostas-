"""
Redis Cache Implementation.
Provides async wrapper for Redis caching with JSON serialization.
"""
import json
from typing import Any, Optional
import redis.asyncio as redis
from src.core.config import settings

class RedisCache:
    """Async Redis Cache Wrapper."""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            f"redis://{settings.DB_HOST}:6379/0",
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour
        
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        data = await self.redis_client.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return None
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache."""
        if ttl is None:
            ttl = self.default_ttl
            
        if not isinstance(value, (str, int, float, bool)):
            value = json.dumps(value)
            
        return await self.redis_client.set(key, value, ex=ttl)
        
    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        return await self.redis_client.delete(key) > 0
        
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching a pattern."""
        keys = await self.redis_client.keys(pattern)
        if keys:
            return await self.redis_client.delete(*keys)
        return 0
        
    async def close(self):
        """Close Redis connection."""
        await self.redis_client.close()

# Global singleton
cache = RedisCache()
