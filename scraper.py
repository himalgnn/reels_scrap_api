"""
High-performance Instagram Reels scraper using Playwright with network interception.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, Page, Response, TimeoutError as PlaywrightTimeout

# Fix for Windows asyncio event loop policy - MUST be set before any asyncio operations
try:
    asyncio.get_event_loop_policy()
except RuntimeError:
    # No event loop exists, set policy before creating one
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger(__name__)


class ScraperStatus:
    """Status codes for scraper results."""
    SUCCESS = "SUCCESS"
    PRIVATE = "PRIVATE"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"
    RATE_LIMITED = "RATE_LIMITED"


class InstagramScraper:
    """High-performance Instagram scraper using Playwright."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.graphql_data: List[Dict] = []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.launch_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()

    async def launch_browser(self):
        """Launch Chromium browser in headless mode (more stable on Windows)."""
        logger.info("Launching Chromium browser...")

        # Create new event loop with WindowsSelector policy for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-gpu'
                ]
            )
            logger.info("Browser launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {str(e)}")
            raise RuntimeError(f"Failed to launch browser: {str(e)}")
        finally:
            loop.close()

    async def close_browser(self):
        """Close browser gracefully."""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
            
    async def _intercept_graphql_response(self, response: Response):
        """
        Intercept GraphQL API responses to extract reel data efficiently.
        Instagram uses GraphQL endpoints for data fetching.
        """
        try:
            url = response.url
            
            # Instagram GraphQL endpoints
            if "graphql/query" in url or "api/v1/feed" in url:
                if response.status == 200:
                    try:
                        data = await response.json()
                        self.graphql_data.append(data)
                        logger.debug(f"Intercepted GraphQL response: {url[:100]}...")
                    except Exception as e:
                        logger.debug(f"Failed to parse response as JSON: {e}")
        except Exception as e:
            logger.debug(f"Error intercepting response: {e}")
            
    async def _extract_shared_data(self, page: Page) -> Optional[Dict]:
        """
        Extract window._sharedData from page scripts.
        This is faster than DOM scraping.
        """
        try:
            shared_data = await page.evaluate("""
                () => {
                    if (window._sharedData) {
                        return window._sharedData;
                    }
                    return null;
                }
            """)
            return shared_data
        except Exception as e:
            logger.debug(f"Failed to extract _sharedData: {e}")
            return None
            
    async def _check_account_status(self, page: Page) -> Tuple[str, Optional[str]]:
        """
        Check if account is private, doesn't exist, or is accessible.
        
        Returns:
            Tuple of (status, message)
        """
        try:
            # Wait a bit for page to load
            await asyncio.sleep(2)
            
            # Check for "Sorry, this page isn't available"
            not_found_selectors = [
                'text="Sorry, this page isn\'t available"',
                'text="The link you followed may be broken"',
            ]
            
            for selector in not_found_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    if element:
                        logger.info("Account not found")
                        return ScraperStatus.NOT_FOUND, "Account does not exist"
                except:
                    pass
                    
            # Check for private account
            private_selectors = [
                'text="This Account is Private"',
                'h2:has-text("This account is private")',
            ]
            
            for selector in private_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    if element:
                        logger.info("Account is private")
                        return ScraperStatus.PRIVATE, "Account is private"
                except:
                    pass
                    
            # Check for rate limiting
            if "challenge" in page.url or "login" in page.url:
                logger.warning("Rate limited or login required")
                return ScraperStatus.RATE_LIMITED, "Rate limited or login required"
                
            return ScraperStatus.SUCCESS, None
            
        except Exception as e:
            logger.error(f"Error checking account status: {e}")
            return ScraperStatus.ERROR, str(e)
            
    async def _smart_scroll(self, page: Page, target_count: int, max_scrolls: int = 50) -> int:
        """
        Efficient scrolling to load reels dynamically.
        Uses exponential backoff when no new content loads.
        
        Returns:
            Number of reels loaded
        """
        logger.info(f"Starting smart scroll to load {target_count} reels...")
        
        previous_height = 0
        scroll_count = 0
        no_change_count = 0
        
        while scroll_count < max_scrolls:
            # Get current scroll height
            current_height = await page.evaluate("document.body.scrollHeight")
            
            # Check if we've loaded enough reels
            reel_count = await page.evaluate("""
                () => {
                    const reelLinks = document.querySelectorAll('a[href*="/reel/"]');
                    return reelLinks.length;
                }
            """)
            
            logger.debug(f"Scroll {scroll_count + 1}: Found {reel_count} reels")
            
            if reel_count >= target_count:
                logger.info(f"Target reached: {reel_count} reels loaded")
                return reel_count
                
            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Wait for content to load (adaptive wait)
            if current_height == previous_height:
                no_change_count += 1
                wait_time = min(0.5 * (2 ** no_change_count), 5)  # Exponential backoff, max 5s
                logger.debug(f"No new content, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                
                # If no change after 3 attempts, we've reached the end
                if no_change_count >= 3:
                    logger.info(f"No more content to load. Final count: {reel_count}")
                    return reel_count
            else:
                no_change_count = 0
                await asyncio.sleep(0.5)  # Fast scroll when content is loading
                
            previous_height = current_height
            scroll_count += 1
            
        logger.info(f"Max scrolls reached. Final count: {reel_count}")
        return reel_count
        
    async def _extract_reels_from_page(self, page: Page) -> List[Dict]:
        """
        Extract reel data from the page using multiple strategies.
        Priority: GraphQL data > _sharedData > DOM scraping
        """
        reels = []
        
        # Strategy 1: Use intercepted GraphQL data (fastest)
        if self.graphql_data:
            logger.info("Extracting from intercepted GraphQL data...")
            reels = self._parse_graphql_data(self.graphql_data)
            if reels:
                logger.info(f"Extracted {len(reels)} reels from GraphQL data")
                return reels
                
        # Strategy 2: Extract from window._sharedData
        logger.info("Extracting from _sharedData...")
        shared_data = await self._extract_shared_data(page)
        if shared_data:
            reels = self._parse_shared_data(shared_data)
            if reels:
                logger.info(f"Extracted {len(reels)} reels from _sharedData")
                return reels
                
        # Strategy 3: DOM scraping (slowest, fallback)
        logger.info("Falling back to DOM scraping...")
        reels = await self._scrape_reels_from_dom(page)
        logger.info(f"Extracted {len(reels)} reels from DOM")
        
        return reels
        
    def _parse_graphql_data(self, graphql_responses: List[Dict]) -> List[Dict]:
        """Parse GraphQL responses to extract reel data."""
        reels = []
        
        for response in graphql_responses:
            try:
                # Instagram's GraphQL structure varies, handle multiple formats
                if "data" in response:
                    data = response["data"]
                    
                    # Check for user profile data
                    if "user" in data:
                        user_data = data["user"]
                        if "edge_owner_to_timeline_media" in user_data:
                            edges = user_data["edge_owner_to_timeline_media"].get("edges", [])
                            for edge in edges:
                                node = edge.get("node", {})
                                if node.get("is_video"):
                                    reel = self._parse_media_node(node)
                                    if reel:
                                        reels.append(reel)
                                        
            except Exception as e:
                logger.debug(f"Error parsing GraphQL response: {e}")
                
        return reels
        
    def _parse_shared_data(self, shared_data: Dict) -> List[Dict]:
        """Parse window._sharedData to extract reel data."""
        reels = []
        
        try:
            entry_data = shared_data.get("entry_data", {})
            
            # Profile page data
            if "ProfilePage" in entry_data:
                profile_page = entry_data["ProfilePage"][0]
                user_data = profile_page.get("graphql", {}).get("user", {})
                
                # Get timeline media
                timeline = user_data.get("edge_owner_to_timeline_media", {})
                edges = timeline.get("edges", [])
                
                for edge in edges:
                    node = edge.get("node", {})
                    if node.get("is_video"):
                        reel = self._parse_media_node(node)
                        if reel:
                            reels.append(reel)
                            
        except Exception as e:
            logger.debug(f"Error parsing _sharedData: {e}")
            
        return reels
        
    def _parse_media_node(self, node: Dict) -> Optional[Dict]:
        """Parse a media node into reel data structure."""
        try:
            shortcode = node.get("shortcode")
            if not shortcode:
                return None
                
            # Extract timestamp
            timestamp = node.get("taken_at_timestamp")
            posted_at = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            
            # Extract engagement metrics
            edge_liked_by = node.get("edge_liked_by", {})
            edge_media_to_comment = node.get("edge_media_to_comment", {})
            
            reel_data = {
                "id": shortcode,
                "reel_url": f"https://www.instagram.com/reel/{shortcode}/",
                "video_url": node.get("video_url"),
                "thumbnail_url": node.get("thumbnail_src") or node.get("display_url"),
                "caption": self._extract_caption(node),
                "posted_at": posted_at.isoformat(),
                "views": node.get("video_view_count"),
                "likes": edge_liked_by.get("count"),
                "comments": edge_media_to_comment.get("count"),
            }
            
            return reel_data
            
        except Exception as e:
            logger.debug(f"Error parsing media node: {e}")
            return None
            
    def _extract_caption(self, node: Dict) -> Optional[str]:
        """Extract caption from media node."""
        try:
            edges = node.get("edge_media_to_caption", {}).get("edges", [])
            if edges:
                return edges[0].get("node", {}).get("text")
        except:
            pass
        return None
        
    async def _scrape_reels_from_dom(self, page: Page) -> List[Dict]:
        """Fallback: Scrape reel data from DOM elements."""
        reels = []
        
        try:
            # Extract all reel links
            reel_links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="/reel/"]'));
                    return links.map(link => link.href);
                }
            """)
            
            # Deduplicate
            unique_links = list(set(reel_links))
            logger.info(f"Found {len(unique_links)} unique reel links in DOM")
            
            for link in unique_links:
                # Extract shortcode from URL
                match = re.search(r'/reel/([^/]+)', link)
                if match:
                    shortcode = match.group(1)
                    reels.append({
                        "id": shortcode,
                        "reel_url": f"https://www.instagram.com/reel/{shortcode}/",
                        "video_url": None,  # Not available from DOM
                        "thumbnail_url": f"https://www.instagram.com/p/{shortcode}/media/?size=l",
                        "caption": None,
                        "posted_at": datetime.now().isoformat(),
                        "views": None,
                        "likes": None,
                        "comments": None,
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping DOM: {e}")
            
        return reels
        
    async def scrape_reels(self, username: str, limit: int = 30) -> Tuple[List[Dict], str, Optional[str]]:
        """
        Scrape Instagram reels from a user profile.
        
        Args:
            username: Instagram username
            limit: Maximum number of reels to scrape
            
        Returns:
            Tuple of (reels_list, status, error_message)
            - reels_list: List of reel dictionaries
            - status: ScraperStatus constant
            - error_message: Error message if status is not SUCCESS
        """
        if not self.browser:
            await self.launch_browser()
            
        context = None
        page = None
        
        try:
            # Create browser context with realistic settings
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                locale="en-US",
            )
            
            page = await context.new_page()
            
            # Set up network interception
            page.on("response", self._intercept_graphql_response)
            
            # Navigate to profile reels page
            url = f"https://www.instagram.com/{username}/reels/"
            logger.info(f"Navigating to {url}")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Check account status
            status, message = await self._check_account_status(page)
            if status != ScraperStatus.SUCCESS:
                return [], status, message
                
            # Smart scroll to load reels
            await self._smart_scroll(page, limit)
            
            # Extract reels using multiple strategies
            reels = await self._extract_reels_from_page(page)
            
            # Limit results
            reels = reels[:limit]
            
            logger.info(f"Successfully scraped {len(reels)} reels for @{username}")
            return reels, ScraperStatus.SUCCESS, None
            
        except PlaywrightTimeout as e:
            logger.error(f"Timeout error: {e}")
            return [], ScraperStatus.ERROR, "Request timeout"
            
        except Exception as e:
            logger.error(f"Error scraping reels: {e}", exc_info=True)
            return [], ScraperStatus.ERROR, str(e)
            
        finally:
            # Clean up
            if page:
                await page.close()
            if context:
                await context.close()
            self.graphql_data.clear()


async def scrape_reels(username: str, limit: int = 30) -> Tuple[List[Dict], str, Optional[str]]:
    """
    Convenience function to scrape reels without managing context.

    Args:
        username: Instagram username
        limit: Maximum number of reels to scrape (default: 30)

    Returns:
        Tuple of (reels_list, status, error_message)
    """
    # Set Windows event loop policy if needed
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create one with proper policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        async with InstagramScraper(headless=True) as scraper:
            return await scraper.scrape_reels(username, limit)
    except Exception as e:
        logger.error(f"Error in scrape_reels convenience function: {e}")
        return [], ScraperStatus.ERROR, str(e)
