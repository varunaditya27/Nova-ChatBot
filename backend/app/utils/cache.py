"""
Cache utilities for the application using Redis.
"""
import json
from typing import Any, Optional, TypeVar, Type, Callable, Awaitable
from functools import wraps
import logging
from fastapi import Request, Response
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

from app.utils.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheManager:
    """Manages cache operations for the application."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.backend = None
            self.initialized = False
            self._initialized = True
    
    async def initialize(self):
        """Initialize the Redis cache backend."""
        if not self.initialized and settings.cache_enabled:
            try:
                redis = aioredis.from_url(
                    settings.redis_url,
                    encoding="utf8",
                    decode_responses=True
                )
                self.backend = RedisBackend(redis)
                FastAPICache.init(self.backend, prefix="nova-cache")
                self.initialized = True
                logger.info("Cache initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize cache: {str(e)}")
                self.initialized = False
    
    def get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from the given prefix and keyword arguments."""
        if not kwargs:
            return prefix
        
        # Sort keys for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts = [f"{k}:{v}" for k, v in sorted_kwargs]
        return f"{prefix}:{":".join(key_parts)}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        if not self.initialized or not settings.cache_enabled:
            return None
            
        try:
            value = await self.backend.get(key)
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a value in the cache."""
        if not self.initialized or not settings.cache_enabled:
            return False
            
        try:
            expire = expire or settings.cache_ttl
            await self.backend.set(key, json.dumps(value), expire=expire)
            logger.debug(f"Cache set for key: {key} (expires in {expire}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        if not self.initialized or not settings.cache_enabled:
            return False
            
        try:
            await self.backend.clear(key)
            logger.debug(f"Cache deleted for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    async def invalidate_by_prefix(self, prefix: str) -> int:
        """Invalidate all cache keys with the given prefix."""
        if not self.initialized or not settings.cache_enabled:
            return 0
            
        try:
            # This is a simple implementation that works with Redis
            # For production, consider using SCAN for large datasets
            keys = await self.backend.redis.keys(f"*{prefix}*")
            if keys:
                await self.backend.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys with prefix: {prefix}")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Error invalidating cache by prefix {prefix}: {str(e)}")
            return 0

# Global cache instance
cache_manager = CacheManager()

def cached(
    key_prefix: str = "",
    expire: Optional[int] = None,
    namespace: str = ""
):
    """
    Decorator to cache the result of an async function.
    
    Args:
        key_prefix: Prefix for the cache key
        expire: Time to live in seconds (defaults to CACHE_TTL from settings)
        namespace: Optional namespace for the cache key
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Skip caching if disabled
            if not settings.cache_enabled:
                return await func(*args, **kwargs)
                
            # Generate cache key
            cache_key = cache_manager.get_cache_key(
                f"{namespace}:{key_prefix or func.__name__}",
                **{
                    k: v for k, v in kwargs.items() 
                    if k not in ['request', 'response']
                }
            )
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Call the function if not in cache
            result = await func(*args, **kwargs)
            
            # Cache the result
            if result is not None:
                await cache_manager.set(
                    cache_key, 
                    result,
                    expire=expire or settings.cache_ttl
                )
                
            return result
            
        return wrapper
    return decorator
