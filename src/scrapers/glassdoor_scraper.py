from datetime import datetime
from typing import List, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from .base_scraper import BaseScraper
from ..models.job import Job
from ..utils.logger import Logger

class GlassdoorScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.base_url = "https://www.glassdoor.com/api/jobs/search"
        self.api_key = None  # Glassdoor API key would go here
        self.rate_limit_delay = 5  # Increased delay for Glassdoor
    
    def _get_search_url(self, job_title: str) -> Optional[str]:
        """Get the search URL for a job title"""
        if not self.api_key:
            self.logger.warning("Glassdoor API key not configured. Skipping Glassdoor scraping.")
            return None
        
        # URL encode the job title
        encoded_title = job_title.replace(" ", "+")
        return f"{self.base_url}?q={encoded_title}&locT=C&locId=1&jobType=all&fromAge=1&api_key={self.api_key}"
    
    def _parse_jobs(self, soup: BeautifulSoup, job_title: str) -> List[Job]:
        """Parse job listings from HTML"""
        jobs = []
        try:
            # Parse the API response
            job_cards = soup.find_all("div", class_="jobCard")
            
            for card in job_cards:
                try:
                    title = card.find("h3", class_="jobTitle").text.strip()
                    company = card.find("div", class_="companyName").text.strip()
                    location = card.find("div", class_="location").text.strip()
                    posted_time = card.find("div", class_="postedTime").text.strip()
                    job_link = card.find("a", class_="jobLink")["href"]
                    
                    # Create job object
                    job = Job(
                        title=title,
                        company=company,
                        location=location,
                        posted_time=self._parse_time(posted_time),
                        job_link=job_link,
                        source="Glassdoor",
                        is_remote=self.is_valid_location(location)
                    )
                    
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Glassdoor job card: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing Glassdoor jobs: {str(e)}")
        
        return jobs
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string into datetime object"""
        try:
            # Glassdoor time format examples:
            # "Just now"
            # "2 hours ago"
            # "3 days ago"
            # "1 week ago"
            
            time_str = time_str.lower()
            
            if "just now" in time_str:
                return datetime.now()
            
            if "hour" in time_str:
                hours = int(time_str.split()[0])
                return datetime.now() - timedelta(hours=hours)
            
            if "day" in time_str:
                days = int(time_str.split()[0])
                return datetime.now() - timedelta(days=days)
            
            if "week" in time_str:
                weeks = int(time_str.split()[0])
                return datetime.now() - timedelta(weeks=weeks)
            
            return datetime.now()
            
        except Exception as e:
            self.logger.warning(f"Error parsing Glassdoor time: {str(e)}")
            return datetime.now()
    
    async def scrape_jobs(self, job_titles: List[str]) -> List[Job]:
        """Scrape jobs from Glassdoor"""
        jobs = []
        try:
            for title in job_titles:
                url = self._get_search_url(title)
                if not url:
                    continue
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            self.logger.error(f"Glassdoor API returned status code: {response.status}")
                            continue
                        
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        jobs.extend(self._parse_jobs(soup, title))
        
        except Exception as e:
            self.logger.error(f"Error scraping Glassdoor: {str(e)}")
        
        return jobs 