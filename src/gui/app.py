import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Callable
import threading
from datetime import datetime
import pandas as pd
import os
from src.utils.file_manager import FileManager
from src.utils.job_matcher import JobMatcher
from src.utils.logger import Logger
from src.main import JobScraper

class JobScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Job Scraper")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.job_scraper = JobScraper()
        self.file_manager = FileManager()
        self.matcher = JobMatcher()
        self.logger = Logger()
        
        self.setup_gui()
        self.is_running = False
        self.scraping_thread = None
        
        self.on_start = self.job_scraper.start
        self.on_stop = self.job_scraper.stop
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Load existing jobs if any
        self._load_jobs()
    
    def setup_gui(self):
        """Create and layout GUI widgets"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.scraping_tab = ttk.Frame(self.notebook)
        self.jobs_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.scraping_tab, text="Scraping")
        self.notebook.add(self.jobs_tab, text="Jobs")
        
        self._setup_scraping_tab()
        self._setup_jobs_tab()
    
    def _setup_scraping_tab(self):
        """Setup the scraping control tab"""
        # Main frame
        main_frame = ttk.Frame(self.scraping_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Job titles input
        ttk.Label(main_frame, text="Enter job titles (one per line):").pack(anchor=tk.W)
        self.titles_text = scrolledtext.ScrolledText(main_frame, width=50, height=10)
        self.titles_text.pack(fill=tk.X, pady=5)
        
        # Load saved titles
        saved_titles = self.file_manager.load_job_titles()
        if saved_titles:
            self.titles_text.insert(tk.END, "\n".join(saved_titles))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start", command=self._start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self._stop_scraping, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Log display
        ttk.Label(main_frame, text="Log:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(main_frame, width=70, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _setup_jobs_tab(self):
        """Setup the jobs viewer tab"""
        # Create treeview
        self.tree = ttk.Treeview(self.jobs_tab, columns=("Title", "Company", "Location", "Posted", "Source", "Remote"), show="headings")
        
        # Configure columns
        self.tree.heading("Title", text="Title", command=lambda: self._sort_jobs("Title"))
        self.tree.heading("Company", text="Company", command=lambda: self._sort_jobs("Company"))
        self.tree.heading("Location", text="Location", command=lambda: self._sort_jobs("Location"))
        self.tree.heading("Posted", text="Posted", command=lambda: self._sort_jobs("Posted"))
        self.tree.heading("Source", text="Source", command=lambda: self._sort_jobs("Source"))
        self.tree.heading("Remote", text="Remote", command=lambda: self._sort_jobs("Remote"))
        
        # Set column widths
        self.tree.column("Title", width=200)
        self.tree.column("Company", width=150)
        self.tree.column("Location", width=100)
        self.tree.column("Posted", width=100)
        self.tree.column("Source", width=100)
        self.tree.column("Remote", width=50)
        
        # Add scrollbars
        yscroll = ttk.Scrollbar(self.jobs_tab, orient=tk.VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(self.jobs_tab, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        self.jobs_tab.grid_rowconfigure(0, weight=1)
        self.jobs_tab.grid_columnconfigure(0, weight=1)
        
        # Add refresh button
        refresh_button = ttk.Button(self.jobs_tab, text="Refresh", command=self._load_jobs)
        refresh_button.grid(row=2, column=0, pady=5)
    
    def _load_jobs(self):
        """Load jobs from CSV files into the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get all CSV files in the jobs directory
        jobs_dir = "data/jobs"
        if not os.path.exists(jobs_dir):
            return
        
        all_jobs = []
        for filename in os.listdir(jobs_dir):
            if filename.endswith(".csv"):
                filepath = os.path.join(jobs_dir, filename)
                try:
                    df = pd.read_csv(filepath)
                    all_jobs.append(df)
                except Exception as e:
                    self.logger.error(f"Error reading {filename}: {str(e)}")
        
        if all_jobs:
            # Combine all jobs
            combined_df = pd.concat(all_jobs, ignore_index=True)
            
            # Sort by posted time (newest first)
            combined_df = combined_df.sort_values("Posted", ascending=False)
            
            # Add to treeview
            for _, row in combined_df.iterrows():
                self.tree.insert("", "end", values=(
                    row["Title"],
                    row["Company"],
                    row["Location"],
                    row["Posted"],
                    row["Source"],
                    "Yes" if row["Is Remote"] else "No"
                ))
    
    def _sort_jobs(self, column):
        """Sort jobs by the specified column"""
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        items.sort()
        
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)
    
    def _on_closing(self):
        """Handle window closing event"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Scraping is still running. Are you sure you want to quit?"):
                self._stop_scraping()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def _get_job_titles(self) -> List[str]:
        """Get non-empty job titles from text area"""
        return [title.strip() for title in self.titles_text.get("1.0", tk.END).splitlines() if title.strip()]
    
    def _start_scraping(self):
        """Start the job scraping process"""
        titles = self._get_job_titles()
        if not titles:
            messagebox.showerror("Error", "Please enter at least one job title")
            return
        
        if len(titles) > 10:
            messagebox.showerror("Error", "Maximum 10 job titles allowed")
            return
        
        # Save titles
        self.file_manager.save_job_titles(titles)
        
        # Update UI
        self.status_var.set("Running")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True
        
        # Start scraping
        self.on_start(titles)
        self.logger.info(f"Started scraping with titles: {titles}")
    
    def _stop_scraping(self):
        """Stop the job scraping process"""
        # Update UI
        self.status_var.set("Stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_running = False
        
        # Stop scraping
        self.on_stop()
        self.logger.info("Stopped scraping")
    
    def update_status(self, status: str):
        """Update the status label"""
        self.status_var.set(status)
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop() 