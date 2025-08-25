"""
Redis-based caching service for StockXpert
Replaces in-memory dictionary with persistent, scalable Redis cache
"""

import redis
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        """Initialize Redis connection with fallback to in-memory cache"""
        self.redis_client = None
        self.fallback_cache = {}  # Fallback to in-memory if Redis unavailable
        self.cache_ttl = int(os.getenv('CACHE_TTL_SECONDS', 3600))
        
        try:
            # Try to connect to Redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', 10)),
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, falling back to in-memory cache: {e}")
            self.redis_client = None

    def _serialize_data(self, data: Dict[Any, Any]) -> str:
        """Serialize data for Redis storage"""
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to serialize data: {e}")
            return "{}"

    def _deserialize_data(self, data: str) -> Dict[Any, Any]:
        """Deserialize data from Redis"""
        try:
            return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to deserialize data: {e}")
            return {}

    def set_cache(self, key: str, data: Dict[Any, Any]) -> bool:
        """
        Store data in cache with TTL
        
        Args:
            key: Cache key
            data: Data to cache
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.redis_client:
                # Use Redis
                serialized_data = self._serialize_data(data)
                result = self.redis_client.setex(
                    name=f"stockxpert:{key}",
                    time=self.cache_ttl,
                    value=serialized_data
                )
                return bool(result)
            else:
                # Fallback to in-memory cache
                self.fallback_cache[key] = {
                    "timestamp": datetime.now(),
                    "data": data
                }
                return True
                
        except Exception as e:
            logger.error(f"Cache set failed for key '{key}': {e}")
            return False

    def get_cache(self, key: str) -> Optional[Dict[Any, Any]]:
        """
        Retrieve data from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        try:
            if self.redis_client:
                # Use Redis
                cached_data = self.redis_client.get(f"stockxpert:{key}")
                if cached_data:
                    return self._deserialize_data(cached_data.decode('utf-8'))
                return None
            else:
                # Fallback to in-memory cache
                if key in self.fallback_cache:
                    cache_entry = self.fallback_cache[key]
                    age = (datetime.now() - cache_entry["timestamp"]).total_seconds()
                    if age < self.cache_ttl:
                        return cache_entry["data"]
                    else:
                        # Clean up expired entry
                        del self.fallback_cache[key]
                return None
                
        except Exception as e:
            logger.error(f"Cache get failed for key '{key}': {e}")
            return None

    def delete_cache(self, key: str) -> bool:
        """Delete specific cache entry"""
        try:
            if self.redis_client:
                result = self.redis_client.delete(f"stockxpert:{key}")
                return bool(result)
            else:
                if key in self.fallback_cache:
                    del self.fallback_cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Cache delete failed for key '{key}': {e}")
            return False

    def clear_cache(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.redis_client:
                # Delete all keys with stockxpert prefix
                keys = self.redis_client.keys("stockxpert:*")
                if keys:
                    result = self.redis_client.delete(*keys)
                    return bool(result)
                return True
            else:
                self.fallback_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                keys = self.redis_client.keys("stockxpert:*")
                return {
                    "backend": "redis",
                    "connected": True,
                    "total_keys": len(keys),
                    "memory_usage": info.get('used_memory_human', 'Unknown'),
                    "hits": info.get('keyspace_hits', 0),
                    "misses": info.get('keyspace_misses', 0)
                }
            else:
                return {
                    "backend": "in-memory",
                    "connected": False,
                    "total_keys": len(self.fallback_cache),
                    "memory_usage": "Unknown",
                    "hits": 0,
                    "misses": 0
                }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Check cache service health"""
        try:
            if self.redis_client:
                start_time = datetime.now()
                self.redis_client.ping()
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    "status": "healthy",
                    "backend": "redis",
                    "response_time_ms": round(response_time, 2),
                    "connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "backend": "in-memory",
                    "response_time_ms": 0,
                    "connected": False,
                    "message": "Using fallback in-memory cache"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "redis",
                "connected": False,
                "error": str(e)
            }


# Global cache service instance
cache_service = CacheService()


# Backward compatibility functions
def set_cache(key: str, data: Dict[Any, Any]) -> bool:
    """Legacy function for backward compatibility"""
    return cache_service.set_cache(key, data)


def get_cache(key: str) -> Optional[Dict[Any, Any]]:
    """Legacy function for backward compatibility"""
    return cache_service.get_cache(key)
