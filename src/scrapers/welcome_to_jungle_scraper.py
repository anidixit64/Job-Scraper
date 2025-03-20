from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from ..models.job import Job
from ..utils.logger import Logger

class WelcomeToJungleScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.base_url = "https://www.welcometothejungle.com/en/jobs"
        self.headers.update({
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest'
        })
    
    async def scrape_jobs(self, job_titles: List[str]) -> List[Job]:
        """Scrape jobs from Welcome to the Jungle"""
        jobs = []
        try:
            for title in job_titles:
                # Welcome to the Jungle uses a search API
                search_url = f"{self.base_url}/api/search"
                params = {
                    'query': title,
                    'location': 'United States',
                    'timeRange': '1h',
                    'page': 1,
                    'limit': 100
                }
                
                async with self.session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for job_data in data.get('jobs', []):
                            try:
                                job = Job(
                                    title=job_data.get('title', ''),
                                    company=job_data.get('company', {}).get('name', ''),
                                    link=f"https://www.welcometothejungle.com/en/jobs/{job_data.get('slug', '')}",
                                    posted_time=datetime.fromisoformat(
                                        job_data.get('publishedAt', '').replace('Z', '+00:00')
                                    ),
                                    source='Welcome to the Jungle',
                                    location=job_data.get('location', {}).get('city', ''),
                                    is_remote=job_data.get('location', {}).get('isRemote', False)
                                )
                                jobs.append(job)
                            except Exception as e:
                                self.logger.error(f"Error parsing Welcome to the Jungle job: {str(e)}")
                                continue
                    else:
                        self.logger.error(
                            f"Welcome to the Jungle API error: {response.status} - {await response.text()}"
                        )
        
        except Exception as e:
            self.logger.error(f"Error scraping Welcome to the Jungle: {str(e)}")
        
        return jobs 