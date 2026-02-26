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
import os
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, AnyHttpUrl, validator
from cache_manager import cache_manager



# Basic logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

REEL_CACHE_TTL_SECONDS = int(os.getenv("REEL_CACHE_TTL_SECONDS", "900"))
RATE_LIMIT_TTL_SECONDS = int(os.getenv("RATE_LIMIT_TTL_SECONDS", "300"))

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

    # Extract shortcode from URL
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    shortcode = parts[-1] if parts else None
    if not shortcode:
        raise ValueError("Invalid Instagram reel URL")

    cache_key = f"reel:{shortcode}"
    rate_limit_key = f"rate_limit:{shortcode}"

    cached = cache_manager.get(cache_key)
    if cache_manager.get(rate_limit_key) and cached:
        logger.info("Rate limit active; serving cached reel data.")
        return ReelData(**cached)

    L = instaloader.Instaloader()
    max_retries = 3
    delay = 5  # seconds, increase on each retry
    for attempt in range(1, max_retries + 1):
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            reel_data = ReelData(
                id=post.shortcode,
                reel_url=url,
                video_url=post.video_url if post.is_video else None,
                thumbnail_url=post.url,
                caption=post.caption,
                posted_at=post.date_utc.isoformat(),
                views=post.video_play_count if post.is_video else None,
                likes=post.likes,
                comments=post.comments
            )
            cache_manager.set(cache_key, reel_data.dict(), REEL_CACHE_TTL_SECONDS)
            cache_manager.delete(rate_limit_key)
            return reel_data
        except Exception as e:
            err_msg = str(e)
            # Detect Instagram rate limit or 401 Unauthorized
            if (
                "401 Unauthorized" in err_msg or
                "Please wait a few minutes before you try again" in err_msg or
                "429" in err_msg or
                "rate limit" in err_msg.lower()
            ):
                cache_manager.set(rate_limit_key, True, RATE_LIMIT_TTL_SECONDS)
                if cached:
                    logger.warning("Rate limited; returning cached reel data.")
                    return ReelData(**cached)
                if attempt == max_retries:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limited by Instagram. Please wait a few minutes before retrying."
                    )
                await asyncio.sleep(delay * attempt)
                continue
            raise ValueError(f"Failed to scrape reel: {err_msg}")
