from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from ..models.job import Job
from ..utils.logger import Logger

class BuiltInScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.base_url = "https://builtin.com/jobs"
        self.regions = [
            "remote",
            "new-york",
            "san-francisco",
            "los-angeles",
            "chicago",
            "boston",
            "seattle",
            "austin",
            "denver",
            "atlanta"
        ]
    
    async def scrape_jobs(self, job_titles: List[str]) -> List[Job]:
        """Scrape jobs from BuiltIn"""
        jobs = []
        try:
            for title in job_titles:
                for region in self.regions:
                    url = f"{self.base_url}/{region}?q={title}"
                    html = await self.fetch_page(url)
                    if not html:
                        continue
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    job_cards = soup.find_all('div', class_='job-card')
                    
                    for card in job_cards:
                        try:
                            # Extract job details
                            title_elem = card.find('h2', class_='job-card__title')
                            company_elem = card.find('div', class_='job-card__company')
                            location_elem = card.find('div', class_='job-card__location')
                            time_elem = card.find('div', class_='job-card__time')
                            link_elem = card.find('a', class_='job-card__link')
                            
                            if not all([title_elem, company_elem, location_elem, time_elem, link_elem]):
                                continue
                            
                            # Parse posted time
                            time_text = time_elem.text.strip()
                            posted_time = self._parse_time(time_text)
                            
                            # Create job object
                            job = Job(
                                title=title_elem.text.strip(),
                                company=company_elem.text.strip(),
                                link=f"https://builtin.com{link_elem['href']}",
                                posted_time=posted_time,
                                source='BuiltIn',
                                location=location_elem.text.strip(),
                                is_remote=region == 'remote'
                            )
                            jobs.append(job)
                        
                        except Exception as e:
                            self.logger.error(f"Error parsing BuiltIn job card: {str(e)}")
                            continue
        
        except Exception as e:
            self.logger.error(f"Error scraping BuiltIn: {str(e)}")
        
        return jobs
    
    def _parse_time(self, time_text: str) -> datetime:
        """Parse BuiltIn's time format into datetime"""
        now = datetime.now()
        
        if 'hour' in time_text:
            hours = int(time_text.split()[0])
            return now - timedelta(hours=hours)
        elif 'day' in time_text:
            days = int(time_text.split()[0])
            return now - timedelta(days=days)
        elif 'week' in time_text:
            weeks = int(time_text.split()[0])
            return now - timedelta(weeks=weeks)
        else:
            return now 