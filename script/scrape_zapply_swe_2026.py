#!/usr/bin/env python3
"""
Scrape job postings from Zapply's New-Grad-Software-Engineering-Jobs-2026 GitHub repository
This adds archived SWE jobs (113+) plus fresh jobs from the 2026 new grad SWE focused repo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from datetime import datetime, timedelta
import re
import sqlite3

def parse_time_ago(time_str):
    """Convert time ago string (3h ago, 2d ago, 1mo ago) to datetime and days"""
    time_str = time_str.lower().strip()

    # Extract number and unit
    match = re.search(r'(\d+)\s*(h|d|w|mo|m)\s*ago', time_str)
    if not match:
        return None, None

    value = int(match.group(1))
    unit = match.group(2)

    # Calculate days ago
    if unit == 'h':  # hours
        days_ago = value / 24.0
    elif unit == 'd':  # days
        days_ago = value
    elif unit == 'w':  # weeks
        days_ago = value * 7
    elif unit in ['mo', 'm']:  # months
        days_ago = value * 30
    else:
        days_ago = 0

    # Calculate actual date
    date_posted = datetime.now() - timedelta(days=days_ago)

    return date_posted.strftime('%Y-%m-%d'), days_ago

def calculate_freshness_score(days_ago):
    """Calculate freshness score (0-100) based on job age"""
    if days_ago is None:
        return 50

    if days_ago < 1:  # Less than 1 day
        return 100
    elif days_ago < 7:  # Less than 1 week
        return 90
    elif days_ago < 14:  # Less than 2 weeks
        return 75
    elif days_ago < 30:  # Less than 1 month
        return 60
    elif days_ago < 60:  # Less than 2 months
        return 40
    else:  # Older than 2 months
        return 20

def scrape_zapply_swe_2026():
    """Scrape job postings from Zapply SWE 2026 GitHub repo"""

    print("="*70)
    print("🔍 SCRAPING ZAPPLY SWE 2026 GITHUB REPOSITORY")
    print("="*70)
    print("\nFetching: https://github.com/zapplyjobs/New-Grad-Software-Engineering-Jobs-2026")
    print("Expected: 113+ archived jobs + fresh postings")
    print("This may take 15-20 seconds...\n")

    # GitHub raw README URL
    url = "https://raw.githubusercontent.com/zapplyjobs/New-Grad-Software-Engineering-Jobs-2026/main/README.md"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        markdown = response.text

        print("✅ Successfully fetched README.md")

    except Exception as e:
        print(f"❌ Error fetching GitHub repo: {e}")
        return None

    # Parse markdown tables
    jobs = []

    print("\n📊 Parsing markdown tables...")

    try:
        lines = markdown.split('\n')
        in_table = False
        current_section = "active"  # or "archived"

        for i, line in enumerate(lines):
            # Detect if we're in archived section
            if 'archived' in line.lower() and 'jobs' in line.lower():
                current_section = "archived"
                continue

            # Check for table rows
            if '|' in line and not line.strip().startswith('|--'):
                parts = [p.strip() for p in line.split('|')]

                # Skip header rows and empty rows
                if len(parts) < 4 or 'Company' in line or 'Role' in line:
                    continue

                # Extract job data
                try:
                    company = parts[1] if len(parts) > 1 else "Unknown"
                    role = parts[2] if len(parts) > 2 else "Unknown"
                    location = parts[3] if len(parts) > 3 else "Unknown"
                    posted_date = parts[4] if len(parts) > 4 else "Unknown"
                    apply_link = ""

                    # Extract apply link from markdown link format
                    if len(parts) > 5:
                        apply_text = parts[5]
                        link_match = re.search(r'\[.*?\]\((.*?)\)', apply_text)
                        if link_match:
                            apply_link = link_match.group(1)

                    # Parse freshness
                    date_posted_parsed, days_ago = parse_time_ago(posted_date)
                    freshness_score = calculate_freshness_score(days_ago)

                    # Detect FAANG
                    faang_companies = ['amazon', 'meta', 'facebook', 'apple', 'netflix', 'google']
                    is_faang = any(fc in company.lower() for fc in faang_companies)

                    job = {
                        'company': company,
                        'title': role,
                        'location': location,
                        'date_posted': date_posted_parsed or posted_date,
                        'posted_time_ago': posted_date,
                        'days_ago': days_ago,
                        'freshness_score': freshness_score,
                        'url': apply_link or f"https://github.com/zapplyjobs/New-Grad-Software-Engineering-Jobs-2026",
                        'source': 'zapply_swe_2026',
                        'is_faang': is_faang,
                        'is_archived': current_section == "archived",
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    jobs.append(job)

                except Exception as e:
                    continue

        print(f"✅ Parsed {len(jobs)} job postings")

    except Exception as e:
        print(f"❌ Error parsing markdown: {e}")
        return None

    if not jobs:
        print("❌ No jobs found")
        return None

    print(f"\n✅ Successfully scraped {len(jobs)} jobs from Zapply SWE 2026 GitHub!")

    # Print breakdown
    df = pd.DataFrame(jobs)

    print(f"\n📊 Breakdown:")
    print(f"   - Total positions: {len(df)}")
    print(f"   - Active jobs: {len(df[df['is_archived'] == False])}")
    print(f"   - Archived jobs (7+ days): {len(df[df['is_archived'] == True])}")
    print(f"   - FAANG companies: {len(df[df['is_faang'] == True])}")
    print(f"   - Fresh jobs (< 1 week): {len(df[df['days_ago'] < 7])}")

    # Top companies
    print(f"\n🏢 Top 10 Companies:")
    for company, count in df['company'].value_counts().head(10).items():
        faang_badge = " [FAANG]" if any(fc in company.lower() for fc in ['amazon', 'meta', 'facebook', 'apple', 'netflix', 'google']) else ""
        print(f"   - {company}{faang_badge}: {count} positions")

    return jobs

def save_to_database(jobs, db_path="database/jobs.db"):
    """Save jobs to database in zapply_swe_2026_jobs table"""

    print(f"\n💾 Saving {len(jobs)} Zapply SWE 2026 jobs to database...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zapply_swe_2026_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                title TEXT,
                location TEXT,
                date_posted TEXT,
                posted_time_ago TEXT,
                days_ago REAL,
                freshness_score INTEGER,
                url TEXT,
                source TEXT,
                is_faang INTEGER,
                is_archived INTEGER,
                scraped_at TEXT
            )
        """)

        # Clear existing data
        cursor.execute("DELETE FROM zapply_swe_2026_jobs")
        print(f"   - Cleared existing Zapply SWE 2026 jobs from database")

        # Insert new jobs
        for job in jobs:
            cursor.execute("""
                INSERT INTO zapply_swe_2026_jobs
                (company, title, location, date_posted, posted_time_ago, days_ago,
                 freshness_score, url, source, is_faang, is_archived, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job['company'],
                job['title'],
                job['location'],
                job['date_posted'],
                job['posted_time_ago'],
                job['days_ago'],
                job['freshness_score'],
                job['url'],
                job['source'],
                1 if job['is_faang'] else 0,
                1 if job['is_archived'] else 0,
                job['scraped_at']
            ))

        conn.commit()
        conn.close()

        print(f"✅ Saved {len(jobs)} Zapply SWE 2026 jobs to database: {db_path}")

    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        raise

if __name__ == "__main__":
    jobs = scrape_zapply_swe_2026()

    if jobs:
        # Get database path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, "..", "database", "jobs.db")

        save_to_database(jobs, db_path)

        # Also save to CSV
        csv_path = os.path.join(script_dir, "..", "database", "zapply_swe_2026_jobs.csv")
        df = pd.DataFrame(jobs)
        df.to_csv(csv_path, index=False)
        print(f"✅ Also saved to CSV: {csv_path}")
