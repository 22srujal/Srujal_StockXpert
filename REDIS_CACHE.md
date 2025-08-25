# 🚀 Redis Cache Implementation Guide

## Overview

StockXpert now uses Redis for persistent, scalable caching instead of in-memory dictionaries. This provides significant improvements in reliability, performance, and scalability.

## 🌟 Benefits

- **Persistent Cache**: Survives server restarts and deployments
- **Scalable**: Supports multiple server instances
- **Automatic Expiration**: Built-in TTL with no memory leaks
- **Performance**: Optimized for caching workloads
- **Monitoring**: Built-in metrics and health checks
- **Fallback**: Graceful degradation to in-memory cache if Redis unavailable

## 🛠 Local Development Setup

### Option 1: Docker Compose (Recommended)

```bash
# Start all services including Redis
docker-compose up -d

# API will be available at http://localhost:8000
# Redis Commander UI at http://localhost:8081
```

### Option 2: Local Redis Installation

#### Windows:
```bash
# Install via Chocolatey
choco install redis-64

# Or download from: https://github.com/microsoftarchive/redis/releases
```

#### macOS:
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

### Option 3: Cloud Redis (Production)

Popular options:
- **Redis Cloud** (free tier available)
- **AWS ElastiCache**
- **Google Cloud Memorystore**
- **Azure Cache for Redis**

## ⚙️ Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600
REDIS_MAX_CONNECTIONS=10

# For cloud Redis:
# REDIS_URL=redis://username:password@host:port/0
```

### Vercel Deployment

For Vercel deployment, add environment variables in dashboard:

1. Go to Project Settings → Environment Variables
2. Add:
   - `REDIS_URL`: Your cloud Redis URL
   - `CACHE_TTL_SECONDS`: `3600`

## 🔄 Migration from In-Memory Cache

The implementation provides backward compatibility:

- ✅ **Automatic Fallback**: If Redis unavailable, uses in-memory cache
- ✅ **Same API**: All existing `get_cache()` and `set_cache()` calls work unchanged
- ✅ **Gradual Migration**: Can deploy without Redis initially

## 📊 Monitoring & Health Checks

### New API Endpoints

#### Health Check
```bash
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-25T10:30:00",
  "cache": {
    "status": "healthy",
    "backend": "redis",
    "response_time_ms": 1.23,
    "connected": true
  },
  "api": "operational"
}
```

#### Cache Statistics
```bash
GET /api/cache/stats
```

Response:
```json
{
  "backend": "redis",
  "connected": true,
  "total_keys": 156,
  "memory_usage": "2.1MB",
  "hits": 1247,
  "misses": 89
}
```

#### Clear Cache
```bash
POST /api/cache/clear
```

## 🐛 Troubleshooting

### Redis Connection Issues

1. **Check Redis Status**:
   ```bash
   redis-cli ping
   # Should return "PONG"
   ```

2. **Verify Connection String**:
   ```bash
   # Test connection
   redis-cli -u $REDIS_URL ping
   ```

3. **Check Logs**:
   ```bash
   # API logs will show cache status
   tail -f logs/app.log
   ```

### Performance Tuning

1. **Memory Settings**:
   ```bash
   # Redis config (redis.conf)
   maxmemory 100mb
   maxmemory-policy allkeys-lru
   ```

2. **Connection Pool**:
   ```bash
   # Increase for high traffic
   REDIS_MAX_CONNECTIONS=20
   ```

## 🧪 Testing

### Test Cache Functionality

```python
# Test cache service directly
from api.cache import cache_service

# Set test data
cache_service.set_cache("test_key", {"data": "test_value"})

# Get test data
result = cache_service.get_cache("test_key")
print(result)  # Should return {"data": "test_value"}

# Health check
health = cache_service.health_check()
print(health)
```

### Load Testing

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Test API with cache
hey -n 1000 -c 10 http://localhost:8000/api/symbols
```

## 📈 Performance Metrics

### Before Redis (In-Memory)
- ❌ Cache lost on restart
- ❌ Memory leaks possible
- ❌ Single instance only
- ⚡ ~0.1ms access time

### After Redis
- ✅ Persistent cache
- ✅ Automatic cleanup
- ✅ Multi-instance support
- ⚡ ~0.5ms access time
- 📊 Built-in monitoring

## 🔮 Future Enhancements

1. **Cache Warming**: Pre-populate cache with popular stocks
2. **Cache Hierarchies**: Different TTLs for different data types
3. **Compression**: Compress large datasets before caching
4. **Cache Invalidation**: Smart cache invalidation strategies
5. **Distributed Caching**: Redis Cluster for very high scale

## 🆘 Support

If you encounter issues:

1. Check the health endpoint: `/api/health`
2. Review cache stats: `/api/cache/stats`
3. Check Redis logs: `docker-compose logs redis`
4. Create an issue with cache health output
