from typing import List
from fuzzywuzzy import fuzz
from src.models.job import Job

class JobMatcher:
    def __init__(self, target_titles: List[str] = None, threshold: int = 80):
        self.target_titles = [title.lower() for title in (target_titles or [])]
        self.threshold = threshold
    
    def match_jobs(self, job_title: str, jobs: List[Job]) -> List[Job]:
        """Match jobs based on title similarity"""
        matched_jobs = []
        for job in jobs:
            similarity = fuzz.ratio(job_title.lower(), job.title.lower())
            if similarity >= self.threshold:
                matched_jobs.append(job)
        return matched_jobs

    def matches_title(self, job_title: str) -> bool:
        """Check if a job title matches any of the target titles using fuzzy matching"""
        job_title = job_title.lower()
        
        for target_title in self.target_titles:
            # Try exact match first
            if target_title in job_title or job_title in target_title:
                return True
            
            # Try fuzzy matching
            ratio = fuzz.ratio(target_title, job_title)
            if ratio >= self.threshold:
                return True
            
            # Try partial ratio for better matching of substrings
            partial_ratio = fuzz.partial_ratio(target_title, job_title)
            if partial_ratio >= self.threshold:
                return True
        
        return False
    
    def filter_jobs(self, jobs: List[Job]) -> List[Job]:
        """Filter jobs based on title matching"""
        return [job for job in jobs if self.matches_title(job.title)]
    
    def get_match_quality(self, job_title: str) -> float:
        """Get the best matching score for a job title"""
        job_title = job_title.lower()
        best_score = 0
        
        for target_title in self.target_titles:
            # Try exact match
            if target_title in job_title or job_title in target_title:
                return 100.0
            
            # Try fuzzy matching
            ratio = fuzz.ratio(target_title, job_title)
            best_score = max(best_score, ratio)
            
            # Try partial ratio
            partial_ratio = fuzz.partial_ratio(target_title, job_title)
            best_score = max(best_score, partial_ratio)
        
        return best_score 