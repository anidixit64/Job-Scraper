from datetime import datetime
from typing import List
import aiohttp
from .base_scraper import BaseScraper
from ..models.job import Job
from ..utils.logger import Logger

class SimplifyScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.base_url = "https://api.simplify.jobs/v1"
        self.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    async def scrape_jobs(self, job_titles: List[str]) -> List[Job]:
        """Scrape jobs from Simplify"""
        jobs = []
        try:
            for title in job_titles:
                # Simplify uses a GraphQL API
                query = {
                    "query": """
                    query SearchJobs($query: String!, $location: String!, $timeRange: String!) {
                        jobs(query: $query, location: $location, timeRange: $timeRange) {
                            id
                            title
                            company {
                                name
                            }
                            location
                            postedAt
                            applyUrl
                            isRemote
                        }
                    }
                    """,
                    "variables": {
                        "query": title,
                        "location": "United States",
                        "timeRange": "1h"
                    }
                }
                
                async with self.session.post(
                    f"{self.base_url}/graphql",
                    json=query
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        for job_data in data.get('data', {}).get('jobs', []):
                            try:
                                job = Job(
                                    title=job_data.get('title', ''),
                                    company=job_data.get('company', {}).get('name', ''),
                                    link=job_data.get('applyUrl', ''),
                                    posted_time=datetime.fromisoformat(
                                        job_data.get('postedAt', '').replace('Z', '+00:00')
                                    ),
                                    source='Simplify',
                                    location=job_data.get('location', ''),
                                    is_remote=job_data.get('isRemote', False)
                                )
                                jobs.append(job)
                            except Exception as e:
                                self.logger.error(f"Error parsing Simplify job: {str(e)}")
                                continue
                    else:
                        self.logger.error(
                            f"Simplify API error: {response.status} - {await response.text()}"
                        )
        
        except Exception as e:
            self.logger.error(f"Error scraping Simplify: {str(e)}")
        
        return jobs 