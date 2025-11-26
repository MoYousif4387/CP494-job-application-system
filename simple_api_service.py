#!/usr/bin/env python3
"""
Simple FastAPI service for job processing without CrewAI dependencies
This provides basic functionality while CrewAI installs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import requests
from job_sources import JobBoardIntegrator

app = FastAPI(title="CP494 Job Application API (Simple)", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize job board integrator
job_integrator = JobBoardIntegrator()

# Pydantic models
class JobSearchRequest(BaseModel):
    keywords: str
    location: str = "All Locations"
    job_type: str = "All Types"
    freshness: str = "Recent (7 days)"  # Fresh (24h), Recent (7d), Active (30d), All
    limit: int = 5000  # Increased to show all jobs

class JobAnalysisRequest(BaseModel):
    job_url: str
    user_skills: List[str]

class ResumeRequest(BaseModel):
    job_description: str
    base_resume: str

# Sample job data focused on internships and new grad opportunities
SAMPLE_JOBS = [
    {
        "title": "Software Engineering Intern - Summer 2025",
        "company": "Shopify",
        "location": "Toronto, ON",
        "description": "Looking for computer science students for summer 2025 internship. Experience with Python, JavaScript, or Java preferred. No prior professional experience required. Will work on real products used by millions of merchants.",
        "url": "https://example.com/intern1",
        "posted_date": "2025-01-01",
        "salary_range": "5000-7000/month",
        "relevance_score": 92
    },
    {
        "title": "New Graduate Software Developer",
        "company": "RBC",
        "location": "Toronto, ON",
        "description": "Entry-level position for recent Computer Science graduates. Join our technology graduate program. Training provided. Looking for knowledge in Python, Java, or C++. Recent graduates welcome.",
        "url": "https://example.com/newgrad1",
        "posted_date": "2025-01-01",
        "salary_range": "65000-75000",
        "relevance_score": 89
    },
    {
        "title": "Data Engineering Intern",
        "company": "TD Bank",
        "location": "Toronto, ON",
        "description": "Summer internship opportunity for students studying Computer Science, Data Science, or related fields. Experience with Python, SQL, and data processing frameworks preferred but not required.",
        "url": "https://example.com/intern2",
        "posted_date": "2025-01-01",
        "salary_range": "4500-6000/month",
        "relevance_score": 88
    },
    {
        "title": "Junior Python Developer (New Grad)",
        "company": "Wealthsimple",
        "location": "Toronto, ON",
        "description": "Entry-level Python developer position for recent graduates. Will work on fintech applications. Looking for new grads with Python knowledge and eagerness to learn. Mentorship provided.",
        "url": "https://example.com/newgrad2",
        "posted_date": "2025-01-01",
        "salary_range": "70000-80000",
        "relevance_score": 91
    },
    {
        "title": "Software Engineering Co-op",
        "company": "Blackberry",
        "location": "Waterloo, ON",
        "description": "4-month co-op position for computer science students. Experience with C++, Python, or Java. Will work on cybersecurity and IoT products. Previous co-op experience an asset but not required.",
        "url": "https://example.com/coop1",
        "posted_date": "2025-01-01",
        "salary_range": "4800-6200/month",
        "relevance_score": 87
    },
    {
        "title": "Machine Learning Intern",
        "company": "Vector Institute",
        "location": "Toronto, ON",
        "description": "Research internship for students interested in AI/ML. Experience with Python, TensorFlow/PyTorch preferred. Will work alongside researchers on cutting-edge AI projects. Academic credit available.",
        "url": "https://example.com/intern3",
        "posted_date": "2025-01-01",
        "salary_range": "5500-7500/month",
        "relevance_score": 94
    }
]

# Database helper
def get_db_connection():
    """Get database connection"""
    db_path = "database/applications.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)

def init_database():
    """Initialize database with schema"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            job_title TEXT,
            company TEXT,
            job_url TEXT,
            compatibility_score REAL,
            date_found DATE,
            date_applied DATE,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()

@app.get("/")
async def root():
    return {"message": "CP494 Job Application API (Simple) is running!"}

@app.post("/search-jobs")
async def search_jobs(request: JobSearchRequest):
    """Search for jobs from database - REAL jobs from JobSpy (Indeed/LinkedIn) + GitHub (SimplifyJobs + Zapply)"""
    try:
        import pandas as pd

        print(f"🔍 Searching database for: {request.keywords}")

        # Read from JOBS database (not applications database)
        jobs_db_path = "database/jobs.db"
        conn = sqlite3.connect(jobs_db_path)

        # Get JobSpy jobs (Indeed + LinkedIn)
        jobspy_df = pd.read_sql("SELECT * FROM raw_jobs", conn)
        print(f"📊 Found {len(jobspy_df)} JobSpy jobs (Indeed + LinkedIn)")

        # Get GitHub jobs (SimplifyJobs)
        try:
            github_df = pd.read_sql("SELECT * FROM github_jobs", conn)
            print(f"📊 Found {len(github_df)} GitHub jobs (SimplifyJobs)")
        except:
            github_df = pd.DataFrame()
            print("⚠️  No GitHub jobs table found")

        # Get Zapply jobs
        try:
            zapply_df = pd.read_sql("SELECT * FROM zapply_jobs", conn)
            print(f"📊 Found {len(zapply_df)} Zapply jobs")
        except:
            zapply_df = pd.DataFrame()
            print("⚠️  No Zapply jobs table found")

        conn.close()

        # Combine all three sources
        all_dfs = [df for df in [jobspy_df, github_df, zapply_df] if len(df) > 0]

        if len(all_dfs) > 0:
            jobs_df = pd.concat(all_dfs, ignore_index=True)
        else:
            jobs_df = pd.DataFrame()

        print(f"📊 Total jobs from all sources: {len(jobs_df)}")

        if len(jobs_df) == 0:
            return {
                "jobs": [],
                "total_found": 0,
                "search_params": {
                    "keywords": request.keywords,
                    "location": request.location
                },
                "data_source": "Database (empty - run script/scrape_real_jobs.py to collect jobs)"
            }

        # Filter by keywords (if provided and not empty)
        if request.keywords and request.keywords.strip():
            keywords_list = [k.strip().lower() for k in request.keywords.split(",")]

            def matches_keywords(row):
                job_text = f"{row['title']} {str(row['description'])} {row['company']}".lower()
                return any(keyword in job_text for keyword in keywords_list)

            jobs_df = jobs_df[jobs_df.apply(matches_keywords, axis=1)]
            print(f"🔍 Keyword filter: {len(jobs_df)} jobs match '{request.keywords}'")

        # Filter by location (if not "All Locations")
        if request.location and request.location != "All Locations":
            jobs_df = jobs_df[jobs_df['location'].str.contains(request.location, case=False, na=False)]
            print(f"📍 Location filter: {len(jobs_df)} jobs in '{request.location}'")

        # Filter by job type (if not "All Types")
        if request.job_type and request.job_type != "All Types":
            if request.job_type.lower() == "fulltime":
                # Must have fulltime in job_type AND must NOT have intern keywords in title
                fulltime_mask = (
                    (jobs_df['job_type'].str.contains('fulltime|full.*time', case=False, na=False, regex=True)) &
                    (~jobs_df['title'].str.contains('intern|co-op|coop|student|co\-op', case=False, na=False, regex=True))
                )
                jobs_df = jobs_df[fulltime_mask]
            elif request.job_type.lower() == "internship":
                # Check both job_type AND title for intern keywords
                intern_mask = (
                    (jobs_df['job_type'].str.contains('intern|internship', case=False, na=False, regex=True)) |
                    (jobs_df['title'].str.contains('intern|co-op|coop|student|co\-op', case=False, na=False, regex=True))
                )
                jobs_df = jobs_df[intern_mask]
            elif request.job_type.lower() == "contract":
                jobs_df = jobs_df[jobs_df['job_type'].str.contains('contract|temporary|term', case=False, na=False, regex=True)]
            print(f"💼 Job type filter: {len(jobs_df)} {request.job_type} jobs")

        # Filter by freshness (calculate days_ago first for all jobs)
        if request.freshness and request.freshness != "All":
            freshness_days = None
            if "24" in request.freshness or "Fresh" in request.freshness:
                freshness_days = 1
            elif "7" in request.freshness or "Recent" in request.freshness:
                freshness_days = 7
            elif "30" in request.freshness or "Active" in request.freshness:
                freshness_days = 30

            if freshness_days:
                # Calculate days_ago for jobs that don't have it yet
                def calculate_days_ago(row):
                    if pd.notna(row.get('days_ago')) and row.get('days_ago') is not None:
                        return row['days_ago']
                    if row['site'] in ['indeed', 'linkedin'] and pd.notna(row.get('date_posted')):
                        try:
                            from dateutil import parser
                            posted_date = parser.parse(str(row['date_posted']))
                            return (datetime.now() - posted_date).days
                        except:
                            pass
                    return 999  # Unknown, don't filter out

                jobs_df['calculated_days_ago'] = jobs_df.apply(calculate_days_ago, axis=1)
                jobs_df = jobs_df[jobs_df['calculated_days_ago'] <= freshness_days]
                print(f"🕒 Freshness filter: {len(jobs_df)} jobs within {freshness_days} days")

        filtered_jobs = jobs_df
        print(f"✅ Total after all filters: {len(filtered_jobs)} jobs")

        # Convert to list of dicts
        jobs_list = []
        job_counter = 0
        for idx, job in filtered_jobs.head(request.limit).iterrows():
            # ALWAYS calculate days_ago dynamically from date_posted (if available)
            # This ensures timestamps update hourly instead of staying static
            days_ago = None
            posted_ago = None

            # Try to parse date_posted for ALL job sources
            if pd.notna(job.get('date_posted')):
                try:
                    from dateutil import parser
                    posted_date_str = str(job['date_posted'])
                    # Handle YYYY-MM-DD format (from GitHub scrapers)
                    if len(posted_date_str) == 10 and '-' in posted_date_str:
                        posted_date = datetime.strptime(posted_date_str, '%Y-%m-%d')
                    else:
                        posted_date = parser.parse(posted_date_str)

                    # Calculate days/hours ago from NOW (not from collected_at)
                    time_diff = datetime.now() - posted_date
                    days_ago = time_diff.days
                    hours_ago = time_diff.seconds // 3600

                    # Format human-readable timestamp
                    if days_ago == 0 and hours_ago < 1:
                        posted_ago = "Just now"
                    elif days_ago == 0 and hours_ago < 24:
                        posted_ago = f"{hours_ago}h ago" if hours_ago > 1 else "1h ago"
                    elif days_ago == 0:
                        posted_ago = "Today"
                    elif days_ago == 1:
                        posted_ago = "1d ago"
                    elif days_ago < 30:
                        posted_ago = f"{days_ago}d ago"
                    elif days_ago < 365:
                        months_ago = days_ago // 30
                        posted_ago = f"{months_ago}mo ago" if months_ago > 1 else "1mo ago"
                    else:
                        years_ago = days_ago // 365
                        posted_ago = f"{years_ago}y ago" if years_ago > 1 else "1y ago"

                except Exception as e:
                    print(f"Warning: Could not parse date_posted '{job.get('date_posted')}': {e}")
                    posted_ago = "Recently posted"
                    days_ago = None
            else:
                # Fallback: no date_posted available
                posted_ago = "Recently posted"
                days_ago = None

            job_dict = {
                "title": job['title'],
                "company": job['company'] if pd.notna(job['company']) else "Company Name Not Listed",
                "location": job['location'],
                "description": job['description'][:500] + "..." if pd.notna(job['description']) and len(str(job['description'])) > 500 else str(job['description']),
                "url": job['job_url'],  # REAL clickable URL!
                "posted_date": str(job['date_posted']) if pd.notna(job['date_posted']) else "Recently",
                "job_type": str(job['job_type']) if pd.notna(job['job_type']) else "Not specified",
                "source": job['site'],  # Indeed, LinkedIn, GitHub, or Zapply
                "relevance_score": 85,  # Could calculate this properly later
                "days_ago": days_ago,
                "posted_ago": posted_ago if posted_ago else "Recently posted"
            }

            # Add GitHub-specific metadata if available
            if job['site'] == 'github':
                job_dict['is_faang'] = bool(job.get('is_faang', False))
                job_dict['requires_citizenship'] = bool(job.get('requires_citizenship', False))
                job_dict['requires_sponsorship'] = bool(job.get('requires_sponsorship', True))
                job_dict['is_closed'] = bool(job.get('is_closed', False))

            # Add Zapply-specific metadata if available (freshness tracking)
            if job['site'] == 'zapply':
                job_dict['freshness_score'] = int(job.get('freshness_score', 0)) if pd.notna(job.get('freshness_score')) else 0
                job_dict['is_fresh'] = bool(job.get('is_fresh', False))
                job_dict['is_faang'] = bool(job.get('is_faang', False))
                job_dict['is_tier1'] = bool(job.get('is_tier1', False))
                job_dict['level'] = str(job.get('level', 'Not specified'))
                job_dict['category'] = str(job.get('category', 'Not specified'))

            jobs_list.append(job_dict)
            job_counter += 1

        # Count jobs by source
        source_counts = jobs_df['site'].value_counts().to_dict() if 'site' in jobs_df.columns else {}

        # Get database last updated time
        import os
        db_last_modified = os.path.getmtime(jobs_db_path) if os.path.exists(jobs_db_path) else None
        last_updated = datetime.fromtimestamp(db_last_modified).strftime("%b %d, %Y %I:%M %p") if db_last_modified else "Unknown"

        return {
            "jobs": jobs_list,
            "total_found": len(filtered_jobs),
            "total_in_database": len(jobspy_df) + len(github_df) + len(zapply_df),
            "search_params": {
                "keywords": request.keywords,
                "location": request.location,
                "job_type": request.job_type
            },
            "data_source": f"Database - {len(jobspy_df)} JobSpy + {len(github_df)} SimplifyJobs + {len(zapply_df)} Zapply = {len(jobspy_df) + len(github_df) + len(zapply_df)} total jobs",
            "source_breakdown": source_counts,
            "last_updated": last_updated
        }

    except Exception as e:
        print(f"❌ Database search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@app.post("/analyze-job")
async def analyze_job(request: JobAnalysisRequest):
    """Analyze job compatibility using simple matching"""
    try:
        # Simple compatibility analysis
        user_skills_lower = [skill.strip().lower() for skill in request.user_skills]

        # Sample job requirements based on the GTS job description
        job_requirements = [
            "python", "mysql", "linux", "fastapi", "airflow",
            "kafka", "redis", "docker", "api development"
        ]

        # Calculate matches
        matching_skills = [skill for skill in job_requirements if skill in user_skills_lower]
        missing_skills = [skill for skill in job_requirements if skill not in user_skills_lower]

        # Calculate scores
        skill_match_score = (len(matching_skills) / len(job_requirements)) * 100
        overall_score = min(95, skill_match_score + 20)  # Bonus for experience

        analysis = {
            "overall_score": round(overall_score, 1),
            "skill_match_score": round(skill_match_score, 1),
            "experience_match_score": 85.0,  # Assuming good experience match
            "education_match_score": 90.0,   # Assuming good education match
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "recommendations": [
                {
                    "type": "skill_development",
                    "message": f"Consider learning: {', '.join(missing_skills[:3])}",
                    "priority": "medium"
                },
                {
                    "type": "application",
                    "message": "Strong candidate - consider applying!",
                    "priority": "high"
                }
            ]
        }

        return {
            "analysis": analysis,
            "job_url": request.job_url,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job analysis failed: {str(e)}")

@app.post("/generate-resume")
async def generate_resume(request: ResumeRequest):
    """Generate tailored resume using Mistral AI"""
    try:
        # Try Mistral API first
        mistral_api_key = os.getenv("MISTRAL_API_KEY", "")

        try:
            from mistralai import Mistral

            client = Mistral(api_key=mistral_api_key)

            prompt = f"""You are an expert resume writer. Tailor this resume for the given job description.

Base Resume:
{request.base_resume[:1500]}

Job Description:
{request.job_description[:1000]}

Generate a tailored resume that:
1. Highlights relevant skills from the job description
2. Emphasizes matching experience
3. Uses keywords from the job posting

Return your response as JSON with this structure:
{{
  "summary": "professional summary highlighting relevant skills",
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "description": "description emphasizing relevant skills"
    }}
  ]
}}
"""

            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )

            if response and response.choices:
                content = response.choices[0].message.content.strip()

                # Try to parse as JSON
                try:
                    import json
                    # Extract JSON from markdown code blocks if present
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()

                    tailored_resume = json.loads(content)

                    # Generate cover letter with Mistral
                    cover_prompt = f"""Write a professional cover letter for this job:

Job Description:
{request.job_description[:1000]}

Candidate's experience (from resume):
{request.base_resume[:1000]}

Write a concise, professional cover letter (3 paragraphs max).
"""

                    cover_response = client.chat.complete(
                        model="mistral-small-latest",
                        messages=[{"role": "user", "content": cover_prompt}],
                        temperature=0.5,
                        max_tokens=500
                    )

                    cover_letter = cover_response.choices[0].message.content.strip() if cover_response and cover_response.choices else "Cover letter generation failed"

                    return {
                        "tailored_resume": tailored_resume,
                        "cover_letter": cover_letter,
                        "job_requirements": tailored_resume.get("skills", []),
                        "timestamp": datetime.now().isoformat(),
                        "api_used": "Mistral AI"
                    }

                except json.JSONDecodeError:
                    print("Failed to parse Mistral response as JSON, using fallback")

        except Exception as e:
            print(f"Mistral API error: {e}, using fallback")

        # Fallback to simple template-based generation
        job_desc_lower = request.job_description.lower()
        important_skills = []

        skill_keywords = [
            "python", "javascript", "java", "sql", "aws", "docker",
            "kubernetes", "react", "node.js", "fastapi", "django",
            "machine learning", "tensorflow", "pytorch", "linux",
            "mysql", "postgresql", "redis", "kafka", "airflow"
        ]

        for skill in skill_keywords:
            if skill in job_desc_lower:
                important_skills.append(skill.title())

        tailored_resume = {
            "summary": f"Experienced software developer with expertise in {', '.join(important_skills[:5])}. Proven track record in building scalable systems and collaborating with cross-functional teams.",
            "skills": important_skills,
            "experience": [
                {
                    "title": "Advanced Analytics & BI Intern",
                    "company": "Sun Life",
                    "description": f"Built end-to-end systems using {', '.join(important_skills[:3])}, serving 290+ users with optimized performance."
                },
                {
                    "title": "Data Engineering Intern",
                    "company": "CIBC",
                    "description": f"Contributed to large-scale distributed systems, worked with {', '.join(important_skills[1:4])} for financial data processing."
                }
            ],
            "tailored_for": {
                "job_title": "Software Developer",
                "company": "Target Company",
                "date_created": datetime.now().isoformat()
            }
        }

        cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the Software Developer position.
With my background in {', '.join(important_skills[:3])}, I am confident I would be
a valuable addition to your team.

My experience with {', '.join(important_skills[:5])} aligns perfectly with your
requirements. I am particularly excited about the opportunity to contribute to
your innovative environment.

Best regards,
Mahmoud Yousif"""

        return {
            "tailored_resume": tailored_resume,
            "cover_letter": cover_letter,
            "job_requirements": important_skills,
            "timestamp": datetime.now().isoformat(),
            "api_used": "Template-based (fallback)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")

@app.post("/save-application")
async def save_application(application_data: Dict[str, Any]):
    """Save job application to database"""
    try:
        init_database()  # Ensure database exists
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert application
        cursor.execute("""
            INSERT INTO applications
            (job_title, company, job_url, compatibility_score, date_found, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            application_data.get("job_title"),
            application_data.get("company"),
            application_data.get("job_url"),
            application_data.get("compatibility_score", 0),
            datetime.now().date(),
            "found"
        ))

        conn.commit()
        application_id = cursor.lastrowid
        conn.close()

        return {
            "message": "Application saved successfully",
            "application_id": application_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save application: {str(e)}")

@app.get("/applications")
async def get_applications():
    """Get all job applications from database"""
    try:
        init_database()  # Ensure database exists
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, job_title, company, compatibility_score,
                   date_found, status
            FROM applications
            ORDER BY date_found DESC
        """)

        results = cursor.fetchall()
        conn.close()

        applications = []
        for row in results:
            applications.append({
                "id": row[0],
                "job_title": row[1],
                "company": row[2],
                "compatibility_score": row[3],
                "date_found": row[4],
                "status": row[5]
            })

        return {"applications": applications}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch applications: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "available",
            "job_search": "active",
            "resume_generator": "active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Simple Job Application API...")
    print("Visit http://localhost:8000 for the API")
    print("Visit http://localhost:8000/docs for interactive documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)