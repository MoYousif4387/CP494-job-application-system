# CP494 - Automated Job Application System

**Student:** Mahmoud Yousif (MoYousif4387)
**Course:** CP494 - Applied Research in Computing
**Professor:** Dr. Emad Amin Mohammed
**Email:** 7wyb4387@gmail.com

---

## 🎯 Project Overview

An AI-powered job application automation system that streamlines the entire job search process from discovery to application submission. The system integrates multiple job boards, performs intelligent job-candidate matching, and generates tailored resumes and cover letters using advanced AI technologies.

## 🚀 **DEMO ACCESS**

**Quick Start Demo:**
```bash
cd CP494-project-demo
./start_demo.sh
```

**Demo URLs:**
- **Main Interface:** http://localhost:7861
- **API Documentation:** http://localhost:8001/docs

---

## ✨ Current Features (Demo Version)

### 🔍 **Job Search Engine**
- **Multi-source Integration:** Indeed, LinkedIn, SimplifyJobs, Zapply (371+ active jobs)
- **Smart Filtering:** Location, job type, and freshness-based filtering
- **Freshness Tracking:** Visual badges showing job age (green = 24h, yellow = 7d, blue = 30d)
- **FAANG Detection:** Automatic identification of top-tier tech companies
- **Real-time Results:** Instant search across 371+ internship and new graduate opportunities

### 📊 **Job Analysis**
- **Compatibility Scoring:** Match percentage between user skills and job requirements
- **Skill Gap Analysis:** Identifies missing skills and learning opportunities
- **Application Recommendations:** AI-generated advice for each position

### 📝 **Resume Tailoring**
- **Dynamic Generation:** Customizes resume for specific job requirements
- **Cover Letter Creation:** Automated personalized cover letters
- **Template System:** Professional formatting and presentation

### 📋 **Application Tracking**
- **Database Management:** SQLite-powered application history
- **Status Monitoring:** Track application progress (found, applied, interview, etc.)
- **Analytics Dashboard:** Application success metrics and insights

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Gradio UI     │───▶│  n8n Workflows │───▶│   FastAPI      │
│   (Port 7860)   │    │  (Port 5678)   │    │   (Port 8000)  │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                     │
         │                       ▼                     ▼
         │              ┌──────────────┐    ┌─────────────────┐
         │              │  Groq API    │    │ Job Sources     │
         │              │  (AI/LLM)    │    │ Integration     │
         │              └──────────────┘    └─────────────────┘
         ▼
┌─────────────────┐
│   SQLite DB     │
│   (Applications)│
└─────────────────┘
```

### **Technology Stack**
- **Frontend:** Gradio (Python-based web interface)
- **Backend:** FastAPI (RESTful API service)
- **Workflow Engine:** n8n (Automation and AI orchestration)
- **Database:** SQLite (Application data and user profiles)
- **AI/LLM:** Groq API (Job analysis and resume generation)
- **Job Sources:** Web scraping + API integrations

---

## 📊 Current Implementation Status (Updated Nov 26, 2025)

**Active Jobs Database:** 371+ fresh positions across 4 sources
- SimplifyJobs GitHub: 260 new grad positions
- Zapply GitHub: 75 ultra-fresh jobs (< 1 week old)
- JobSpy (Indeed): 34 local opportunities
- JobSpy (LinkedIn): 2 professional network jobs

| Feature | Status | Description |
|---------|--------|-------------|
| **Job Search** | ✅ **Complete** | Multi-source job discovery with real-time filtering |
| **Freshness Tracking** | ✅ **Complete** | Green/yellow/blue badges for job recency |
| **Job Analysis** | ✅ **Complete** | Automated compatibility analysis |
| **Resume Tailoring** | ✅ **Complete** | Automated resume and cover letter generation |
| **Application Tracking** | ✅ **Complete** | Database-driven application management |
| **Daily Automation** | ✅ **Complete** | Automatic job refresh every 24 hours |
| **Web Interface** | ✅ **Complete** | Professional Gradio-based UI with filters |
| **API Documentation** | ✅ **Complete** | Comprehensive FastAPI docs with examples |

---

## 🔄 Upcoming Enhancements

### **Phase 1: Advanced Resume Management** (In Progress)
- **File Upload System:** PDF, DOCX, and text resume parsing
- **AI Skill Extraction:** Groq-powered skill identification from resumes
- **Real Matching Logic:** User resume vs. actual job requirements
- **User Profile Management:** Persistent user data and preferences

### **Phase 2: Real Job Analysis** (Planned)
- **Web Scraping Engine:** Extract content from actual job posting URLs
- **AI Content Analysis:** Groq-powered job description parsing
- **Smart Compatibility:** Advanced matching algorithms
- **Clickable Job Links:** Direct access to original job postings

### **Phase 3: Workflow Automation** (Planned)
- **n8n Integration:** Fully automated job discovery and analysis
- **AI Pipeline:** End-to-end automation with Groq API
- **Batch Processing:** Multiple job analysis and resume generation
- **Application Automation:** One-click application submission

### **Phase 4: Export & Analytics** (Planned)
- **PDF Generation:** Professional resume and cover letter export
- **Application Analytics:** Success tracking and improvement insights
- **Interview Preparation:** AI-powered interview question generation
- **Market Analysis:** Job market trends and salary insights

---

## 🛠️ Installation & Setup

### **Prerequisites**
```bash
# Python 3.10+
python3 --version

# Required packages
pip install fastapi uvicorn gradio requests sqlite3 python-dotenv
```

### **Environment Setup**
1. **Clone Repository:**
   ```bash
   git clone https://github.com/MoYousif4387/CP494-job-application-system.git
   cd CP494-job-application-system
   ```

2. **Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Database Initialization:**
   ```bash
   # Database will auto-initialize on first run
   python3 simple_api_service.py
   ```

### **Running the Demo**
```bash
# Option 1: Use the demo script
cd CP494-project-demo
./start_demo.sh

# Option 2: Manual startup
# Terminal 1 - API Service
python3 simple_api_service.py

# Terminal 2 - Web Interface
cd ui && python3 app.py
```

---

## 📁 Project Structure

```
CP494-job-application-system/
├── README.md                 # This documentation
├── DEMO.md                   # Demo-specific instructions
├── simple_api_service.py     # Main FastAPI backend
├── job_sources.py           # Job board integration
├── resume_manager.py        # Resume handling (in development)
├── ui/
│   └── app.py               # Gradio web interface
├── database/
│   ├── schema.sql           # Database structure
│   └── applications.db      # SQLite database (auto-generated)
├── n8n-workflows/           # Automation workflows
│   ├── job-scout.json
│   ├── resume-optimizer.json
│   └── main-orchestrator.json
├── uploads/                 # Resume file storage
└── docs/                    # Additional documentation
```

---

## 🧪 Testing & Validation

### **Demo Test Cases**
1. **Job Search Test:**
   - Search for "software intern" in "Toronto"
   - Verify 6+ results with relevance scores
   - Check job sources (Indeed, LinkedIn, Government, Universities)

2. **Job Analysis Test:**
   - Input job URL and skills list
   - Verify compatibility analysis and recommendations
   - Test with different skill combinations

3. **Resume Tailoring Test:**
   - Input job description and base resume
   - Generate tailored resume and cover letter
   - Verify customization based on job requirements

### **API Testing**
```bash
# Health check
curl http://localhost:8000/health

# Job search
curl -X POST http://localhost:8000/search-jobs \
  -H "Content-Type: application/json" \
  -d '{"keywords": "Python Developer", "location": "Toronto"}'
```

---

## 📈 Research & Innovation

### **Novel Contributions**
1. **Multi-source Job Aggregation:** Unified interface for diverse job sources
2. **AI-Powered Matching:** Groq LLM integration for intelligent job analysis
3. **Automated Workflow Pipeline:** n8n-based job application automation
4. **Real-time Skill Gap Analysis:** Dynamic learning recommendations

### **Technical Challenges Addressed**
- **Web Scraping Complexity:** Handling different job board structures
- **AI Integration:** Balancing API costs with analysis quality
- **User Experience:** Professional interface for complex backend processes
- **Data Management:** Efficient storage and retrieval of job/application data

---

## 🎯 Success Metrics (Nov 26, 2025)

- **Job Discovery:** 371+ active positions from 4 real sources
- **Freshness:** 75 ultra-fresh jobs (< 1 week old) via Zapply
- **Search Performance:** <1 second response time for all queries
- **Resume Generation:** 10-15 seconds per customized resume
- **Daily Automation:** Automatic database refresh every 24 hours
- **User Interface:** Professional Gradio interface with real-time filtering
- **System Reliability:** Production-ready with comprehensive error handling

---

## 🤝 Collaboration & Development

**Professor Access:**
- **Repository:** https://github.com/MoYousif4387/CP494-job-application-system
- **Collaborator Invitation:** Sent to emad.amin.mohammed@gmail.com
- **Demo Access:** Available at provided URLs after running `start_demo.sh`

**Development Approach:**
- **Agile Methodology:** Iterative development with working prototypes
- **Version Control:** Git-based with clear commit messages
- **Documentation:** Comprehensive code and API documentation
- **Testing:** Continuous testing with real job data

---

## 📞 Contact & Support

**Student Contact:**
- **Name:** Mahmoud Yousif
- **Email:** 7wyb4387@gmail.com
- **GitHub:** [@MoYousif4387](https://github.com/MoYousif4387)

**Professor Contact:**
- **Email:** emad.amin.mohammed@gmail.com

---

## 📄 License & Acknowledgments

**Academic Use:** This project is developed for CP494 coursework and research purposes.

**Technologies Used:**
- Gradio (Interface framework)
- FastAPI (API framework)
- n8n (Workflow automation)
- Groq (AI/LLM services)
- SQLite (Database)

---

*Last Updated: January 2025*
*Repository: https://github.com/MoYousif4387/CP494-job-application-system*
