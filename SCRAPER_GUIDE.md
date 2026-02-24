# 🚀 Instagram Reels Scraper - Usage Guide

## Overview

High-performance Instagram Reels scraper built with **Playwright** and **FastAPI**, featuring:

- ⚡ **Network interception** for efficient data extraction
- 🔄 **Smart scrolling** algorithm with exponential backoff
- 🦊 **Firefox browser** (non-default, headless)
- 🛡️ **Private/non-existent account detection**
- 📊 **Structured data extraction** from GraphQL/JSON responses

---

## 🎯 New Endpoint: Scrape User Reels

### **GET** `/scrape/user/{username}`

Scrape Instagram reels from a user's profile with high performance.

#### Parameters

| Parameter | Type | Location | Required | Default | Description |
|-----------|------|----------|----------|---------|-------------|
| `username` | string | path | ✅ Yes | - | Instagram username (without @) |
| `limit` | integer | query | ❌ No | 30 | Number of reels to scrape (1-100) |

#### Example Requests

**Using cURL:**
```bash
# Scrape 30 reels (default)
curl http://localhost:8000/scrape/user/instagram

# Scrape 50 reels
curl "http://localhost:8000/scrape/user/instagram?limit=50"
```

**Using Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/scrape/user/instagram",
    params={"limit": 50}
)

if response.status_code == 200:
    data = response.json()
    print(f"Scraped {data['reels_count']} reels from @{data['username']}")
    for reel in data['reels']:
        print(f"  - {reel['id']}: {reel['caption'][:50]}...")
```

**Using JavaScript:**
```javascript
fetch('http://localhost:8000/scrape/user/instagram?limit=50')
  .then(res => res.json())
  .then(data => {
    console.log(`Scraped ${data.reels_count} reels`);
    data.reels.forEach(reel => {
      console.log(`${reel.id}: ${reel.caption}`);
    });
  });
```

{
  "username": "instagram",
  "status": "SUCCESS",
  "message": "Successfully scraped reels",
  "reels_count": 30,
  "reels": [
    {
      "id": "ABC123",
      "reel_url": "https://www.instagram.com/reel/DOJXD-mAFPz/?hl=en",
      "video_url": "https://scontent.cdninstagram.com/...",
      "thumbnail_url": "https://scontent.cdninstagram.com/...",
      "caption": "Check out this amazing reel! #instagram",
      "posted_at": "2025-10-01T10:30:00",
      "views": 150000,
      "likes": 5000,
      "comments": 250
    }
  ]
}

---

## 🏗️ Architecture

### Scraping Strategy (Priority Order)

1. **GraphQL Interception** (Fastest) ⚡
   - Intercepts Instagram's GraphQL API responses
   - Extracts structured JSON data directly from network
   - No DOM parsing required

2. **window._sharedData Extraction** (Fast) 🔍
   - Extracts initial page data from JavaScript
   - Pre-rendered data available immediately
   - Fallback if GraphQL interception fails

3. **DOM Scraping** (Slowest, Fallback) 🐌
   - Parses HTML elements for reel links
   - Used only when other methods fail
   - Limited metadata available

### Smart Scrolling Algorithm

```python
# Exponential backoff when no new content loads
wait_time = min(0.5 * (2 ** no_change_count), 5)

# Stops after 3 consecutive failed scroll attempts
if no_change_count >= 3:
    break  # Reached end of content
```

### Browser Configuration

- **Browser**: Firefox (non-default, less detectable)
- **Mode**: Headless
- **Viewport**: 1920x1080
- **User Agent**: Firefox 121 on Windows 10
- **Locale**: en-US

---

## 🔧 Technical Implementation

### Key Features in `scraper.py`

#### 1. Network Interception
```python
async def _intercept_graphql_response(self, response: Response):
    """Intercepts GraphQL API responses for efficient data extraction."""
    if "graphql/query" in response.url:
        data = await response.json()
        self.graphql_data.append(data)
```

#### 2. Account Status Detection
```python
async def _check_account_status(self, page: Page):
    """Detects private/non-existent accounts."""
    # Checks for:
    # - "Sorry, this page isn't available"
    # - "This Account is Private"
    # - Rate limiting/login challenges
```

#### 3. Context Manager Support
```python
async with InstagramScraper(headless=True) as scraper:
    reels, status, error = await scraper.scrape_reels("username", limit=50)
```

---

## 📊 Data Model

### ReelData Structure

```python
{
    "id": str,              # Reel shortcode (e.g., "ABC123")
    "reel_url": str,        # Full Instagram URL
    "video_url": str,       # Direct video URL (may be None)
    "thumbnail_url": str,   # Thumbnail image URL
    "caption": str,         # Reel caption (may be None)
    "posted_at": str,       # ISO 8601 timestamp
    "views": int,           # View count (may be None)
    "likes": int,           # Like count (may be None)
    "comments": int         # Comment count (may be None)
}
```

**Note**: Some fields may be `None` if:
- Data is not available in the initial response
- Account privacy settings restrict access
- Instagram's API structure changes

---

## 🚀 Deployment & Production 🚀

### Docker Deployment 🐳

#### Build and Run with Docker

```bash
# Build the Docker image
docker build -t insta-scraper-api .

# Run the container
docker run -p 8000:8000 insta-scraper-api
```

#### Using Docker Compose (Recommended)

```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

#### Dockerfile Features

- **Multi-stage build** for smaller image size
- **Playwright browser dependencies** pre-installed
- **Non-root user** for security
- **Health check** for container monitoring
- **Proper signal handling** for graceful shutdowns

#### Docker Commands

```bash
# Check container health
docker ps

# View logs
docker logs insta-scraper-api

# Execute commands in container
docker exec -it insta-scraper-api /bin/bash
```

---

## 💾 Caching System 💾

### Overview

The API includes an **in-memory caching system** with **TTL (Time-To-Live)** support to improve performance and reduce unnecessary scraping requests.

### Cache Features

- **TTL-based expiration**: 300 seconds (5 minutes) by default
- **Thread-safe operations** for concurrent access
- **Automatic cleanup** of expired entries
- **Cache statistics** for monitoring

### Cache Endpoints

#### Get Cache Statistics
**GET** `/cache/stats`

```bash
curl http://localhost:8000/cache/stats
```

**Response**:
```json
{
  "cache_stats": {
    "total_entries": 5,
    "expired_entries": 0,
    "active_entries": 5,
    "default_ttl": 300
  },
  "timestamp": "2025-10-02T16:54:41"
}
```

#### Clear All Cache
**DELETE** `/cache`

```bash
curl -X DELETE http://localhost:8000/cache
```

#### Clean Expired Entries
**DELETE** `/cache/expired`

```bash
curl -X DELETE http://localhost:8000/cache/expired
```

#### Get Cached User Data
**GET** `/cache/{username}`

```bash
curl http://localhost:8000/cache/instagram
```

### Cache Workflow

1. **Request received** → Check cache first
2. **Cache hit** → Return cached data immediately
3. **Cache miss** → Scrape fresh data
4. **Scrape success** → Cache the result
5. **Scrape failure** → Don't cache (avoid caching errors)

### Cache Benefits

- ⚡ **Faster response times** for repeated requests
- 🔄 **Reduced load** on Instagram servers
- 💰 **Lower bandwidth usage**
- 📊 **Better rate limit management**

### Cache Configuration

```python
# In cache_manager.py
DEFAULT_TTL = 300  # 5 minutes

# Custom TTL for specific users
set_cached_scraped_data(username, data, status, ttl_seconds=600)  # 10 minutes
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'playwright'"

**Solution**:
```bash
pip install playwright
python -m playwright install chromium
```

### Issue: Windows Asyncio Event Loop Error

**Problem**: `NotImplementedError` when launching Playwright browser

**Solution**:
1. The code includes Windows-specific event loop policy fixes
2. If issues persist, try using the requests-based fallback scraper
3. Consider using WSL (Windows Subsystem for Linux) for better compatibility

### Issue: Docker Container Issues

**Problem**: Playwright browser fails to launch in Docker

**Solution**:
```bash
# Make sure to install browsers in container
python -m playwright install chromium firefox

# Check if /dev/shm is properly mounted
# The Dockerfile includes proper shared memory setup
```

### Issue: Rate Limited by Instagram

**Solution**:
- Wait 15-30 minutes before retrying
- Use different IP address (VPN/proxy)
- Reduce scraping frequency
- Check cache first to avoid unnecessary requests

### Issue: Empty Results for Public Account

**Solution**:
- Check if account has reels (not just posts)
- Increase `limit` parameter
- Check logs for GraphQL interception success
- Try navigating to `/username/reels/` manually in browser

### Issue: Cache Not Working

**Problem**: Cache hits not registering

**Solution**:
```bash
# Check cache statistics
curl http://localhost:8000/cache/stats

# Clear cache if needed
curl -X DELETE http://localhost:8000/cache

### Example Test Usernames

| Username | Type | Expected Result |
|----------|------|-----------------|
{{ ... }}
| `cristiano` | Public, celebrity | ✅ Success with many reels |
| `private_account` | Private | ❌ 403 Forbidden |
| `nonexistent123456` | Non-existent | ❌ 404 Not Found |

---

## 🚀 Performance Optimization Tips

### 1. Reuse Browser Instance
```python
# Instead of creating new browser per request
scraper = InstagramScraper(headless=True)
await scraper.launch_browser()

# Make multiple scraping calls
reels1 = await scraper.scrape_reels("user1", 30)
reels2 = await scraper.scrape_reels("user2", 30)

await scraper.close_browser()
```

### 2. Adjust Scroll Speed
```python
# In scraper.py, modify wait times:
await asyncio.sleep(0.3)  # Faster scrolling (more aggressive)
await asyncio.sleep(1.0)  # Slower scrolling (more reliable)
```

### 3. Limit Data Extraction
```python
# Only extract essential fields to reduce processing time
# Modify _parse_media_node() to skip optional fields
```

---

## 📝 Next Steps

### Recommended Enhancements

1. **Caching Layer**
   - Cache scraped data in Redis/database
   - Reduce redundant scraping
   - Implement TTL for freshness

2. **Queue System**
   - Use Celery/RQ for background scraping
   - Handle concurrent requests properly
   - Implement retry logic

3. **Proxy Rotation**
   - Integrate proxy service
   - Rotate IPs to avoid rate limiting
   - Use residential proxies for better success rate

4. **Authentication**
   - Add Instagram login support
   - Access private accounts (with permission)
   - Increase rate limits

5. **Video Download**
   - Implement video downloading from `video_url`
   - Store videos locally or in cloud storage
   - Generate thumbnails

---

## 📚 API Documentation

Full interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**Built with Playwright + FastAPI** 🎭⚡
