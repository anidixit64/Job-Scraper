import os
import csv
from datetime import datetime, timedelta
from typing import List
import pandas as pd
from src.models.job import Job
import yaml

class FileManager:
    def __init__(self):
        self.data_dir = "data"
        self.config_file = "config.yaml"
        self.titles_file = "job_titles.txt"
        self.jobs_dir = os.path.join(self.data_dir, "jobs")
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        os.makedirs(self.jobs_dir, exist_ok=True)
    
    def save_job_titles(self, titles: List[str]):
        """Save job titles to CSV"""
        df = pd.DataFrame(titles, columns=['title'])
        df.to_csv(self.titles_file, index=False)
    
    def load_job_titles(self) -> List[str]:
        """Load job titles from CSV"""
        if not os.path.exists(self.titles_file):
            return []
        df = pd.read_csv(self.titles_file)
        return df['title'].tolist()
    
    def save_jobs(self, jobs: List[Job]):
        """Save jobs to a new hourly file"""
        if not jobs:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobs_{timestamp}.csv"
        filepath = os.path.join(self.jobs_dir, filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'title', 'company', 'link', 'posted_time',
                'source', 'location', 'is_remote'
            ])
            writer.writeheader()
            for job in jobs:
                writer.writerow(job.to_dict())
    
    def cleanup_old_files(self, hours: int = 24):
        """Delete job files older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for filename in os.listdir(self.jobs_dir):
            if not filename.endswith('.csv'):
                continue
                
            filepath = os.path.join(self.jobs_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getctime(filepath))
            
            if file_time < cutoff_time:
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting {filepath}: {str(e)}")
    
    def get_latest_jobs(self) -> List[Job]:
        """Get the most recent jobs from the latest file"""
        files = [f for f in os.listdir(self.jobs_dir) if f.endswith('.csv')]
        if not files:
            return []
        
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.jobs_dir, x)))
        filepath = os.path.join(self.jobs_dir, latest_file)
        
        jobs = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(Job.from_dict(row))
        
        return jobs 