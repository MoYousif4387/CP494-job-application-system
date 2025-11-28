"""
Resume Tailoring Module using Mistral AI
Implements the user's exact prompt template for LaTeX resume generation
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(dotenv_path="../.env")

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def tailor_resume_with_mistral(base_resume_latex, job_title, company, job_description):
    """
    Tailor LaTeX resume using Mistral AI with user's exact prompt template

    Returns:
        tuple: (tailored_resume_latex, cover_letter_text, status_message)
    """

    # User's exact prompt template
    prompt = f"""You are a professional resume and cover letter writer specializing in tailoring resumes for new graduates and early-career professionals. Your task is to customize a LaTeX resume and write a cover letter for a specific job application.

**CRITICAL REQUIREMENTS:**
1. The tailored resume MUST be between 210-217 lines of LaTeX code (count carefully!)
2. Use the candidate's email address from their resume
3. MUST include AWS Cloud Practitioner certification in the skills section
4. NEVER exaggerate, lie, or add fake experiences
5. Keep the EXACT structure: Header → Skills → Experience → Projects → Leadership → Education
6. Maintain natural, student-like language (avoid AI-sounding phrases)
7. Cover letter MUST be in prose format (NO bullet points)

**EXPERIENCES TO KEEP (DO NOT MODIFY THESE):**
- Sun Life (Advanced Analytics & BI Intern) - May 2025 to Aug 2025
- CIBC (Data Engineering Intern) - Dec 2024 to Apr 2025
- CIBC (QA Developer Intern) - Sep 2024 to Dec 2024
- Delton Glebe Counseling Centre (Data Developer Intern) - Jun 2024 to Aug 2024

**PROJECTS TO KEEP:**
- GenAI Mentorship Matching Platform (2025)
- Stock Market Data Analysis Tool (2023-2024)
- E-commerce Platform Prototype (2024)

**AVOID THESE AI-SOUNDING PHRASES:**
- "leverage", "robust", "cutting-edge", "innovative solutions", "drive results"
- "stakeholder engagement", "synergy", "best-in-class", "game-changer"
- Instead use: simple, clear, direct language like a real student would write

**YOUR TASK:**
Given the base resume below and the job details, create:
1. A tailored LaTeX resume (210-217 lines) that emphasizes relevant skills and experiences
2. A cover letter in prose format (no bullets) that sounds natural and student-like

---

**BASE RESUME (LaTeX):**
```latex
{base_resume_latex}
```

---

**JOB DETAILS:**
- **Job Title:** {job_title}
- **Company:** {company}
- **Job Description:**
{job_description}

---

**OUTPUT FORMAT:**
Please respond with EXACTLY this format:

===TAILORED_RESUME_START===
[Your tailored LaTeX resume here - MUST be 210-217 lines]
===TAILORED_RESUME_END===

===COVER_LETTER_START===
[Your cover letter here - prose format, no bullets, natural student tone]
===COVER_LETTER_END===

**REMINDERS:**
- Count your LaTeX lines carefully (210-217 lines required)
- Use the candidate's email from their resume
- Include AWS Cloud Practitioner cert
- Keep all 4 work experiences unchanged
- Natural student language, not corporate jargon
- Cover letter in prose (no bullets)
"""

    try:
        response = requests.post(
            MISTRAL_API_URL,
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistral-small-latest",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more consistent output
                "max_tokens": 8000
            },
            timeout=60
        )

        if response.status_code != 200:
            return None, None, f"❌ Mistral API Error: {response.status_code} - {response.text}"

        result = response.json()
        content = result['choices'][0]['message']['content']

        # Parse the response
        tailored_resume = None
        cover_letter = None

        if "===TAILORED_RESUME_START===" in content and "===TAILORED_RESUME_END===" in content:
            resume_start = content.find("===TAILORED_RESUME_START===") + len("===TAILORED_RESUME_START===")
            resume_end = content.find("===TAILORED_RESUME_END===")
            tailored_resume = content[resume_start:resume_end].strip()

        if "===COVER_LETTER_START===" in content and "===COVER_LETTER_END===" in content:
            letter_start = content.find("===COVER_LETTER_START===") + len("===COVER_LETTER_START===")
            letter_end = content.find("===COVER_LETTER_END===")
            cover_letter = content[letter_start:letter_end].strip()

        # Validate resume
        if tailored_resume:
            line_count = len(tailored_resume.split('\n'))
            if line_count < 210 or line_count > 217:
                status = f"⚠️ Warning: Resume has {line_count} lines (should be 210-217). Please review."
            else:
                status = f"✅ Success! Resume tailored ({line_count} lines)"
        else:
            status = "❌ Failed to parse resume from AI response"

        return tailored_resume, cover_letter, status

    except requests.exceptions.Timeout:
        return None, None, "❌ Request timed out. Please try again."
    except Exception as e:
        return None, None, f"❌ Error: {str(e)}"
