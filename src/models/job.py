from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Job:
    title: str
    company: str
    link: str
    posted_time: datetime
    source: str
    location: Optional[str] = None
    is_remote: bool = False
    
    def to_dict(self) -> dict:
        """Convert job to dictionary for CSV storage"""
        return {
            'title': self.title,
            'company': self.company,
            'link': self.link,
            'posted_time': self.posted_time.isoformat(),
            'source': self.source,
            'location': self.location or '',
            'is_remote': self.is_remote
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Job':
        """Create job from dictionary (for CSV reading)"""
        return cls(
            title=data['title'],
            company=data['company'],
            link=data['link'],
            posted_time=datetime.fromisoformat(data['posted_time']),
            source=data['source'],
            location=data['location'] if data['location'] else None,
            is_remote=data['is_remote']
        ) 