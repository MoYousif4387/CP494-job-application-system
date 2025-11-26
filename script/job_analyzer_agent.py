from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
import os
import pandas as pd

# Set up Groq API (get free API key from https://console.groq.com)
# Load API key from environment variable or .env file
# os.environ["GROQ_API_KEY"] = "your_api_key_here"

def create_job_analyzer_agent():
    """Create the Job Analyzer agent"""
    
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0.3  # Lower = more consistent
    )
    
    job_analyzer = Agent(
        role='Job Compatibility Analyst',
        goal='Analyze job postings and score them for candidate fit',
        backstory='''You are an expert technical recruiter with 10+ years of experience 
        matching candidates to positions. You understand job requirements deeply and can 
        identify good matches even when requirements don't perfectly align.''',
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    return job_analyzer

def analyze_job(agent, job_description, resume_text):
    """Analyze a single job against a resume"""
    
    task = Task(
        description=f"""
        Analyze this job posting and score the compatibility with the candidate's resume.
        
        JOB DESCRIPTION:
        {job_description}
        
        CANDIDATE RESUME:
        {resume_text}
        
        Provide:
        1. Compatibility score (0-10)
        2. Key matching skills
        3. Skills gaps
        4. Recommendation (Apply/Don't Apply/Maybe)
        5. Brief reasoning (2-3 sentences)
        """,
        expected_output="A structured analysis with score, skills match, gaps, and recommendation",
        agent=agent
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )
    
    result = crew.kickoff()
    return result

if __name__ == "__main__":
    # Test the agent
    agent = create_job_analyzer_agent()
    
    # Sample job (replace with real job from your database)
    sample_job = """
    Software Engineer Intern - Summer 2025
    
    We're seeking a motivated software engineering intern to join our team.
    
    Requirements:
    - Currently pursuing Computer Science degree
    - Knowledge of Python, Java, or C++
    - Understanding of data structures and algorithms
    - Experience with Git
    - Strong problem-solving skills
    
    Nice to have:
    - Experience with web frameworks (React, Django)
    - Cloud platforms (AWS, Azure)
    - Previous internship experience
    """
    
    # Your resume (simplified version)
    sample_resume = """
    Computer Science Student at Wilfrid Laurier University
    
    Skills:
    - Languages: Python, Java, C++, JavaScript
    - Frameworks: React, Flask, n8n
    - Tools: Git, Docker, SQLite
    - AI/ML: CrewAI, Ollama, LangChain
    
    Projects:
    - Multi-agent AI job search system (Current)
    - Various coursework projects in CP493/CP494
    
    Currently working on agentic AI systems and automation.
    """
    
    print("🤖 Analyzing job compatibility...\n")
    result = analyze_job(agent, sample_job, sample_resume)
    
    print("\n" + "="*50)
    print("ANALYSIS RESULT:")
    print("="*50)
    print(result)