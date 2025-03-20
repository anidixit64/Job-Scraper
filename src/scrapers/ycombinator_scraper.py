from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from ..models.job import Job
from ..utils.logger import Logger

class YCombinatorScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.base_url = "https://www.ycombinator.com/jobs"
        self.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
    
    async def scrape_jobs(self, job_titles: List[str]) -> List[Job]:
        """Scrape jobs from Y Combinator"""
        jobs = []
        try:
            for title in job_titles:
                # URL encode the job title
                encoded_title = title.replace(' ', '+')
                url = f"{self.base_url}/search?q={encoded_title}&location=United%20States"
                
                html = await self.fetch_page(url)
                if not html:
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                job_cards = soup.find_all('div', class_='job-card')
                
                for card in job_cards:
                    try:
                        # Extract job details
                        title_elem = card.find('h3', class_='job-title')
                        company_elem = card.find('div', class_='company-name')
                        location_elem = card.find('div', class_='location')
                        time_elem = card.find('div', class_='posted-time')
                        link_elem = card.find('a', class_='job-link')
                        
                        if not all([title_elem, company_elem, location_elem, time_elem, link_elem]):
                            continue
                        
                        # Parse posted time
                        time_text = time_elem.text.strip()
                        posted_time = self._parse_time(time_text)
                        
                        # Create job object
                        job = Job(
                            title=title_elem.text.strip(),
                            company=company_elem.text.strip(),
                            link=f"https://www.ycombinator.com{link_elem['href']}",
                            posted_time=posted_time,
                            source='Y Combinator',
                            location=location_elem.text.strip(),
                            is_remote='remote' in location_elem.text.lower()
                        )
                        jobs.append(job)
                    
                    except Exception as e:
                        self.logger.error(f"Error parsing Y Combinator job card: {str(e)}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error scraping Y Combinator: {str(e)}")
        
        return jobs
    
    def _parse_time(self, time_text: str) -> datetime:
        """Parse Y Combinator's time format into datetime"""
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