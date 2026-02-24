"""
In-memory cache manager with TTL support for Instagram Reels Scraper API.
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support."""

    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return (time.time() - self.created_at) > self.ttl_seconds

    def get_data(self) -> Any:
        """Get the cached data."""
        return self.data


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        with self.lock:
            entry = self.cache.get(key)
            if entry is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            if entry.is_expired():
                # Remove expired entry
                del self.cache[key]
                logger.debug(f"Cache expired for key: {key}")
                return None

            logger.debug(f"Cache hit for key: {key}")
            return entry.get_data()

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            data: Data to cache
            ttl_seconds: TTL in seconds (uses default if None)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        with self.lock:
            self.cache[key] = CacheEntry(data, ttl)
            logger.debug(f"Cached data for key: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Deleted cache key: {key}")
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared {count} cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_entries = len(self.cache)
            expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())

            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "default_ttl": self.default_ttl
            }

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self.lock:
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)


# Global cache instance
cache_manager = InMemoryCache(default_ttl=300)  # 5 minutes TTL


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return cache_manager.get_stats()


def clear_cache() -> None:
    """Clear all cache entries."""
    cache_manager.clear()


def cleanup_expired_cache() -> int:
    """Clean up expired cache entries and return count removed."""
    return cache_manager.cleanup_expired()


def get_cached_scraped_data(username: str) -> Optional[Tuple[List[Dict], str, Optional[str]]]:
    """
    Get cached scraped data for a username.

    Args:
        username: Instagram username

    Returns:
        Tuple of (reels_data, status, error_message) or None if not cached/expired
    """
    return cache_manager.get(f"scraped_data:{username}")


def set_cached_scraped_data(
    username: str,
    reels_data: List[Dict],
    status: str,
    error_message: Optional[str] = None,
    ttl_seconds: Optional[int] = None
) -> None:
    """
    Cache scraped data for a username.

    Args:
        username: Instagram username
        reels_data: List of reel dictionaries
        status: Scraper status
        error_message: Optional error message
        ttl_seconds: Optional custom TTL (uses default if None)
    """
    cache_data = (reels_data, status, error_message)
    cache_manager.set(f"scraped_data:{username}", cache_data, ttl_seconds)
