"""
In-Memory Caching Service
Provides caching for job listings, dashboard metrics, and frequently accessed data.
"""
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheEntry(Generic[T]):
    """A single cache entry with expiration."""
    
    def __init__(self, value: T, ttl_seconds: int):
        self.value = value
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.hits = 0
    
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    def get(self) -> T:
        self.hits += 1
        return self.value


class InMemoryCache:
    """
    Thread-safe in-memory cache with TTL support.
    """
    
    # Default TTL values in seconds
    TTL_SHORT = 60  # 1 minute
    TTL_MEDIUM = 300  # 5 minutes
    TTL_LONG = 900  # 15 minutes
    TTL_VERY_LONG = 3600  # 1 hour
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return entry.get()
    
    async def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM) -> None:
        """Set a value in cache."""
        async with self._lock:
            # Evict if at max size
            if len(self._cache) >= self._max_size:
                await self._evict_expired()
                if len(self._cache) >= self._max_size:
                    await self._evict_lru()
            
            self._cache[key] = CacheEntry(value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self, prefix: Optional[str] = None) -> int:
        """Clear cache. If prefix provided, only clear keys with that prefix pattern."""
        async with self._lock:
            if prefix is None:
                count = len(self._cache)
                self._cache.clear()
                return count
            
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    async def _evict_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
            self._stats["evictions"] += 1
        return len(expired_keys)
    
    async def _evict_lru(self) -> None:
        """Remove least recently used entries (lowest hit count)."""
        if not self._cache:
            return
        
        # Sort by hits and remove bottom 10%
        sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k].hits)
        num_to_remove = max(1, len(sorted_keys) // 10)
        
        for key in sorted_keys[:num_to_remove]:
            del self._cache[key]
            self._stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": f"{hit_rate:.1f}%"
        }


# Global cache instance
cache = InMemoryCache(max_size=2000)


# Cache key prefixes
class CacheKeys:
    JOBS = "jobs"
    JOB_DETAIL = "job_detail"
    COMPANIES = "companies"
    COMPANY_DETAIL = "company_detail"
    CANDIDATES = "candidates"
    CANDIDATE_DETAIL = "candidate_detail"
    DASHBOARD = "dashboard"
    LEADERBOARD = "leaderboard"
    USER_STATS = "user_stats"
    COMMISSION_RATES = "commission_rates"
    ACHIEVEMENTS = "achievements"


def cached(prefix: str, ttl: int = InMemoryCache.TTL_MEDIUM):
    """
    Decorator for caching async function results.
    
    Usage:
        @cached(CacheKeys.JOBS, ttl=300)
        async def get_jobs(filters):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            # Skip 'self' or 'cls' if present
            cache_args = args[1:] if args and hasattr(args[0], '__dict__') else args
            key = cache._generate_key(prefix, *cache_args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache HIT for {prefix}")
                return cached_value
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(key, result, ttl)
            logger.debug(f"Cache MISS for {prefix}, stored result")
            
            return result
        
        # Add method to invalidate this function's cache
        wrapper.invalidate = lambda: cache.clear(prefix)
        
        return wrapper
    return decorator


class CacheManager:
    """
    High-level cache management interface.
    """
    
    def __init__(self):
        self.cache = cache
    
    # ============= JOB CACHING =============
    
    async def get_jobs(self, filters: Dict = None) -> Optional[list]:
        """Get cached job listings."""
        key = cache._generate_key(CacheKeys.JOBS, filters=filters or {})
        return await cache.get(key)
    
    async def set_jobs(self, jobs: list, filters: Dict = None) -> None:
        """Cache job listings."""
        key = cache._generate_key(CacheKeys.JOBS, filters=filters or {})
        await cache.set(key, jobs, InMemoryCache.TTL_MEDIUM)
    
    async def invalidate_jobs(self) -> int:
        """Invalidate all job caches."""
        return await cache.clear(CacheKeys.JOBS)
    
    # ============= DASHBOARD CACHING =============
    
    async def get_dashboard(self, user_id: str, role: str) -> Optional[Dict]:
        """Get cached dashboard data."""
        key = cache._generate_key(CacheKeys.DASHBOARD, user_id=user_id, role=role)
        return await cache.get(key)
    
    async def set_dashboard(self, user_id: str, role: str, data: Dict) -> None:
        """Cache dashboard data."""
        key = cache._generate_key(CacheKeys.DASHBOARD, user_id=user_id, role=role)
        await cache.set(key, data, InMemoryCache.TTL_SHORT)  # Short TTL for dashboards
    
    async def invalidate_dashboard(self, user_id: str = None) -> int:
        """Invalidate dashboard caches."""
        if user_id:
            key = cache._generate_key(CacheKeys.DASHBOARD, user_id=user_id)
            return 1 if await cache.delete(key) else 0
        return await cache.clear(CacheKeys.DASHBOARD)
    
    # ============= LEADERBOARD CACHING =============
    
    async def get_leaderboard(self, period: str = "all") -> Optional[list]:
        """Get cached leaderboard."""
        key = cache._generate_key(CacheKeys.LEADERBOARD, period=period)
        return await cache.get(key)
    
    async def set_leaderboard(self, data: list, period: str = "all") -> None:
        """Cache leaderboard data."""
        key = cache._generate_key(CacheKeys.LEADERBOARD, period=period)
        await cache.set(key, data, InMemoryCache.TTL_MEDIUM)
    
    # ============= ACHIEVEMENTS CACHING =============
    
    async def get_achievements(self) -> Optional[list]:
        """Get cached achievements list."""
        return await cache.get(CacheKeys.ACHIEVEMENTS)
    
    async def set_achievements(self, achievements: list) -> None:
        """Cache achievements list."""
        await cache.set(CacheKeys.ACHIEVEMENTS, achievements, InMemoryCache.TTL_VERY_LONG)
    
    # ============= COMMISSION RATES CACHING =============
    
    async def get_commission_rates(self) -> Optional[Dict]:
        """Get cached commission rates."""
        return await cache.get(CacheKeys.COMMISSION_RATES)
    
    async def set_commission_rates(self, rates: Dict) -> None:
        """Cache commission rates."""
        await cache.set(CacheKeys.COMMISSION_RATES, rates, InMemoryCache.TTL_VERY_LONG)
    
    # ============= STATS =============
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return cache.get_stats()
    
    async def clear_all(self) -> Dict[str, int]:
        """Clear all caches."""
        count = await cache.clear()
        return {"cleared": count}


# Singleton instance
cache_manager = CacheManager()
