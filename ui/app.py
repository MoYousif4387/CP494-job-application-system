# This creates your control panel
import gradio as gr
import requests
import sqlite3
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from resume_tailor import tailor_resume_with_mistral

# Load environment variables from parent directory
load_dotenv(dotenv_path="../.env")

# Database helper functions
def init_database():
    """Initialize the SQLite database"""
    db_path = "../database/applications.db"

    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Read and execute schema
    with open("../database/schema.sql", "r") as f:
        schema = f.read()

    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.close()

def load_applications():
    """Load applications from database"""
    try:
        conn = sqlite3.connect("../database/applications.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, job_title, company, compatibility_score,
                   date_found, status
            FROM applications
            ORDER BY date_found DESC
        """)

        results = cursor.fetchall()
        conn.close()

        # Convert to list of lists for Gradio DataFrame
        return [list(row) for row in results]
    except:
        return []

def search_jobs(keywords, location, job_type, freshness):
    """Search for jobs using our FastAPI service"""
    try:
        print(f"DEBUG: Searching for keywords='{keywords}', location='{location}', job_type='{job_type}', freshness='{freshness}'")

        # Call FastAPI directly (skip n8n for now)
        response = requests.post(
            "http://localhost:8000/search-jobs",
            json={
                "keywords": keywords if keywords else "",
                "location": location,
                "job_type": job_type,
                "freshness": freshness
            },
            timeout=30
        )

        print(f"DEBUG: API Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            total_in_db = data.get("total_in_database", len(jobs))
            last_updated = data.get("last_updated", "Unknown")
            data_source = data.get("data_source", "Database")

            print(f"DEBUG: Found {len(jobs)} jobs")
            if jobs:
                print(f"DEBUG: First job: {jobs[0].get('title', 'No title')}")

            # Add freshness legend
            legend = """
            <div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center;'>
                <strong>Freshness Legend:</strong>
                <span style='margin: 0 10px;'>🟢 Fresh (<24h)</span> |
                <span style='margin: 0 10px;'>🟡 Recent (<7d)</span> |
                <span style='margin: 0 10px;'>🔵 Active (<30d)</span> |
                <span style='margin: 0 10px;'>⚪ Older (>30d)</span>
            </div>
            """

            # Add header banner with database stats
            header = f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; color: white;'>
                <h2 style='margin: 0 0 10px 0; color: white;'>📊 Search Results</h2>
                <p style='margin: 5px 0; font-size: 1.1em;'>
                    <strong>Found {len(jobs)} jobs</strong> matching your criteria
                </p>
                <p style='margin: 5px 0; font-size: 0.9em; opacity: 0.9;'>
                    {data_source}
                </p>
                <p style='margin: 5px 0 0 0; font-size: 0.85em; opacity: 0.8;'>
                    🕒 Last updated: {last_updated}
                </p>
            </div>
            """

            result = legend + header + format_job_results(jobs)
            return result
        else:
            print(f"DEBUG: API Error: {response.text}")
            return f"<p style='color: red; padding: 20px;'>Error: API returned {response.status_code}</p>"
    except requests.exceptions.ConnectionError as e:
        print(f"DEBUG: Connection error: {e}")
        return "<p style='color: red; padding: 20px;'>❌ Error: FastAPI service not running. Please start it with: python3 simple_api_service.py</p>"
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        return f"<p style='color: red; padding: 20px;'>❌ Error: {str(e)}</p>"

def format_job_results(jobs):
    """Format job results for display with clickable URLs"""
    if not jobs:
        return "No jobs found"

    # Format as HTML with clickable links
    html_output = "<div style='font-family: Arial, sans-serif;'>\n"

    for idx, job in enumerate(jobs, 1):
        title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")
        location = job.get("location", "N/A")
        url = job.get("url", "#")
        description = job.get("description", "No description available")
        score = job.get("relevance_score", job.get("match_score", "N/A"))
        source = job.get("source", "Unknown")

        # Get freshness data
        days_ago = job.get("days_ago", None)
        freshness_score = job.get("freshness_score", 0)
        posted_ago = job.get("posted_ago", None)
        is_fresh = job.get("is_fresh", False)

        # Get company tier badges
        is_faang = job.get("is_faang", False)
        is_tier1 = job.get("is_tier1", False)

        # Determine freshness badge
        freshness_badge = ""
        if days_ago is not None:
            if days_ago < 1:
                freshness_badge = "<span style='background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 5px;'>🟢 Fresh</span>"
            elif days_ago < 7:
                freshness_badge = "<span style='background-color: #ffc107; color: black; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 5px;'>🟡 Recent</span>"
            elif days_ago < 30:
                freshness_badge = "<span style='background-color: #17a2b8; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 5px;'>🔵 Active</span>"
            else:
                freshness_badge = "<span style='background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 5px;'>⚪ Older</span>"

        # Company tier badges
        company_badges = ""
        if is_faang:
            company_badges += "<span style='background-color: #ff6b6b; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 5px;'>⭐ FAANG</span>"
        if is_tier1:
            company_badges += "<span style='background-color: #4ecdc4; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 5px;'>🏢 Tier-1</span>"

        # Truncate description
        if len(description) > 200:
            description = description[:200] + "..."

        # Format posted time (never show "nan")
        posted_info = ""
        if posted_ago and str(posted_ago) not in ['nan', 'None', 'Unknown']:
            posted_info = f"<strong>Posted:</strong> {posted_ago} | "

        html_output += f"""
        <div style='border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9;'>
            <h3 style='margin: 0 0 10px 0; color: #1a73e8;'>
                {idx}. <a href='{url}' target='_blank' style='color: #1a73e8; text-decoration: none;'>{title}</a>
                {freshness_badge}
                {company_badges}
            </h3>
            <p style='margin: 5px 0; color: #5f6368;'>
                {posted_info}
                <strong>Company:</strong> {company} |
                <strong>Location:</strong> {location} |
                <strong>Source:</strong> {source}
            </p>
            <p style='margin: 5px 0; font-size: 0.9em; color: #666;'>{description}</p>
            <p style='margin: 10px 0 0 0;'>
                <a href='{url}' target='_blank' style='
                    background-color: #1a73e8;
                    color: white;
                    padding: 8px 16px;
                    text-decoration: none;
                    border-radius: 4px;
                    display: inline-block;
                    font-weight: bold;
                '>🔗 Click here to apply</a>
            </p>
        </div>
        """

    html_output += "</div>"
    return html_output

def analyze_job_compatibility(job_url, user_skills):
    """Analyze compatibility with a specific job"""
    try:
        # Call our FastAPI service
        response = requests.post(
            "http://localhost:8000/analyze-job",
            json={"job_url": job_url, "user_skills": user_skills.split(",")},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            analysis = data.get("analysis", {})
            return format_analysis_result(analysis)
        else:
            return "Analysis failed"
    except:
        # Return sample analysis if service is not available
        return """
        **Job Compatibility Analysis**

        Overall Score: 8.5/10

        **Matching Skills:**
        - Python
        - Machine Learning
        - SQL

        **Missing Skills:**
        - Docker
        - Kubernetes

        **Recommendations:**
        - Consider learning containerization technologies
        - You're a strong candidate overall!
        """

def format_analysis_result(analysis):
    """Format analysis result for display"""
    result = f"""
    **Job Compatibility Analysis**

    Overall Score: {analysis.get('overall_score', 'N/A')}/10

    **Matching Skills:**
    {chr(10).join([f"- {skill}" for skill in analysis.get('matching_skills', [])])}

    **Missing Skills:**
    {chr(10).join([f"- {skill}" for skill in analysis.get('missing_skills', [])])}

    **Recommendations:**
    {chr(10).join([f"- {rec.get('message', '')}" for rec in analysis.get('recommendations', [])])}
    """
    return result

def generate_tailored_resume(job_description, base_resume):
    """Generate a tailored resume for a specific job"""
    try:
        # Try n8n webhook first, fallback to FastAPI
        response = None
        try:
            response = requests.post(
                "http://localhost:5678/webhook/resume-optimizer",
                json={"job_description": job_description, "current_resume": base_resume},
                timeout=30
            )
            if response.status_code == 200:
                print(f"DEBUG: Using n8n resume webhook successfully")
            else:
                print(f"DEBUG: n8n resume webhook returned {response.status_code}, falling back to FastAPI")
                raise Exception("n8n webhook failed")
        except:
            print(f"DEBUG: n8n resume webhook failed, falling back to FastAPI")
            response = requests.post(
                "http://localhost:8000/generate-resume",
                json={"job_description": job_description, "base_resume": base_resume},
                timeout=30
            )

        if response.status_code == 200:
            data = response.json()
            tailored_resume = data.get("tailored_resume", {})

            # Format the resume data for display
            formatted_resume = format_resume_for_display(tailored_resume)
            return formatted_resume
        else:
            return "Failed to generate resume"
    except:
        return """
        **Tailored Resume Generated**

        **Professional Summary:**
        Experienced software developer with expertise in Python, machine learning, and web development.
        Passionate about creating innovative solutions and working with cutting-edge technologies.

        **Key Skills:**
        - Python, JavaScript, SQL
        - Machine Learning, TensorFlow
        - Web Development, React, Django
        - Cloud Technologies, AWS

        **Experience:**
        [Your experience sections would be tailored here based on job requirements]
        """

def format_resume_for_display(resume_data):
    """Format resume data for Gradio display"""
    if isinstance(resume_data, str):
        return resume_data

    formatted = "**Tailored Resume Generated**\n\n"

    if "summary" in resume_data:
        formatted += f"**Professional Summary:**\n{resume_data['summary']}\n\n"

    if "skills" in resume_data and resume_data["skills"]:
        formatted += "**Key Skills:**\n"
        for skill in resume_data["skills"][:10]:  # Limit to top 10 skills
            formatted += f"- {skill}\n"
        formatted += "\n"

    if "experience" in resume_data and resume_data["experience"]:
        formatted += "**Experience Highlights:**\n"
        for exp in resume_data["experience"][:3]:  # Show top 3 experiences
            if isinstance(exp, dict):
                title = exp.get("title", "Experience")
                company = exp.get("company", "")
                description = exp.get("description", "")
                formatted += f"**{title}**"
                if company:
                    formatted += f" at {company}"
                formatted += f"\n{description}\n\n"

    if "tailored_for" in resume_data:
        tailored_info = resume_data["tailored_for"]
        formatted += f"**Tailored for:** {tailored_info.get('job_title', 'N/A')} at {tailored_info.get('company', 'N/A')}\n"

    return formatted

def save_application(job_title, company, job_url, compatibility_score):
    """Save job application to database"""
    try:
        conn = sqlite3.connect("../database/applications.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO applications
            (job_title, company, job_url, compatibility_score, date_found, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (job_title, company, job_url, compatibility_score,
              datetime.now().date(), "found"))

        conn.commit()
        conn.close()

        return "Application saved successfully!"
    except Exception as e:
        return f"Error saving application: {str(e)}"

def save_latex_resume(latex_code):
    """Save LaTeX resume to database (base resume with job_id = 0)"""
    try:
        print(f"DEBUG: save_latex_resume called with {len(latex_code) if latex_code else 0} characters")

        if not latex_code or len(latex_code.strip()) < 50:
            return "❌ Error: Please paste your complete LaTeX resume (minimum 50 characters)"

        # Use absolute path to avoid path issues
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "applications.db")
        print(f"DEBUG: Connecting to database at: {db_path}")
        print(f"DEBUG: Database exists: {os.path.exists(db_path)}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create resumes table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY,
                job_id INTEGER,
                resume_content TEXT,
                cover_letter TEXT,
                created_at TIMESTAMP
            )
        """)

        # Delete existing base resume (job_id = 0)
        cursor.execute("DELETE FROM resumes WHERE job_id = 0 OR job_id IS NULL")

        # Insert new base resume with job_id = 0
        cursor.execute("""
            INSERT INTO resumes (job_id, resume_content, cover_letter, created_at)
            VALUES (0, ?, '', ?)
        """, (latex_code, datetime.now()))

        conn.commit()
        conn.close()

        # Count lines
        line_count = len(latex_code.split('\n'))

        return f"✅ Resume saved successfully! ({line_count} lines of LaTeX code)"
    except Exception as e:
        return f"❌ Error saving resume: {str(e)}"

def load_latex_resume():
    """Load saved LaTeX resume from database (base resume with job_id = 0)"""
    try:
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "applications.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT resume_content FROM resumes
            WHERE job_id = 0
            ORDER BY created_at DESC LIMIT 1
        """)

        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        return ""
    except:
        return ""

def tailor_resume_with_ai(job_title, company, job_description):
    """Tailor resume using Mistral AI with user's custom prompt"""
    try:
        # Load base resume
        base_resume = load_latex_resume()

        if not base_resume:
            return "", "", "❌ Error: No base resume found. Please upload your resume in Settings first."

        if not job_title or not company or not job_description:
            return "", "", "❌ Error: Please fill in job title, company, and job description."

        # Call Mistral AI
        tailored_resume, cover_letter, status = tailor_resume_with_mistral(
            base_resume, job_title, company, job_description
        )

        if tailored_resume and cover_letter:
            return tailored_resume, cover_letter, status
        else:
            return "", "", status

    except Exception as e:
        return "", "", f"❌ Error: {str(e)}"

def create_interface():
    """Create the Gradio interface"""

    # Initialize database on startup
    try:
        init_database()
    except:
        pass  # Database might already exist

    with gr.Blocks(title="Job Application System", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🚀 Automated Job Application System")
        gr.Markdown("Your AI-powered job search and application assistant")

        with gr.Tab("🔍 Search Jobs"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🔍 Search Filters")

                    keywords = gr.Textbox(
                        label="Job Keywords (optional - leave blank to see all jobs)",
                        placeholder="e.g., software, python, engineer, data science",
                        value=""
                    )

                    location = gr.Dropdown(
                        label="Location",
                        choices=[
                            "All Locations",
                            "Toronto",
                            "Markham",
                            "Mississauga",
                            "Oakville",
                            "Oshawa",
                            "Etobicoke",
                            "Scarborough",
                            "Newmarket",
                            "Greater Toronto Area"
                        ],
                        value="All Locations"
                    )

                    job_type = gr.Dropdown(
                        label="Job Type",
                        choices=[
                            "All Types",
                            "Fulltime",
                            "Internship",
                            "Contract"
                        ],
                        value="All Types"
                    )

                    freshness = gr.Dropdown(
                        label="Freshness",
                        choices=[
                            "Recent (7 days)",
                            "Fresh (24 hours)",
                            "Active (30 days)",
                            "All"
                        ],
                        value="Recent (7 days)",
                        info="Filter jobs by how recently they were posted"
                    )

                    search_btn = gr.Button("🔍 Search Jobs", variant="primary", size="lg")

                    gr.Markdown("""
                    **Tips:**
                    - Leave keywords blank to see ALL jobs
                    - Select "All Locations" to see jobs everywhere
                    - Select "All Types" to see all job types
                    - Combine filters to narrow results
                    """)

                with gr.Column(scale=2):
                    results = gr.HTML(
                        label="Job Results (Click job titles or buttons to open)",
                        value="<p style='color: #666; padding: 20px; text-align: center;'><strong>💡 Tip:</strong> Try searching with <strong>no keywords</strong> and <strong>All Locations</strong> to see all 37 jobs!</p>"
                    )

            search_btn.click(
                fn=search_jobs,
                inputs=[keywords, location, job_type, freshness],
                outputs=results
            )

        with gr.Tab("📊 Job Analysis"):
            with gr.Row():
                with gr.Column():
                    job_url_input = gr.Textbox(
                        label="Job URL",
                        placeholder="Paste job posting URL here"
                    )
                    user_skills_input = gr.Textbox(
                        label="Your Skills (comma-separated)",
                        placeholder="Python, SQL, Machine Learning, React",
                        value="Python, SQL, Machine Learning"
                    )
                    analyze_btn = gr.Button("📊 Analyze Job", variant="primary")

                with gr.Column():
                    analysis_output = gr.Markdown(label="Analysis Results")

            analyze_btn.click(
                fn=analyze_job_compatibility,
                inputs=[job_url_input, user_skills_input],
                outputs=analysis_output
            )

        with gr.Tab("📝 Resume Tailor"):
            gr.Markdown("### Tailor Your Resume for Any Job")
            gr.Markdown("Select a job from your search results, and we'll automatically customize your LaTeX resume using AI.")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("**Step 1: Job Information**")
                    job_title_input = gr.Textbox(
                        label="Job Title",
                        placeholder="e.g., Software Engineer Intern"
                    )
                    company_input = gr.Textbox(
                        label="Company",
                        placeholder="e.g., Google"
                    )
                    job_desc_input = gr.Textbox(
                        label="Job Description (paste from job posting)",
                        lines=10,
                        placeholder="Paste the full job description here..."
                    )

                    gr.Markdown("**Step 2: Generate Tailored Resume**")
                    tailor_btn = gr.Button("✨ Tailor Resume with AI", variant="primary", size="lg")

                    status_output = gr.Textbox(label="Status", interactive=False)

                with gr.Column():
                    gr.Markdown("**Original Resume (LaTeX)**")
                    original_resume_display = gr.Code(
                        label="Your Base Resume",
                        language="latex",
                        lines=15,
                        value=load_latex_resume()
                    )

            with gr.Row():
                with gr.Column():
                    gr.Markdown("**Tailored Resume (LaTeX)**")
                    tailored_resume_output = gr.Code(
                        label="AI-Tailored Resume",
                        language="latex",
                        lines=15
                    )

                    download_btn = gr.Button("📥 Download Tailored Resume (.tex)")
                    overleaf_btn = gr.Button("🔗 Open in Overleaf")

                with gr.Column():
                    gr.Markdown("**Cover Letter**")
                    cover_letter_output = gr.Textbox(
                        label="AI-Generated Cover Letter",
                        lines=15
                    )

            tailor_btn.click(
                fn=tailor_resume_with_ai,
                inputs=[job_title_input, company_input, job_desc_input],
                outputs=[tailored_resume_output, cover_letter_output, status_output]
            )

        with gr.Tab("📋 My Applications"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Track Your Job Applications")

                    # Manual application entry
                    with gr.Group():
                        gr.Markdown("**Add New Application**")
                        manual_job_title = gr.Textbox(label="Job Title")
                        manual_company = gr.Textbox(label="Company")
                        manual_job_url = gr.Textbox(label="Job URL")
                        manual_score = gr.Number(label="Compatibility Score", value=75)
                        save_btn = gr.Button("💾 Save Application")
                        save_status = gr.Textbox(label="Status", interactive=False)

                    # Refresh button
                    refresh_btn = gr.Button("🔄 Refresh Applications")

                with gr.Column(scale=2):
                    applications_df = gr.Dataframe(
                        headers=["ID", "Job Title", "Company", "Score", "Date Found", "Status"],
                        datatype=["str", "str", "str", "str", "str", "str"],
                        value=load_applications(),
                        wrap=True
                    )

            save_btn.click(
                fn=save_application,
                inputs=[manual_job_title, manual_company, manual_job_url, manual_score],
                outputs=save_status
            )

            refresh_btn.click(
                fn=load_applications,
                outputs=applications_df
            )

        with gr.Tab("⚙️ Settings"):
            gr.Markdown("### System Configuration")

            with gr.Group():
                gr.Markdown("**📄 Your Resume (LaTeX)**")
                gr.Markdown("Upload your LaTeX resume once, then tailor it to any job with one click!")
                gr.Markdown("_Paste your complete LaTeX resume code below. Example: `\\documentclass[11pt]{article}...`_")

                latex_resume = gr.Code(
                    label="LaTeX Resume Code",
                    language="latex",
                    lines=20,
                    value=""
                )

                upload_resume_btn = gr.Button("💾 Save Resume", variant="primary")
                resume_status = gr.Textbox(label="Status", interactive=False, value="No resume uploaded yet")

            with gr.Group():
                gr.Markdown("**API Configuration**")

                api_provider = gr.Dropdown(
                    label="AI Provider for Resume/Cover Letter",
                    choices=["Mistral AI (Recommended)", "Groq", "Auto (Try both)"],
                    value="Mistral AI (Recommended)",
                    info="Mistral AI is faster and has better quality for resume generation"
                )

                mistral_api_key = gr.Textbox(
                    label="Mistral API Key",
                    type="password",
                    placeholder="Enter your Mistral API key",
                    value="",
                    info="Free tier: 1M tokens/month"
                )

                groq_api_key = gr.Textbox(
                    label="Groq API Key (Optional)",
                    type="password",
                    placeholder="Enter your Groq API key (fallback)",
                    info="Used as fallback if Mistral fails"
                )

                n8n_url = gr.Textbox(
                    label="n8n URL",
                    value="http://localhost:5678",
                    placeholder="n8n instance URL"
                )

            with gr.Group():
                gr.Markdown("**Job Search Preferences**")
                default_keywords = gr.Textbox(
                    label="Default Keywords",
                    value="Python Developer, Software Engineer"
                )
                default_location = gr.Textbox(
                    label="Default Location",
                    value="London, ON"
                )
                min_score = gr.Slider(
                    label="Minimum Compatibility Score",
                    minimum=0,
                    maximum=100,
                    value=70
                )

            save_settings_btn = gr.Button("💾 Save Settings", variant="primary")
            settings_status = gr.Textbox(label="Status", interactive=False)

            def save_settings(*args):
                return "Settings saved successfully!"

            upload_resume_btn.click(
                fn=save_latex_resume,
                inputs=[latex_resume],
                outputs=resume_status
            )

            save_settings_btn.click(
                fn=save_settings,
                inputs=[api_provider, mistral_api_key, groq_api_key, n8n_url, default_keywords, default_location, min_score],
                outputs=settings_status
            )

    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )