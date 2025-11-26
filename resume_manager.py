#!/usr/bin/env python3
"""
Resume Management Service for CP494 Job Application System
Handles resume upload, parsing, and skill extraction
"""

import os
import json
import sqlite3
import PyPDF2
import docx
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path

class ResumeManager:
    def __init__(self, db_path="database/applications.db", groq_api_key=None, mistral_api_key=None, preferred_api="mistral"):
        self.db_path = db_path
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.mistral_api_key = mistral_api_key or os.getenv("MISTRAL_API_KEY")
        self.preferred_api = preferred_api  # "mistral", "groq", or "auto"
        self.uploads_dir = Path("uploads/resumes")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""

    def extract_resume_text(self, file_path: str, file_type: str) -> str:
        """Extract text from resume file based on type"""
        if file_type.lower() == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_type.lower() in ['docx', 'doc']:
            return self.extract_text_from_docx(file_path)
        elif file_type.lower() == 'txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def extract_skills_smart(self, resume_text: str) -> List[str]:
        """Smart skill extraction with API fallback chain"""
        if self.preferred_api == "mistral":
            return self.extract_skills_with_mistral(resume_text)
        elif self.preferred_api == "groq":
            return self.extract_skills_with_groq(resume_text)
        else:  # "auto" - try Mistral first, then Groq, then fallback
            try:
                if self.mistral_api_key:
                    return self.extract_skills_with_mistral(resume_text)
                elif self.groq_api_key:
                    return self.extract_skills_with_groq(resume_text)
            except:
                pass
            return self.extract_skills_fallback(resume_text)

    def extract_skills_with_mistral(self, resume_text: str) -> List[str]:
        """Extract skills from resume text using Mistral API"""
        if not self.mistral_api_key:
            print("No Mistral API key available, trying Groq or fallback")
            return self.extract_skills_with_groq(resume_text)

        try:
            from mistralai import Mistral

            client = Mistral(api_key=self.mistral_api_key)

            prompt = f"""Extract technical skills, programming languages, frameworks, tools, and technologies from this resume.
Return ONLY a JSON array of skills, no other text.

Resume text:
{resume_text[:2000]}

Example format: ["Python", "JavaScript", "React", "SQL", "Machine Learning"]
"""

            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.1,
                max_tokens=500
            )

            if response and response.choices:
                content = response.choices[0].message.content.strip()

                # Try to parse as JSON
                try:
                    import json
                    skills = json.loads(content)
                    if isinstance(skills, list):
                        return [skill.strip() for skill in skills if skill.strip()]
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract from text
                    return self.extract_skills_from_text_response(content)

        except Exception as e:
            print(f"Error using Mistral API for skill extraction: {e}")
            # Fallback to Groq
            return self.extract_skills_with_groq(resume_text)

        # Ultimate fallback to local extraction
        return self.extract_skills_fallback(resume_text)

    def extract_skills_with_groq(self, resume_text: str) -> List[str]:
        """Extract skills from resume text using Groq API"""
        if not self.groq_api_key:
            print("No Groq API key available, using fallback skill extraction")
            return self.extract_skills_fallback(resume_text)

        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""
            Extract technical skills, programming languages, frameworks, tools, and technologies from this resume.
            Return ONLY a JSON array of skills, no other text.

            Resume text:
            {resume_text[:2000]}  # Limit text to avoid token limits

            Example format: ["Python", "JavaScript", "React", "SQL", "Machine Learning"]
            """

            data = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "model": "mixtral-8x7b-32768",
                "temperature": 0.1,
                "max_tokens": 500
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                # Try to parse as JSON
                try:
                    skills = json.loads(content)
                    if isinstance(skills, list):
                        return [skill.strip() for skill in skills if skill.strip()]
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract from text
                    return self.extract_skills_from_text_response(content)

        except Exception as e:
            print(f"Error using Groq API for skill extraction: {e}")

        # Fallback to local extraction
        return self.extract_skills_fallback(resume_text)

    def extract_skills_from_text_response(self, text: str) -> List[str]:
        """Extract skills from non-JSON text response"""
        # Look for common patterns in AI responses
        lines = text.split('\n')
        skills = []

        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('• '):
                skill = line[2:].strip()
                if skill:
                    skills.append(skill)
            elif ',' in line and len(line.split(',')) > 2:
                # Looks like a comma-separated list
                for skill in line.split(','):
                    skill = skill.strip().strip('"').strip("'")
                    if skill:
                        skills.append(skill)

        return skills[:20]  # Limit to top 20 skills

    def extract_skills_fallback(self, resume_text: str) -> List[str]:
        """Fallback skill extraction using keyword matching"""
        # Common technical skills to look for
        skill_keywords = [
            # Programming Languages
            "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift",
            "Kotlin", "TypeScript", "Scala", "R", "MATLAB", "SQL", "HTML", "CSS",

            # Frameworks & Libraries
            "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask", "FastAPI",
            "Spring", "Laravel", "Ruby on Rails", "TensorFlow", "PyTorch", "Scikit-learn",
            "Pandas", "NumPy", "jQuery", "Bootstrap",

            # Databases
            "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite", "Oracle", "SQL Server",
            "Cassandra", "DynamoDB", "Elasticsearch",

            # Cloud & DevOps
            "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "GitLab CI",
            "Terraform", "Ansible", "Linux", "Unix", "Bash", "PowerShell",

            # Tools & Technologies
            "Git", "GitHub", "GitLab", "Jira", "Confluence", "Slack", "Figma", "Adobe",
            "Photoshop", "Illustrator", "Tableau", "Power BI", "Excel", "Word", "PowerPoint",

            # Data Science & ML
            "Machine Learning", "Deep Learning", "Data Analysis", "Statistics", "Big Data",
            "Apache Spark", "Hadoop", "Kafka", "Airflow", "MLflow", "Jupyter",

            # Web Technologies
            "REST API", "GraphQL", "JSON", "XML", "WebSocket", "HTTP", "HTTPS", "OAuth",

            # Mobile Development
            "iOS", "Android", "React Native", "Flutter", "Xamarin",

            # Other
            "Agile", "Scrum", "Kanban", "DevOps", "CI/CD", "Testing", "Unit Testing",
            "API Development", "Microservices", "Blockchain", "Cybersecurity"
        ]

        resume_lower = resume_text.lower()
        found_skills = []

        for skill in skill_keywords:
            if skill.lower() in resume_lower:
                found_skills.append(skill)

        return found_skills

    def extract_contact_info(self, resume_text: str) -> Dict[str, str]:
        """Extract contact information from resume text"""
        import re

        contact_info = {}

        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, resume_text)
        if email_match:
            contact_info['email'] = email_match.group()

        # Extract phone number
        phone_pattern = r'(\+?1?[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, resume_text)
        if phone_match:
            contact_info['phone'] = phone_match.group()

        # Extract LinkedIn URL
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_match = re.search(linkedin_pattern, resume_text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin_url'] = f"https://{linkedin_match.group()}"

        # Extract GitHub URL
        github_pattern = r'github\.com/[\w-]+'
        github_match = re.search(github_pattern, resume_text, re.IGNORECASE)
        if github_match:
            contact_info['github_url'] = f"https://{github_match.group()}"

        return contact_info

    def save_resume(self, file_content: bytes, filename: str, is_base_resume: bool = False) -> Dict[str, Any]:
        """Save uploaded resume file and extract information"""
        try:
            # Determine file type
            file_extension = filename.split('.')[-1].lower()
            if file_extension not in ['pdf', 'docx', 'txt']:
                raise ValueError(f"Unsupported file type: {file_extension}")

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename}"
            file_path = self.uploads_dir / safe_filename

            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Extract text
            resume_text = self.extract_resume_text(str(file_path), file_extension)

            if not resume_text.strip():
                raise ValueError("Could not extract text from resume file")

            # Extract skills and contact info using smart API selection
            skills = self.extract_skills_smart(resume_text)
            contact_info = self.extract_contact_info(resume_text)

            # Save to database
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Insert/update user profile if this is a base resume
            if is_base_resume:
                cursor.execute("""
                    INSERT OR REPLACE INTO user_profiles
                    (id, email, phone, linkedin_url, github_url, skills, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?)
                """, (
                    contact_info.get('email'),
                    contact_info.get('phone'),
                    contact_info.get('linkedin_url'),
                    contact_info.get('github_url'),
                    json.dumps(skills),
                    datetime.now()
                ))

            # Insert resume record
            cursor.execute("""
                INSERT INTO resumes
                (user_profile_id, resume_content, original_filename, file_type, is_base_resume, created_at)
                VALUES (1, ?, ?, ?, ?, ?)
            """, (
                resume_text,
                filename,
                file_extension,
                is_base_resume,
                datetime.now()
            ))

            resume_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {
                "success": True,
                "resume_id": resume_id,
                "filename": filename,
                "file_type": file_extension,
                "skills_extracted": len(skills),
                "skills": skills,
                "contact_info": contact_info,
                "text_length": len(resume_text),
                "is_base_resume": is_base_resume
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, full_name, email, phone, location, linkedin_url, github_url,
                       skills, experience_years, education, created_at, updated_at
                FROM user_profiles
                WHERE id = 1
            """)

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "id": row[0],
                    "full_name": row[1],
                    "email": row[2],
                    "phone": row[3],
                    "location": row[4],
                    "linkedin_url": row[5],
                    "github_url": row[6],
                    "skills": json.loads(row[7]) if row[7] else [],
                    "experience_years": row[8],
                    "education": json.loads(row[9]) if row[9] else [],
                    "created_at": row[10],
                    "updated_at": row[11]
                }

            return None

        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

    def get_base_resume(self) -> Optional[Dict[str, Any]]:
        """Get the user's base resume"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, resume_content, original_filename, file_type, created_at
                FROM resumes
                WHERE user_profile_id = 1 AND is_base_resume = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """)

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "id": row[0],
                    "content": row[1],
                    "filename": row[2],
                    "file_type": row[3],
                    "created_at": row[4]
                }

            return None

        except Exception as e:
            print(f"Error getting base resume: {e}")
            return None

if __name__ == "__main__":
    # Test the resume manager
    manager = ResumeManager()

    # Test with sample resume text
    sample_resume = """
    John Doe
    Software Developer
    john.doe@email.com
    (555) 123-4567
    linkedin.com/in/johndoe
    github.com/johndoe

    SKILLS:
    - Python, JavaScript, Java
    - React, Node.js, Django
    - MySQL, PostgreSQL, MongoDB
    - AWS, Docker, Git
    - Machine Learning, TensorFlow

    EXPERIENCE:
    Software Developer Intern | TechCorp | 2023-2024
    - Developed web applications using Python and React
    - Implemented machine learning models for data analysis
    - Worked with databases and cloud infrastructure
    """

    # Test skill extraction
    skills = manager.extract_skills_with_groq(sample_resume)
    print(f"Extracted skills: {skills}")

    # Test contact info extraction
    contact = manager.extract_contact_info(sample_resume)
    print(f"Contact info: {contact}")