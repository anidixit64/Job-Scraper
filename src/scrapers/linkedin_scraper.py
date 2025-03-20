import os
from datetime import datetime
from typing import List
import aiohttp
from dotenv import load_dotenv
from .base_scraper import BaseScraper
from ..models.job import Job
from ..utils.logger import Logger

class LinkedInScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        load_dotenv()
        self.api_key = os.getenv('LINKEDIN_API_KEY')
        self.api_url = "https://api.linkedin.com/v2/jobs"
        
        if not self.api_key:
            self.logger.warning("LinkedIn API key not found. LinkedIn scraping will be disabled.")
    
    async def scrape_jobs(self, job_titles: List[str]) -> List[Job]:
        """Scrape jobs from LinkedIn"""
        if not self.api_key:
            return []
        
        jobs = []
        try:
            async with self.session as session:
                for title in job_titles:
                    params = {
                        'keywords': title,
                        'location': 'United States',
                        'timePosted': 'r86400',  # Last 24 hours
                        'limit': 100
                    }
                    
                    headers = {
                        'Authorization': f'Bearer {self.api_key}',
                        'X-Restli-Protocol-Version': '2.0.0'
                    }
                    
                    async with session.get(
                        self.api_url,
                        params=params,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            for job_data in data.get('elements', []):
                                job = Job(
                                    title=job_data.get('title', ''),
                                    company=job_data.get('companyName', ''),
                                    link=job_data.get('applyUrl', ''),
                                    posted_time=datetime.fromtimestamp(
                                        job_data.get('listedAt', 0) / 1000
                                    ),
                                    source='LinkedIn',
                                    location=job_data.get('location', ''),
                                    is_remote='remote' in job_data.get('location', '').lower()
                                )
                                jobs.append(job)
                        else:
                            self.logger.error(
                                f"LinkedIn API error: {response.status} - {await response.text()}"
                            )
        
        except Exception as e:
            self.logger.error(f"Error scraping LinkedIn: {str(e)}")
        
        return jobs 