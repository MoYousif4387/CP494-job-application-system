#!/usr/bin/env python3
"""
Scrape job postings from SimplifyJobs/New-Grad-Positions GitHub repository
This adds ~325+ curated new grad positions to our database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from datetime import datetime
import re
import sqlite3
from bs4 import BeautifulSoup

def scrape_simplify_jobs_github():
    """Scrape job postings from SimplifyJobs GitHub repo"""

    print("="*70)
    print("🔍 SCRAPING SIMPLIFYJOBS GITHUB REPOSITORY")
    print("="*70)
    print("\nFetching: https://github.com/SimplifyJobs/New-Grad-Positions")
    print("This may take 10-20 seconds...\n")

    # GitHub raw README URL
    url = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        markdown = response.text

        print("✅ Successfully fetched README.md")

    except Exception as e:
        print(f"❌ Error fetching GitHub repo: {e}")
        return None

    # Parse the HTML table using BeautifulSoup
    jobs = []

    print("\n📊 Parsing HTML table...")

    try:
        soup = BeautifulSoup(markdown, 'html.parser')

        # Find all tables - the first one should be the main Software Engineering table
        all_tables = soup.find_all('table')

        if not all_tables:
            print("❌ No tables found in markdown")
            return None

        print(f"✅ Found {len(all_tables)} tables in markdown")

        # The first table is the main Software Engineering new grad roles table
        swe_table = all_tables[0]

        print("✅ Using first table (Software Engineering new grad roles)")

        # Get all table rows (skip header)
        rows = swe_table.find_all('tr')[1:]  # Skip header row

        for row in rows:
            cells = row.find_all('td')

            if len(cells) < 5:
                continue

            # Extract data from cells
            company = cells[0].get_text(strip=True)
            role = cells[1].get_text(strip=True)
            location = cells[2].get_text(strip=True)
            age = cells[4].get_text(strip=True)

            # Extract apply URL from link in 4th cell
            apply_link = cells[3].find('a')
            apply_url = apply_link.get('href') if apply_link else None

            # Skip if no company name
            if not company or len(company) < 2:
                continue

            # Check for special flags/emojis in role
            no_sponsorship = '🛂' in role
            us_citizenship = '🇺🇸' in role
            closed = '🔒' in role
            faang = '🔥' in role
            advanced_degree = '🎓' in role

            # Clean role name (remove emojis)
            role_clean = role
            for emoji in ['🛂', '🇺🇸', '🔒', '🔥', '🎓']:
                role_clean = role_clean.replace(emoji, '')
            role_clean = role_clean.strip()

            # Parse age (convert "0d" to 0, "2d" to 2, etc.)
            age_days = None
            age_match = re.search(r'(\d+)d', age)
            if age_match:
                age_days = int(age_match.group(1))

            jobs.append({
                'company': company,
                'title': role_clean,
                'location': location,
                'job_url': apply_url if apply_url else f"https://github.com/SimplifyJobs/New-Grad-Positions",
                'site': 'github',
                'source': 'SimplifyJobs-GitHub',
                'age_posted': age,
                'age_days': age_days,
                'requires_sponsorship': not no_sponsorship,  # If 🛂 present, NO sponsorship
                'requires_citizenship': us_citizenship,
                'is_closed': closed,
                'is_faang': faang,
                'requires_advanced_degree': advanced_degree,
                'job_type': 'fulltime',
                'description': f"New graduate position at {company}. " +
                               ("FAANG company. " if faang else "") +
                               ("US Citizenship required. " if us_citizenship else "") +
                               ("Visa sponsorship NOT available. " if no_sponsorship else "Visa sponsorship may be available. ") +
                               ("Advanced degree (Master's/PhD) required. " if advanced_degree else ""),
                'date_posted': datetime.now().strftime("%Y-%m-%d"),
                'collected_at': datetime.now().isoformat()
            })

        print(f"✅ Parsed {len(jobs)} job rows from table")

    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        import traceback
        traceback.print_exc()
        return None

    df = pd.DataFrame(jobs)

    if len(df) == 0:
        print("❌ No jobs found in GitHub repo")
        return None

    print(f"\n✅ Successfully scraped {len(df)} jobs from SimplifyJobs GitHub!")
    print(f"\n📊 Breakdown:")
    print(f"   - Total positions: {len(df)}")
    print(f"   - FAANG companies: {df['is_faang'].sum()}")
    print(f"   - Requires US citizenship: {df['requires_citizenship'].sum()}")
    print(f"   - NO visa sponsorship: {(~df['requires_sponsorship']).sum()}")
    print(f"   - Open positions: {(~df['is_closed']).sum()}")
    print(f"   - Closed positions: {df['is_closed'].sum()}")
    print(f"   - Requires advanced degree: {df['requires_advanced_degree'].sum()}")

    # Show age distribution
    print(f"\n📅 Job Age Distribution:")
    age_counts = df['age_posted'].value_counts().head(5)
    for age, count in age_counts.items():
        print(f"   - {age}: {count} jobs")

    # Show top companies
    print(f"\n🏢 Top 10 Companies:")
    top_companies = df['company'].value_counts().head(10)
    for company, count in top_companies.items():
        print(f"   - {company}: {count} positions")

    # Show location distribution
    print(f"\n📍 Top 10 Locations:")
    top_locations = df['location'].value_counts().head(10)
    for location, count in top_locations.items():
        print(f"   - {location}: {count} positions")

    return df

def save_to_database(jobs_df, db_path="../database/jobs.db"):
    """Save GitHub jobs to database"""

    if jobs_df is None or len(jobs_df) == 0:
        print("❌ No jobs to save")
        return

    print(f"\n💾 Saving {len(jobs_df)} GitHub jobs to database...")

    try:
        # Get absolute path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_absolute_path = os.path.join(script_dir, db_path)

        conn = sqlite3.connect(db_absolute_path)

        # Create github_jobs table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS github_jobs (
                company TEXT,
                title TEXT,
                location TEXT,
                job_url TEXT,
                site TEXT,
                source TEXT,
                age_posted TEXT,
                age_days INTEGER,
                requires_sponsorship BOOLEAN,
                requires_citizenship BOOLEAN,
                is_closed BOOLEAN,
                is_faang BOOLEAN,
                requires_advanced_degree BOOLEAN,
                job_type TEXT,
                description TEXT,
                date_posted DATE,
                collected_at TIMESTAMP
            )
        """)

        # Clear existing GitHub jobs to avoid duplicates
        conn.execute("DELETE FROM github_jobs")
        print("   - Cleared existing GitHub jobs from database")

        # Save new jobs
        jobs_df.to_sql('github_jobs', conn, if_exists='append', index=False)

        conn.commit()

        # Verify
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM github_jobs")
        count = cursor.fetchone()[0]

        conn.close()

        print(f"✅ Saved {count} GitHub jobs to database: {db_absolute_path}")

    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()

def save_to_csv(jobs_df, csv_path="../database/github_jobs.csv"):
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
    """Main function to scrape and save GitHub jobs"""

    print("\n" + "="*70)
    print("🚀 SIMPLIFYJOBS GITHUB SCRAPER")
    print("="*70)
    print("\nThis script scrapes curated new grad positions from:")
    print("https://github.com/SimplifyJobs/New-Grad-Positions")
    print("\nExpected results: 325+ software engineering new grad roles")
    print("="*70 + "\n")

    # Scrape jobs
    jobs = scrape_simplify_jobs_github()

    if jobs is None or len(jobs) == 0:
        print("\n❌ No jobs collected. Exiting.")
        return

    # Save to database
    save_to_database(jobs)

    # Save to CSV for inspection
    save_to_csv(jobs)

    print("\n" + "="*70)
    print("✅ SUCCESS! GitHub jobs scraped and saved")
    print("="*70)
    print(f"\nTotal jobs collected: {len(jobs)}")
    print(f"Database: database/jobs.db (github_jobs table)")
    print(f"CSV backup: database/github_jobs.csv")
    print("\nNext steps:")
    print("1. Update API to serve GitHub jobs alongside Indeed/LinkedIn")
    print("2. Update UI to display GitHub jobs with metadata badges")
    print("3. Test complete system with all 3 sources")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
