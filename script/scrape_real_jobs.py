#!/usr/bin/env python3
"""
Scrape REAL jobs using JobSpy and save to database
This replaces the mock/sample data with actual job postings
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobspy import scrape_jobs
import sqlite3
import pandas as pd
from datetime import datetime

def scrape_real_jobs(search_term="software intern", location="Toronto, ON", results_wanted=50):
    """Scrape real jobs from Indeed and LinkedIn"""

    print("="*70)
    print("🔍 SCRAPING REAL JOBS FROM JOB BOARDS")
    print("="*70)
    print(f"\nSearch term: {search_term}")
    print(f"Location: {location}")
    print(f"Target results: {results_wanted}")
    print("\nThis may take 30-60 seconds...\n")

    try:
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin"],  # Multiple sources
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=168,  # Last week
            country_indeed='Canada',
            is_remote=True  # Include remote jobs
        )

        print(f"\n✅ Successfully scraped {len(jobs)} jobs!")

        # Add collection timestamp
        jobs['collected_at'] = datetime.now().isoformat()

        # Show sample
        print("\n📊 Sample jobs found:")
        print("-" * 70)
        for idx, job in jobs.head(5).iterrows():
            print(f"{idx+1}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job['site']}")
            print(f"   URL: {job['job_url'][:60]}...")
            print()

        return jobs

    except Exception as e:
        print(f"\n❌ Error scraping jobs: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_to_database(jobs_df, db_path="../database/jobs.db"):
    """Save jobs to SQLite database"""

    if jobs_df is None or len(jobs_df) == 0:
        print("❌ No jobs to save")
        return

    print(f"\n💾 Saving {len(jobs_df)} jobs to database...")

    try:
        # Get absolute path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_absolute_path = os.path.join(script_dir, db_path)

        conn = sqlite3.connect(db_absolute_path)

        # Save to database (replace existing data)
        jobs_df.to_sql('raw_jobs', conn, if_exists='replace', index=False)

        conn.commit()

        # Verify
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_jobs")
        count = cursor.fetchone()[0]

        conn.close()

        print(f"✅ Saved {count} jobs to database: {db_absolute_path}")

    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()

def save_to_csv(jobs_df, csv_path="../database/real_jobs_collected.csv"):
    """Save jobs to CSV for inspection"""

    if jobs_df is None or len(jobs_df) == 0:
        return

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_absolute_path = os.path.join(script_dir, csv_path)

        jobs_df.to_csv(csv_absolute_path, index=False)
        print(f"✅ Also saved to CSV: {csv_absolute_path}")

    except Exception as e:
        print(f"⚠️  Could not save CSV: {e}")

def main():
    """Main function to scrape and save jobs"""

    # Configuration
    search_terms = [
        "software intern",
        "software engineer intern",
        "data science intern"
    ]

    location = "Toronto, ON"
    results_per_term = 20  # Will get ~60 jobs total

    all_jobs = []

    print("\n" + "="*70)
    print("🚀 STARTING REAL JOB SCRAPING SESSION")
    print("="*70)
    print(f"\nSearch terms: {len(search_terms)}")
    print(f"Results per term: {results_per_term}")
    print(f"Expected total: ~{len(search_terms) * results_per_term} jobs")
    print("\nThis will take 2-3 minutes...")
    print("="*70 + "\n")

    for idx, term in enumerate(search_terms, 1):
        print(f"\n[{idx}/{len(search_terms)}] Searching: '{term}'")
        print("-" * 70)

        jobs = scrape_real_jobs(
            search_term=term,
            location=location,
            results_wanted=results_per_term
        )

        if jobs is not None and len(jobs) > 0:
            all_jobs.append(jobs)

        # Rate limiting - be respectful to job boards
        if idx < len(search_terms):
            import time
            print("\n⏳ Waiting 10 seconds before next search (rate limiting)...")
            time.sleep(10)

    # Combine all results
    if not all_jobs:
        print("\n❌ No jobs collected. Check your internet connection.")
        return

    combined_jobs = pd.concat(all_jobs, ignore_index=True)

    # Remove duplicates by job URL
    original_count = len(combined_jobs)
    combined_jobs = combined_jobs.drop_duplicates(subset=['job_url'], keep='first')
    duplicates_removed = original_count - len(combined_jobs)

    print("\n" + "="*70)
    print("📊 SCRAPING COMPLETE!")
    print("="*70)
    print(f"\nTotal jobs scraped: {original_count}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Unique jobs: {len(combined_jobs)}")
    print(f"\nSources breakdown:")
    print(combined_jobs['site'].value_counts().to_string())

    # Save to database
    save_to_database(combined_jobs)

    # Save to CSV for inspection
    save_to_csv(combined_jobs)

    print("\n" + "="*70)
    print("✅ SUCCESS! Real jobs are now in your database")
    print("="*70)
    print("\nNext steps:")
    print("1. Refresh your Gradio UI (http://localhost:7860)")
    print("2. Search for jobs - you'll see REAL job postings now!")
    print("3. Click on job URLs to visit actual job pages")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
