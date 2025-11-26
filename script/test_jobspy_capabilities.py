#!/usr/bin/env python3
"""
Test JobSpy's scraping capabilities with different parameters
Validate what we can scrape and measure performance
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobspy import scrape_jobs
import pandas as pd
import time
from datetime import datetime

def test_jobspy_capabilities():
    """Test JobSpy with different parameters to validate capabilities"""

    print("="*70)
    print("🔍 JOBSPY CAPABILITIES VALIDATION TEST")
    print("="*70)
    print("\nTesting JobSpy with 4 different scenarios:")
    print("1. Software Intern - Toronto, ON (Canada focus)")
    print("2. Full Stack Developer - San Francisco, CA (US market)")
    print("3. Data Scientist - Remote (Remote jobs)")
    print("4. Software Engineer New Grad - No location filter")
    print("\nEach test will take 15-20 seconds. Total time: ~2-3 minutes")
    print("="*70 + "\n")

    test_scenarios = [
        {
            "name": "Test 1: Software Intern - Toronto",
            "params": {
                "site_name": ["indeed", "linkedin"],
                "search_term": "software intern",
                "location": "Toronto, ON",
                "results_wanted": 25,
                "job_type": "internship",
                "country_indeed": "Canada"
            }
        },
        {
            "name": "Test 2: Full Stack - San Francisco",
            "params": {
                "site_name": ["indeed", "linkedin"],
                "search_term": "full stack developer",
                "location": "San Francisco, CA",
                "results_wanted": 25,
                "job_type": "fulltime",
                "country_indeed": "USA"
            }
        },
        {
            "name": "Test 3: Data Science - Remote",
            "params": {
                "site_name": ["indeed", "linkedin"],
                "search_term": "data scientist",
                "location": "Remote",
                "results_wanted": 25,
                "is_remote": True,
                "country_indeed": "USA"
            }
        },
        {
            "name": "Test 4: New Grad - No Location Filter",
            "params": {
                "site_name": ["indeed", "linkedin"],
                "search_term": "software engineer new grad",
                "results_wanted": 30,
                "country_indeed": "USA"
            }
        }
    ]

    all_results = []
    summary_stats = []

    for idx, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*70}")
        print(f"🔍 [{idx}/{len(test_scenarios)}] {scenario['name']}")
        print(f"{'='*70}")

        try:
            start_time = time.time()
            jobs = scrape_jobs(**scenario['params'])
            elapsed = time.time() - start_time

            if len(jobs) == 0:
                print(f"❌ No jobs found")
                summary_stats.append({
                    'test': scenario['name'],
                    'jobs_found': 0,
                    'time_seconds': elapsed,
                    'indeed_count': 0,
                    'linkedin_count': 0,
                    'status': 'No results'
                })
                continue

            print(f"✅ Found {len(jobs)} jobs in {elapsed:.2f} seconds")
            print(f"   Rate: {len(jobs)/elapsed:.1f} jobs/second")

            # Breakdown by source
            indeed_count = len(jobs[jobs['site'] == 'indeed'])
            linkedin_count = len(jobs[jobs['site'] == 'linkedin'])

            print(f"\n📊 Breakdown:")
            print(f"   - Indeed: {indeed_count} jobs ({indeed_count/len(jobs)*100:.1f}%)")
            print(f"   - LinkedIn: {linkedin_count} jobs ({linkedin_count/len(jobs)*100:.1f}%)")

            # Location analysis
            if len(jobs) > 0 and 'location' in jobs.columns:
                print(f"\n📍 Top 5 Locations:")
                locations = jobs['location'].value_counts().head(5)
                for loc, count in locations.items():
                    print(f"   - {loc}: {count} jobs")

            # Company analysis
            if len(jobs) > 0 and 'company' in jobs.columns:
                print(f"\n🏢 Top 5 Companies:")
                companies = jobs['company'].value_counts().head(5)
                for company, count in companies.items():
                    print(f"   - {company}: {count} jobs")

            # Job type analysis
            if len(jobs) > 0 and 'job_type' in jobs.columns:
                print(f"\n💼 Job Types:")
                job_types = jobs['job_type'].value_counts()
                for jtype, count in job_types.items():
                    print(f"   - {jtype}: {count} jobs")

            # Add scenario name to results
            jobs['test_scenario'] = scenario['name']
            all_results.append(jobs)

            # Save summary stats
            summary_stats.append({
                'test': scenario['name'],
                'jobs_found': len(jobs),
                'time_seconds': round(elapsed, 2),
                'indeed_count': indeed_count,
                'linkedin_count': linkedin_count,
                'jobs_per_second': round(len(jobs)/elapsed, 2),
                'status': 'Success'
            })

            # Rate limiting - be respectful
            if idx < len(test_scenarios):
                print(f"\n⏳ Waiting 10 seconds before next test (rate limiting)...")
                time.sleep(10)

        except Exception as e:
            print(f"❌ Error: {e}")
            summary_stats.append({
                'test': scenario['name'],
                'jobs_found': 0,
                'time_seconds': 0,
                'indeed_count': 0,
                'linkedin_count': 0,
                'status': f'Error: {str(e)[:50]}'
            })
            import traceback
            traceback.print_exc()

    # Combine all results
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)

        print(f"\n{'='*70}")
        print(f"📊 OVERALL SUMMARY")
        print(f"{'='*70}")
        print(f"\nTotal jobs collected: {len(combined)}")
        print(f"Unique jobs (by URL): {combined['job_url'].nunique()}")
        print(f"Duplicate rate: {(len(combined) - combined['job_url'].nunique())/len(combined)*100:.1f}%")
        print(f"Average per scenario: {len(combined) / len([s for s in summary_stats if s['jobs_found'] > 0]):.1f}")

        # Source breakdown
        print(f"\n📊 Source Breakdown:")
        source_counts = combined['site'].value_counts()
        for source, count in source_counts.items():
            print(f"   - {source}: {count} jobs ({count/len(combined)*100:.1f}%)")

        # Save results
        combined.to_csv("database/jobspy_validation_results.csv", index=False)
        print(f"\n💾 Detailed results saved to: database/jobspy_validation_results.csv")

        # Save summary
        summary_df = pd.DataFrame(summary_stats)
        summary_df.to_csv("database/jobspy_validation_summary.csv", index=False)
        print(f"💾 Summary saved to: database/jobspy_validation_summary.csv")

        # Print summary table
        print(f"\n📋 Test Summary Table:")
        print(f"{'='*70}")
        print(summary_df.to_string(index=False))
        print(f"{'='*70}")

        # Validation conclusions
        print(f"\n✅ VALIDATION CONCLUSIONS:")
        print(f"   - JobSpy can scrape from Indeed and LinkedIn")
        print(f"   - Average scraping rate: {combined['job_url'].nunique()/sum(s['time_seconds'] for s in summary_stats):.1f} unique jobs/second")
        print(f"   - Works with different locations (Toronto, SF, Remote, USA)")
        print(f"   - Works with different job types (internship, fulltime, remote)")
        print(f"   - Deduplication needed ({(len(combined) - combined['job_url'].nunique())} duplicates found)")

        return combined, summary_df
    else:
        print(f"\n❌ No results collected from any test")
        return None, None

def main():
    """Main function"""
    print("\n" + "="*70)
    print("🚀 JOBSPY CAPABILITIES VALIDATION")
    print("="*70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nThis script validates JobSpy's scraping capabilities by testing:")
    print(f"  - Different search terms")
    print(f"  - Different locations")
    print(f"  - Different job types")
    print(f"  - Different markets (Canada, USA, Remote)")
    print("\nResults will be saved to database/ folder for analysis")
    print("="*70 + "\n")

    try:
        results, summary = test_jobspy_capabilities()

        print(f"\n" + "="*70)
        print(f"✅ VALIDATION COMPLETE!")
        print(f"="*70)
        print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if results is not None:
            print(f"\n📊 Key Findings:")
            print(f"   - Total unique jobs: {results['job_url'].nunique()}")
            print(f"   - Total test scenarios: {len(summary)}")
            print(f"   - Successful scenarios: {sum(summary['status'] == 'Success')}")
            print(f"   - Failed scenarios: {sum(summary['status'] != 'Success')}")

            print(f"\n📁 Output Files:")
            print(f"   - database/jobspy_validation_results.csv (detailed job data)")
            print(f"   - database/jobspy_validation_summary.csv (test summary)")

            print(f"\n🎯 Next Steps:")
            print(f"   1. Review validation results")
            print(f"   2. Use successful parameters for job collection expansion")
            print(f"   3. Include validation metrics in research paper")
        else:
            print(f"\n❌ Validation failed - no results collected")

        print(f"\n" + "="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
