import asyncio
import schedule
import time
from datetime import datetime
from typing import List, Optional
import threading
import os
import sys
import signal
from src.utils.file_manager import FileManager
from src.utils.job_matcher import JobMatcher
from src.utils.logger import Logger
from src.scrapers.builtin_scraper import BuiltInScraper
from src.scrapers.levels_scraper import LevelsScraper
from src.scrapers.hiring_cafe_scraper import HiringCafeScraper
from src.scrapers.ycombinator_scraper import YCombinatorScraper
from src.scrapers.wellfound_scraper import WellfoundScraper
from src.scrapers.stackoverflow_scraper import StackOverflowScraper
from src.scrapers.dice_scraper import DiceScraper
from src.scrapers.crunchbase_scraper import CrunchbaseScraper
from src.scrapers.venturefizz_scraper import VentureFizzScraper
from src.scrapers.techcrunch_scraper import TechCrunchScraper
from src.scrapers.venturebeat_scraper import VentureBeatScraper
from src.models.job import Job

class JobScraper:
    def __init__(self):
        self.file_manager = FileManager()
        self.logger = Logger()
        self.is_running = False
        self.scraping_thread: Optional[threading.Thread] = None
        self.job_titles: List[str] = []
        self.matcher: Optional[JobMatcher] = None
        self.pid_file = "job_scraper.pid"
        
        # Initialize scrapers (only non-API sites)
        self.scrapers = [
            BuiltInScraper(),        # Web scraping
            LevelsScraper(),         # Web scraping
            HiringCafeScraper(),     # Web scraping
            YCombinatorScraper(),    # Web scraping
            WellfoundScraper(),      # Web scraping
            StackOverflowScraper(),  # Web scraping
            DiceScraper(),           # Web scraping
            CrunchbaseScraper(),     # Web scraping
            VentureFizzScraper(),    # Web scraping
            TechCrunchScraper(),     # Web scraping
            VentureBeatScraper()     # Web scraping
        ]
        
        # Load saved job titles if they exist
        saved_titles = self.file_manager.load_job_titles()
        if saved_titles:
            self.job_titles = saved_titles
            self.matcher = JobMatcher(saved_titles)
            self.is_running = True
            self._start_scraping_thread()
    
    def _start_scraping_thread(self):
        """Start the scraping thread"""
        self.scraping_thread = threading.Thread(target=self._scraping_loop)
        self.scraping_thread.daemon = True
        self.scraping_thread.start()
    
    def _save_pid(self):
        """Save the process ID to a file"""
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def _remove_pid(self):
        """Remove the PID file"""
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
    
    def _is_working_hours(self) -> bool:
        """Check if current time is within working hours (7 AM - 1 AM)"""
        current_hour = datetime.now().hour
        return 7 <= current_hour or current_hour < 1
    
    async def _scrape_jobs(self):
        """Scrape jobs from all sources"""
        if not self.matcher:
            return
        
        all_jobs: List[Job] = []
        
        # Run scrapers with delay between each
        for scraper in self.scrapers:
            try:
                jobs = await scraper.scrape_jobs(self.job_titles)
                all_jobs.extend(jobs)
                
                # Add delay between scrapers to avoid overwhelming servers
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in {scraper.__class__.__name__}: {str(e)}")
                continue
        
        # Filter jobs based on titles and location
        filtered_jobs = self.matcher.filter_jobs(all_jobs)
        filtered_jobs = [
            job for job in filtered_jobs
            if job.is_remote or self.matcher.is_valid_location(job.location)
        ]
        
        # Save jobs
        if filtered_jobs:
            self.file_manager.save_jobs(filtered_jobs)
            self.logger.info(f"Saved {len(filtered_jobs)} new jobs")
    
    def _scraping_loop(self):
        """Main scraping loop"""
        while self.is_running:
            try:
                # Run scraping tasks
                asyncio.run(self._scrape_jobs())
                
                # Wait for an hour before next scrape
                for _ in range(3600):  # 1 hour = 3600 seconds
                    if not self.is_running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in scraping loop: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying on error
    
    def start(self, job_titles: List[str]):
        """Start the job scraping process"""
        if self.is_running:
            return
        
        self.job_titles = job_titles
        self.matcher = JobMatcher(job_titles)
        self.is_running = True
        
        # Save job titles
        self.file_manager.save_job_titles(job_titles)
        
        # Save PID
        self._save_pid()
        
        # Start scraping thread
        self._start_scraping_thread()
        
        self.logger.info(f"Started scraping for titles: {', '.join(job_titles)}")
    
    def stop(self):
        """Stop the job scraping process"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("Stopping job scraping process")
        
        if self.scraping_thread and self.scraping_thread.is_alive():
            self.scraping_thread.join(timeout=5)
        
        self._remove_pid()

def run_as_daemon():
    """Run the scraper as a daemon process"""
    # Create a new process
    pid = os.fork()
    
    if pid > 0:
        # Parent process
        sys.exit(0)
    
    # Child process
    os.setsid()
    os.umask(0)
    
    # Create a new process again to ensure we're not a session leader
    pid = os.fork()
    
    if pid > 0:
        # Parent process
        sys.exit(0)
    
    # Child process
    os.chdir('/')
    
    # Close standard file descriptors
    sys.stdout.close()
    sys.stderr.close()
    sys.stdin.close()
    
    # Start the scraper
    scraper = JobScraper()
    
    # Handle signals
    def signal_handler(signum, frame):
        scraper.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep the process running
    while True:
        time.sleep(1)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        run_as_daemon()
    else:
        scraper = JobScraper()
        
        def on_start(titles: List[str]):
            scraper.start(titles)
        
        def on_stop():
            scraper.stop()
        
        # Create and run GUI
        gui = JobScraperGUI(on_start, on_stop)
        gui.run()

if __name__ == "__main__":
    main() 