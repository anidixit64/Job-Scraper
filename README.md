# Job Scraper

A comprehensive job scraping tool that monitors multiple job sites for new opportunities matching your specified job titles.

## Features

- Interactive GUI for managing job titles
- Scrapes multiple job sites (LinkedIn, Glassdoor, Monster, etc.)
- Runs in the background between 7 AM and 1 AM
- Creates hourly job dumps with automatic cleanup after 24 hours
- Fuzzy matching for job titles
- Location filtering (Remote/US-based jobs)
- Real-time status monitoring
- Detailed error logging

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory with your API keys (if using any job site APIs)

## Usage

1. Run the application:
   ```bash
   python src/main.py
   ```
2. Enter up to 10 job titles in the GUI
3. The scraper will automatically start running in the background
4. Job results will be saved in the `data/jobs` directory
5. To stop the scraper, use the stop button in the GUI

## Job Sites Supported

- LinkedIn (API)
- Glassdoor
- Monster
- ZipRecruiter
- BuiltIn
- Google Jobs
- Levels.fyi
- Lever.co
- Simplify
- Welcome to the Jungle / Otta

## File Structure

- `data/job_titles.csv`: Stores user's preferred job titles
- `data/jobs/`: Contains hourly job dumps (automatically cleaned up after 24 hours)
- `logs/`: Contains application logs

## Note

The scraper respects rate limits and robots.txt for all job sites. Some sites may require API keys for access.