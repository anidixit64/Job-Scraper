from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from src.models.job import Job
from src.utils.logger import Logger

class BaseScraper(ABC):
    def __init__(self):
        self.logger = Logger()
        self.session = None
        self.rate_limit_delay = 2  # seconds between requests
        self.max_retries = 3
        self.retry_delay = 5  # seconds between retries
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    async def _init_session(self):
        """Initialize aiohttp session if not already initialized"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def _close_session(self):
        """Close aiohttp session if it exists"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch URL with retry logic and rate limiting"""
        await self._init_session()
        
        for attempt in range(self.max_retries):
            try:
                # Add delay between requests
                await asyncio.sleep(self.rate_limit_delay)
                
                async with self.session.get(url) as response:
                    if response.status == 429:  # Too Many Requests
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                        self.logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if response.status == 403:  # Forbidden
                        self.logger.warning(f"Access forbidden for {url}. Skipping...")
                        return None
                    
                    if response.status == 404:  # Not Found
                        self.logger.warning(f"URL not found: {url}. Skipping...")
                        return None
                    
                    if response.status != 200:
                        self.logger.warning(f"Unexpected status {response.status} for {url}")
                        return None
                    
                    return await response.text()
            
            except aiohttp.ClientError as e:
                self.logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error fetching {url}: {str(e)}")
                return None
        
        return None
    
    @abstractmethod
    async def scrape_jobs(self, job_titles: List[str]) -> List[Job]:
        """Scrape jobs for the given titles"""
        pass
    
    def is_within_last_hour(self, posted_time: datetime) -> bool:
        """Check if a job was posted within the last hour"""
        return datetime.now() - posted_time <= timedelta(hours=1)
    
    def is_valid_location(self, location: Optional[str]) -> bool:
        """Check if job location is valid (Remote or US-based)"""
        if not location:
            return False
        location = location.lower()
        return (
            'remote' in location or
            'united states' in location or
            'usa' in location or
            'us' in location
        )
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a webpage with rate limiting"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        self.logger.error(f"Error fetching {url}: Status {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
        finally:
            # Rate limiting delay
            await asyncio.sleep(1)

    def _get_search_url(self, job_title: str) -> Optional[str]:
        """Get the search URL for a job title"""
        raise NotImplementedError
    
    def _parse_jobs(self, soup: BeautifulSoup, job_title: str) -> List[Job]:
        """Parse job listings from HTML"""
        raise NotImplementedError
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string into datetime object"""
        raise NotImplementedError 