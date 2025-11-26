#!/usr/bin/env python3
"""
Scrape job postings from Zapply's New-Grad-Jobs GitHub repository
This adds 557+ curated new grad positions from 40+ top tech companies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from datetime import datetime, timedelta
import re
import sqlite3
from bs4 import BeautifulSoup

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

def scrape_zapply_github():
    """Scrape job postings from Zapply GitHub repo"""

    print("="*70)
    print("🔍 SCRAPING ZAPPLY NEW-GRAD-JOBS GITHUB REPOSITORY")
    print("="*70)
    print("\nFetching: https://github.com/zapplyjobs/New-Grad-Jobs")
    print("Expected: 557+ jobs from 40+ companies")
    print("This may take 15-20 seconds...\n")

    # GitHub raw README URL
    url = "https://raw.githubusercontent.com/zapplyjobs/New-Grad-Jobs/main/README.md"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        markdown = response.text

        print("✅ Successfully fetched README.md")

    except Exception as e:
        print(f"❌ Error fetching GitHub repo: {e}")
        return None

    # Parse markdown tables line by line
    jobs = []

    print("\n📊 Parsing markdown tables...")

    try:
        lines = markdown.split('\n')
        current_company = "Unknown"
        in_table = False
        table_header_seen = False

        for i, line in enumerate(lines):
            # Look for company headings: #### **Company Name** (count)
            if line.strip().startswith('####') and '**' in line:
                # Extract company name
                company_match = re.search(r'####\s+[🔥🟢🟦🔵📦🍎🎬⚡🎮💳₿]?\s*\*\*([A-Za-z0-9\s&\.]+)\*\*', line)
                if company_match:
                    current_company = company_match.group(1).strip()
                    in_table = False
                    table_header_seen = False
                    print(f"   Found company: {current_company}")
                continue

            # Check if this is a table separator line (|---|---|)
            if '|' in line and '---' in line:
                in_table = True
                table_header_seen = True
                continue

            # Check if this is a table header line (| Role | Location | ...)
            if '|' in line and not in_table and ('Role' in line or 'Company' in line):
                continue

            # Parse table rows (must have | and be in table context)
            if '|' in line and in_table and table_header_seen:
                # Split by pipe
                cells = [cell.strip() for cell in line.split('|')]
                cells = [c for c in cells if c]  # Remove empty cells

                # Need at least 4 cells: Role, Location, Posted, Level
                if len(cells) < 4:
                    # Check if this line ends the table (empty or non-table line)
                    if not line.strip() or not line.strip().startswith('|'):
                        in_table = False
                        table_header_seen = False
                    continue

                # Extract fields
                role = cells[0].strip()
                location = cells[1].strip()
                posted = cells[2].strip() if len(cells) > 2 else 'Unknown'
                level = cells[3].strip() if len(cells) > 3 else 'Entry-Level'
                category = cells[4].strip() if len(cells) > 4 else 'Software Engineering'
                apply_cell = cells[5].strip() if len(cells) > 5 else cells[-1].strip()

                # Extract URL from markdown link [Apply](URL)
                apply_url = None
                url_match = re.search(r'\[.*?\]\((https?://[^\)]+)\)', apply_cell)
                if url_match:
                    apply_url = url_match.group(1)

                # Skip if no role
                if not role or len(role) < 2:
                    continue

                # Parse posted time
                date_posted, days_ago = parse_time_ago(posted)
                freshness_score = calculate_freshness_score(days_ago)

                # Determine if fresh (< 1 week)
                is_fresh = days_ago is not None and days_ago < 7

                # Determine job type from role
                role_lower = role.lower()
                if 'intern' in role_lower:
                    job_type = 'internship'
                elif 'co-op' in role_lower or 'coop' in role_lower:
                    job_type = 'internship'
                elif 'contract' in role_lower:
                    job_type = 'contract'
                else:
                    job_type = 'fulltime'

                # STRICT FAANG classification - only these 7 companies
                faang_companies = ['google', 'amazon', 'apple', 'meta', 'facebook', 'microsoft', 'netflix']
                is_faang = any(comp in current_company.lower() for comp in faang_companies)

                # STRICT Tier-1 classification - only top tech unicorns (NOT banks/consulting)
                tier1_companies = ['tesla', 'nvidia', 'spacex', 'stripe', 'coinbase',
                                   'uber', 'lyft', 'airbnb', 'databricks', 'openai',
                                   'anthropic', 'snap', 'reddit', 'dropbox', 'twitch', 'x', 'twitter']
                is_tier1 = any(comp in current_company.lower() for comp in tier1_companies)

                # DO NOT mark these as FAANG/Tier-1: BMO, CIBC, RBC, TD, Scotiabank,
                # Autodesk, Canada Life, Deloitte, EY, PwC, KPMG, Accenture

                jobs.append({
                    'company': current_company,
                    'title': role,
                    'location': location,
                    'job_url': apply_url if apply_url else f"https://github.com/zapplyjobs/New-Grad-Jobs",
                    'site': 'zapply',
                    'source': 'Zapply-GitHub',
                    'posted_ago': posted,
                    'days_ago': days_ago,
                    'date_posted': date_posted if date_posted else datetime.now().strftime('%Y-%m-%d'),
                    'freshness_score': freshness_score,
                    'is_fresh': is_fresh,
                    'level': level,
                    'category': category,
                    'job_type': job_type,
                    'is_faang': is_faang,
                    'is_tier1': is_tier1,
                    'description': f"{level} position at {current_company} in {category}. " +
                                   f"Posted {posted}. " +
                                   ("FAANG company. " if is_faang else "") +
                                   ("Top-tier tech company. " if is_tier1 and not is_faang else ""),
                    'collected_at': datetime.now().isoformat()
                })

        print(f"✅ Parsed {len(jobs)} job postings")

    except Exception as e:
        print(f"❌ Error parsing tables: {e}")
        import traceback
        traceback.print_exc()
        return None

    df = pd.DataFrame(jobs)

    if len(df) == 0:
        print("❌ No jobs found in GitHub repo")
        return None

    print(f"\n✅ Successfully scraped {len(df)} jobs from Zapply GitHub!")

    print(f"\n📊 Breakdown:")
    print(f"   - Total positions: {len(df)}")
    print(f"   - Unique companies: {df['company'].nunique()}")
    print(f"   - FAANG companies: {df['is_faang'].sum()}")
    print(f"   - Tier-1 companies: {df['is_tier1'].sum()}")
    print(f"   - Fresh jobs (< 1 week): {df['is_fresh'].sum()}")
    print(f"   - Average freshness score: {df['freshness_score'].mean():.1f}/100")

    # Level distribution
    print(f"\n👥 Level Distribution:")
    level_counts = df['level'].value_counts()
    for level, count in level_counts.items():
        print(f"   - {level}: {count} jobs")

    # Category distribution
    print(f"\n📂 Category Distribution:")
    category_counts = df['category'].value_counts().head(5)
    for cat, count in category_counts.items():
        print(f"   - {cat}: {count} jobs")

    # Top companies
    print(f"\n🏢 Top 10 Companies:")
    top_companies = df['company'].value_counts().head(10)
    for company, count in top_companies.items():
        faang_tag = " [FAANG]" if any(comp in company.lower() for comp in ['google', 'amazon', 'apple', 'meta', 'microsoft']) else ""
        print(f"   - {company}{faang_tag}: {count} positions")

    # Location distribution
    print(f"\n📍 Top 10 Locations:")
    top_locations = df['location'].value_counts().head(10)
    for location, count in top_locations.items():
        print(f"   - {location}: {count} positions")

    # Freshness distribution
    print(f"\n📅 Freshness Distribution:")
    print(f"   - Fresh (< 1 day): {len(df[df['days_ago'] < 1])} jobs")
    print(f"   - Recent (< 1 week): {len(df[df['days_ago'] < 7])} jobs")
    print(f"   - Active (< 1 month): {len(df[df['days_ago'] < 30])} jobs")
    print(f"   - Older (> 1 month): {len(df[df['days_ago'] >= 30])} jobs")

    return df

def save_to_database(jobs_df, db_path="../database/jobs.db"):
    """Save Zapply jobs to database"""

    if jobs_df is None or len(jobs_df) == 0:
        print("❌ No jobs to save")
        return

    print(f"\n💾 Saving {len(jobs_df)} Zapply jobs to database...")

    try:
        # Get absolute path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_absolute_path = os.path.join(script_dir, db_path)

        conn = sqlite3.connect(db_absolute_path)

        # Create zapply_jobs table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS zapply_jobs (
                company TEXT,
                title TEXT,
                location TEXT,
                job_url TEXT,
                site TEXT,
                source TEXT,
                posted_ago TEXT,
                days_ago REAL,
                date_posted DATE,
                freshness_score INTEGER,
                is_fresh BOOLEAN,
                level TEXT,
                category TEXT,
                job_type TEXT,
                is_faang BOOLEAN,
                is_tier1 BOOLEAN,
                description TEXT,
                collected_at TIMESTAMP
            )
        """)

        # Clear existing Zapply jobs to avoid duplicates
        conn.execute("DELETE FROM zapply_jobs")
        print("   - Cleared existing Zapply jobs from database")

        # Save new jobs
        jobs_df.to_sql('zapply_jobs', conn, if_exists='append', index=False)

        conn.commit()

        # Verify
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM zapply_jobs")
        count = cursor.fetchone()[0]

        conn.close()

        print(f"✅ Saved {count} Zapply jobs to database: {db_absolute_path}")

    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()

def save_to_csv(jobs_df, csv_path="../database/zapply_jobs.csv"):
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
    """Main function to scrape and save Zapply jobs"""

    print("\n" + "="*70)
    print("🚀 ZAPPLY NEW-GRAD-JOBS GITHUB SCRAPER")
    print("="*70)
    print("\nThis script scrapes curated new grad positions from:")
    print("https://github.com/zapplyjobs/New-Grad-Jobs")
    print("\nExpected results: 557+ jobs from 40+ top tech companies")
    print("Including: Google (228+), Microsoft (28+), Amazon (23+), and more")
    print("="*70 + "\n")

    # Scrape jobs
    jobs = scrape_zapply_github()

    if jobs is None or len(jobs) == 0:
        print("\n❌ No jobs collected. Exiting.")
        return

    # Save to database
    save_to_database(jobs)

    # Save to CSV for inspection
    save_to_csv(jobs)

    print("\n" + "="*70)
    print("✅ SUCCESS! Zapply jobs scraped and saved")
    print("="*70)
    print(f"\nTotal jobs collected: {len(jobs)}")
    print(f"Database: database/jobs.db (zapply_jobs table)")
    print(f"CSV backup: database/zapply_jobs.csv")
    print("\nNext steps:")
    print("1. Integrate with unified database schema")
    print("2. Update API to serve Zapply jobs")
    print("3. Update UI to display Zapply jobs with freshness badges")
    print("4. Set up daily automation")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
