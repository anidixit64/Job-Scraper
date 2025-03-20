import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Create necessary directories
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)

from src.gui.app import JobScraperGUI

if __name__ == "__main__":
    app = JobScraperGUI()
    app.run() 