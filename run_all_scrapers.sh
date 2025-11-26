#!/bin/bash
# Master script to run all job scrapers
# Runs at 6:00 AM and 4:00 PM daily to keep jobs fresh

cd /Users/mahmoud/job-search-ai/CP494-project

echo "=========================================="
echo "Starting job scrapers at $(date)"
echo "=========================================="

# 1. Scrape JobSpy (Indeed + LinkedIn)
echo "\n[1/3] Running JobSpy scraper (Indeed + LinkedIn)..."
python3 script/scrape_real_jobs.py
echo "✅ JobSpy complete"

# 2. Scrape SimplifyJobs GitHub
echo "\n[2/3] Running SimplifyJobs GitHub scraper..."
python3 script/scrape_github_jobs.py
echo "✅ SimplifyJobs complete"

# 3. Scrape Zapply GitHub
echo "\n[3/3] Running Zapply GitHub scraper..."
python3 script/scrape_zapply_github.py
echo "✅ Zapply complete"

echo "\n=========================================="
echo "All scrapers completed at $(date)"
echo "=========================================="
