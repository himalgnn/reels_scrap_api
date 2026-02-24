from fastapi import Depends, Header

# Simple API key (in production, use a more secure method)
API_KEY = "himalgnnguragain"  # Change this to your actual key or use an environment variable

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
import asyncio

# Fix for Windows asyncio event loop policy - set before any imports that use asyncio
try:
    # Check if we're in an async context
    loop = asyncio.get_running_loop()
except RuntimeError:
    # No running loop, set policy before creating any async operations
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, AnyHttpUrl, validator



# Basic logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Instagram Reels Scraper API",
    description="An API to scrape Instagram Reels.",
    version="0.1.0"
)

# Request model for scraping a reel
class ScrapeRequest(BaseModel):
    # AnyHttpUrl से बेसिक URL schema/domain validation मिलती है
    reel_url: AnyHttpUrl

    # Use pydantic v1.x @validator
    from pydantic import validator
    @validator("reel_url")
    def validate_instagram_url(cls, v):
        host = v.host or ""
        path = v.path or ""
        # Instagram domain check
        if "instagram.com" not in host and "instagr.am" not in host:
            raise ValueError("URL must be an Instagram URL")
        # Accept /reel/<shortcode>, /reels/<shortcode>, or /p/<shortcode>
        import re
        if not re.search(r"/(reel|reels|p)/[\w\-]+/?", path):
            raise ValueError("URL must be an Instagram reel or post URL")
        return v

# Response model for a single reel
class ReelData(BaseModel):
    id: str
    reel_url: str  # Changed from AnyHttpUrl for flexibility
    video_url: Optional[str] = None
    thumbnail_url: str
    caption: Optional[str] = None
    posted_at: str  # ISO format string
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None

# Response model for bulk scraping
class ScrapeUserResponse(BaseModel):
    username: str
    status: str
    message: Optional[str] = None
    reels_count: int
    reels: List[ReelData]

@app.get("/")
def read_root():
    """Root endpoint that returns a welcome message."""
    logger.info("Root endpoint was accessed.")
    return {"message": "Instagram Reels Scraper API operational"}

@app.post("/scrape", response_model=ReelData, dependencies=[Depends(verify_api_key)])
async def scrape_reel(request: ScrapeRequest):
    """
    Scrape Instagram reel data from the provided URL.

    Args:
        request: ScrapeRequest containing the reel URL

    Returns:
        ReelData: Scraped reel information

    Raises:
        HTTPException: If scraping fails or URL is invalid
    """
    logger.info(f"Scraping reel from URL: {request.reel_url}")

    try:
        # TODO: Implement actual scraping logic here
        # This is a placeholder that returns mock data
        reel_data = await scrape_instagram_reel(str(request.reel_url))
        logger.info(f"Successfully scraped reel: {reel_data.id}")
        return reel_data
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error scraping reel: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to scrape reel")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/scrape/user/{username}", response_model=ScrapeUserResponse, dependencies=[Depends(verify_api_key)])
async def scrape_user_reels(
    username: str,
    limit: int = Query(default=30, ge=1, le=100, description="Number of reels to scrape (1-100)")
):
    """
    Scrape Instagram reels from a user's profile.
    
    This endpoint uses high-performance Playwright scraping with:
    - Network interception for efficient data extraction
    - Smart scrolling algorithm
    - Private/non-existent account detection
    
    Args:
        username: Instagram username (without @)
        limit: Maximum number of reels to scrape (1-100)
        
    Returns:
        ScrapeUserResponse with list of scraped reels
        
    Raises:
        HTTPException: If scraping fails or account is inaccessible
    """
    logger.info(f"Scraping reels for user: @{username} (limit: {limit})")
    try:
        # Call the Playwright scraper with proper event loop handling
        reels_data, status, error_message = await scrape_reels(username, limit)
        # Handle different statuses
        if status == ScraperStatus.PRIVATE:
            raise HTTPException(
                status_code=403,
                detail=f"Account @{username} is private and cannot be scraped"
            )
        elif status == ScraperStatus.NOT_FOUND:
            raise HTTPException(
                status_code=404,
                detail=f"Account @{username} does not exist"
            )
        elif status == ScraperStatus.RATE_LIMITED:
            raise HTTPException(
                status_code=429,
                detail="Rate limited by Instagram. Please try again later."
            )
        elif status == ScraperStatus.ERROR:
            raise HTTPException(
                status_code=500,
                detail=f"Scraping failed: {error_message}"
            )
        # Convert to ReelData models
        reels = [ReelData(**reel) for reel in reels_data]
        logger.info(f"Successfully scraped {len(reels)} reels for @{username}")
        return ScrapeUserResponse(
            username=username,
            status=status,
            message="Successfully scraped reels",
            reels_count=len(reels),
            reels=reels
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error scraping @{username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
async def scrape_instagram_reel(url: str) -> ReelData:
    """
    Scrape Instagram reel data from the provided URL using instaloader.
    Args:
        url: Instagram reel URL
    Returns:
        ReelData: Scraped reel information
    """
    import instaloader
    from urllib.parse import urlparse
    import asyncio
    import random
    import time

    # List of proxies (add your own proxies here)
    import threading
    # Global proxy pool and lock
    if not hasattr(scrape_instagram_reel, "_proxy_pool"):
        scrape_instagram_reel._proxy_pool = [
            'http://103.169.255.54:8080',
            'http://103.169.255.50:8080',
            'http://103.169.255.51:8080',
            'http://103.169.255.52:8080',
            'http://103.169.255.53:8080',
            'http://103.169.255.55:8080',
            'http://103.169.255.56:8080',
            'http://103.105.49.53:8080',
            'http://103.105.49.54:8080',
            'http://103.105.49.55:8080',
            'http://103.105.49.56:8080',
            'http://103.105.49.57:8080',
            'http://103.105.49.58:8080',
            'http://103.105.49.59:8080',
            'http://103.105.49.60:8080',
            'http://103.105.49.61:8080',
            'http://103.105.49.62:8080',
            'http://103.105.49.63:8080',
            'http://103.105.49.64:8080',
            'http://103.105.49.65:8080',
            'http://103.105.49.66:8080',
            'http://103.105.49.67:8080',
            'http://103.105.49.68:8080',
            'http://103.105.49.69:8080',
            'http://103.105.49.70:8080',
            'http://103.105.49.71:8080',
            'http://103.105.49.72:8080',
            'http://103.105.49.73:8080',
            'http://103.105.49.74:8080',
            'http://103.105.49.75:8080',
            'http://103.105.49.76:8080',
            'http://103.105.49.77:8080',
            'http://103.105.49.78:8080',
            'http://103.105.49.79:8080',
            'http://103.105.49.80:8080',
            'http://103.105.49.81:8080',
            'http://103.105.49.82:8080',
            'http://103.105.49.83:8080',
            'http://103.105.49.84:8080',
            'http://103.105.49.85:8080',
            'http://103.105.49.86:8080',
            'http://103.105.49.87:8080',
            'http://103.105.49.88:8080',
            'http://103.105.49.89:8080',
            'http://103.105.49.90:8080',
            'http://103.105.49.91:8080',
            'http://103.105.49.92:8080',
            'http://103.105.49.93:8080',
            'http://103.105.49.94:8080',
            'http://103.105.49.95:8080',
            'http://103.105.49.96:8080',
            'http://103.105.49.97:8080',
            'http://103.105.49.98:8080',
            'http://103.105.49.99:8080',
            'http://103.105.49.100:8080',
        ]
        scrape_instagram_reel._proxy_lock = threading.Lock()
        scrape_instagram_reel._last_proxy = None

    def get_next_proxy():
        with scrape_instagram_reel._proxy_lock:
            pool = scrape_instagram_reel._proxy_pool
            last = scrape_instagram_reel._last_proxy
            # Remove last used from candidates
            candidates = [p for p in pool if p != last]
            if not candidates:
                # Only one proxy left, use it
                candidates = pool[:]
            if not candidates:
                return None
            proxy = random.choice(candidates)
            scrape_instagram_reel._last_proxy = proxy
            return proxy

    def remove_bad_proxy(proxy):
        with scrape_instagram_reel._proxy_lock:
            if proxy in scrape_instagram_reel._proxy_pool:
                scrape_instagram_reel._proxy_pool.remove(proxy)
                if scrape_instagram_reel._last_proxy == proxy:
                    scrape_instagram_reel._last_proxy = None

    # List of user agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1",
    ]

    # Extract shortcode from URL
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    shortcode = parts[-1] if parts else None
    if not shortcode:
        raise ValueError("Invalid Instagram reel URL")

    cooldown_seconds = 60
    user_agent = random.choice(USER_AGENTS)
    last_error = None
    proxies_tried = set()
    while True:
        pool = scrape_instagram_reel._proxy_pool[:]
        if not pool:
            # No proxies left, cooldown and retry
            await asyncio.sleep(cooldown_seconds)
            # Optionally, reload proxies from a source here
            pool = scrape_instagram_reel._proxy_pool[:]
            if not pool:
                raise HTTPException(
                    status_code=429,
                    detail="All proxies failed and pool is empty. Please wait and try again later."
                )
        for proxy in pool:
            if proxy in proxies_tried:
                continue
            proxies_tried.add(proxy)
            await asyncio.sleep(random.uniform(1, 2))
            L = instaloader.Instaloader()
            session_obj = getattr(L.context, '_session', None)
            if session_obj is not None:
                if proxy:
                    session_obj.proxies = {
                        "http": proxy,
                        "https": proxy,
                    }
                session_obj.headers["User-Agent"] = user_agent
            try:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                return ReelData(
                    id=post.shortcode,
                    reel_url=url,
                    video_url=post.video_url if post.is_video else None,
                    thumbnail_url=post.url,
                    caption=post.caption,
                    posted_at=post.date_utc.isoformat(),
                    views=post.video_view_count if post.is_video else None,
                    likes=post.likes,
                    comments=post.comments
                )
            except Exception as e:
                err_msg = str(e)
                last_error = err_msg
                # Remove bad proxy and try next
                remove_bad_proxy(proxy)
                # If rate-limited or 401, skip to next proxy immediately
                if (
                    "401 Unauthorized" in err_msg or
                    "Please wait a few minutes before you try again" in err_msg or
                    "429" in err_msg or
                    "rate limit" in err_msg.lower()
                ):
                    continue
                # Other errors: try next proxy
                continue
        # If all proxies tried and failed, cooldown and retry
        await asyncio.sleep(cooldown_seconds)
        # Optionally, reload proxies from a source here
        if not scrape_instagram_reel._proxy_pool:
            raise HTTPException(
                status_code=429,
                detail="All proxies failed and pool is empty. Please wait and try again later."
            )
