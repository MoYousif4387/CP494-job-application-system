#!/usr/bin/env python3
"""
Master scraper that runs all job collection sources
Called by daily_refresh.sh for automated updates
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import sqlite3

def run_scraper(scraper_name, scraper_function):
    """Run a scraper and return results"""
    print(f"\n{'='*70}")
    print(f"🔄 Running {scraper_name}...")
    print(f"{'='*70}")

    try:
        start_time = datetime.now()
        result = scraper_function()
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        if result is not None and len(result) > 0:
            print(f"✅ {scraper_name} completed: {len(result)} jobs in {elapsed:.1f}s")
            return {"success": True, "jobs": len(result), "time": elapsed, "data": result}
        else:
            print(f"⚠️  {scraper_name} returned no jobs")
            return {"success": False, "jobs": 0, "time": elapsed, "data": None}

    except Exception as e:
        print(f"❌ {scraper_name} failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "jobs": 0, "time": 0, "error": str(e)}

def main():
    """Run all scrapers in sequence"""

    print("\n" + "="*70)
    print("🚀 MASTER SCRAPER - ALL SOURCES")
    print("="*70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis will scrape:")
    print("1. SimplifyJobs GitHub (new grad positions)")
    print("2. Zapply GitHub (tech company positions)")
    print("3. JobSpy (optional - for expansion)")
    print("="*70 + "\n")

    results = {}

    # 1. SimplifyJobs GitHub
    try:
        from scrape_github_jobs import scrape_simplify_jobs_github, save_to_database as save_simplify
        result = run_scraper("SimplifyJobs GitHub", scrape_simplify_jobs_github)
        if result['success'] and result['data'] is not None:
            save_simplify(result['data'])
        results['simplify'] = result
    except ImportError as e:
        print(f"⚠️  Could not import SimplifyJobs scraper: {e}")
        results['simplify'] = {"success": False, "error": "Import failed"}

    # 2. Zapply GitHub
    try:
        from scrape_zapply_github import scrape_zapply_github, save_to_database as save_zapply
        result = run_scraper("Zapply GitHub", scrape_zapply_github)
        if result['success'] and result['data'] is not None:
            save_zapply(result['data'])
        results['zapply'] = result
    except ImportError as e:
        print(f"⚠️  Could not import Zapply scraper: {e}")
        results['zapply'] = {"success": False, "error": "Import failed"}

    # 3. JobSpy (optional - can be expanded later)
    # Uncomment when ready to expand JobSpy collection
    # try:
    #     from scrape_real_jobs import main as scrape_jobspy
    #     result = run_scraper("JobSpy (Indeed + LinkedIn)", scrape_jobspy)
    #     results['jobspy'] = result
    # except ImportError as e:
    #     print(f"⚠️  Could not import JobSpy scraper: {e}")
    #     results['jobspy'] = {"success": False, "error": "Import failed"}

    # Summary
    print("\n" + "="*70)
    print("📊 MASTER SCRAPER SUMMARY")
    print("="*70)

    total_jobs = sum(r.get('jobs', 0) for r in results.values())
    total_time = sum(r.get('time', 0) for r in results.values())
    successful = sum(1 for r in results.values() if r.get('success', False))

    print(f"\nTotal jobs collected: {total_jobs}")
    print(f"Total time: {total_time:.1f} seconds")
    print(f"Successful scrapers: {successful}/{len(results)}")
    print(f"\nBreakdown:")
    for name, result in results.items():
        status = "✅" if result.get('success') else "❌"
        jobs = result.get('jobs', 0)
        time = result.get('time', 0)
        print(f"  {status} {name}: {jobs} jobs in {time:.1f}s")

    # Check database totals
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "jobs.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"\n📊 Database Totals:")

        tables = ['raw_jobs', 'github_jobs', 'zapply_jobs']
        total_db = 0
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_db += count
                print(f"  - {table}: {count} jobs")
            except:
                pass

        print(f"\n  TOTAL IN DATABASE: {total_db} jobs")
        conn.close()

    except Exception as e:
        print(f"\n⚠️  Could not check database: {e}")

    print("\n" + "="*70)
    print(f"✅ Master scraper completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    return results

if __name__ == "__main__":
    results = main()

    # Exit with error code if all scrapers failed
    if all(not r.get('success', False) for r in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)
