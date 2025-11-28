# 🚀 Quick Start Guide
**Updated:** January 2025

---

## ⚡ FASTEST WAY TO START

```bash
cd job-search-ai-system
./START_SERVICES.sh
```

Then open: **http://localhost:7860**

That's it! 🎉

---

## 📋 WHAT JUST HAPPENED

The start script launched:
1. ✅ **FastAPI** on http://localhost:8000 (backend API)
2. ✅ **Gradio** on http://localhost:7860 (web interface)
3. ✅ **Logs** saved to `logs/` directory

**n8n** is already running on http://localhost:5678

---

## 🎯 WHAT TO DO NEXT

### Option 1: Use the Web Interface
1. Open http://localhost:7860
2. Go to "🔍 Search Jobs" tab
3. Enter: "software intern"
4. Click "Search Jobs"
5. See 9 real jobs from database!

### Option 2: Test Job Analysis
1. Go to "📊 Job Analysis" tab
2. Paste a job URL (or use any text)
3. Enter your skills: `Python, SQL, FastAPI`
4. Click "Analyze Job"
5. See compatibility score from CrewAI agent!

### Option 3: Test Resume Tailoring
1. Go to "📝 Resume Tailor" tab
2. Paste a job description
3. Your resume is already loaded from `docs/resume.txt`
4. Click "Generate Tailored Resume"
5. Get AI-customized resume!

---

## 🛑 HOW TO STOP

```bash
./STOP_SERVICES.sh
```

Or manually:
```bash
kill $(cat logs/fastapi.pid) $(cat logs/gradio.pid)
```

---

## 📊 CHECK STATUS

```bash
# Check if services are running
curl http://localhost:8000/health
curl http://localhost:7860

# View logs
tail -f logs/fastapi.log
tail -f logs/gradio.log

# Check what's on each port
lsof -i :8000
lsof -i :7860
lsof -i :5678
```

---

## 📁 IMPORTANT FILES

### Data Files:
- `database/jobs.db` - 9 real jobs from JobSpy
- `database/jobs_sample.csv` - Same 9 jobs in CSV format
- `database/applications.db` - Application tracking (empty, ready to use)
- `docs/resume.txt` - Your resume (created for you!)

### Service Files:
- `simple_api_service.py` - FastAPI backend
- `ui/app.py` - Gradio web interface
- `crews/job_application_crew.py` - CrewAI multi-agent system
- `job_sources.py` - Job board integrator

### Scripts:
- `START_SERVICES.sh` - Launch everything ✅
- `STOP_SERVICES.sh` - Stop everything ✅
- `script/job_analyzer_agent.py` - Test single agent

---

## 🔧 TROUBLESHOOTING

### Port Already in Use?
```bash
# Kill whatever's on port 8000
lsof -ti:8000 | xargs kill -9

# Kill whatever's on port 7860
lsof -ti:7860 | xargs kill -9

# Then restart
./START_SERVICES.sh
```

### Services Won't Start?
Check the logs:
```bash
cat logs/fastapi.log
cat logs/gradio.log
```

### Missing Dependencies?
```bash
pip install -r requirements.txt
```

---

## 📈 NEXT STEPS FOR YOUR PROJECT

### 1. Collect More Jobs (Current: 9)
```bash
python3 -c "
from jobspy import scrape_jobs
import pandas as pd

jobs = scrape_jobs(
    site_name=['indeed', 'linkedin'],
    search_term='software intern',
    location='Toronto, ON',
    results_wanted=50
)

jobs.to_csv('database/more_jobs.csv', index=False)
print(f'Collected {len(jobs)} jobs!')
"
```

### 2. Analyze Jobs with CrewAI
Use the web interface:
1. Search for jobs
2. Click on each job
3. Analyze compatibility
4. Save results

### 3. Collect Metrics for Paper
- Processing time per job
- Compatibility scores distribution
- High-match jobs (score >8)
- Agent accuracy vs manual review

---

## 🎓 FOR YOUR RESEARCH PAPER

### Current Stats You Can Report:
- ✅ System components: FastAPI, Gradio, CrewAI, n8n
- ✅ Jobs in database: 9 (from JobSpy scraping)
- ✅ Multi-agent architecture: 3 specialized agents
- ✅ Job sources: Indeed, LinkedIn, Government, Universities
- ✅ Database: SQLite with 5 tables

### Stats You Still Need:
- ❌ Total jobs analyzed: 0 (run analysis!)
- ❌ Processing time per job: (measure it!)
- ❌ Agent accuracy: (manual review 20 jobs)
- ❌ High-match jobs found: (count score >8)

---

## 📞 SUPPORT

### View Full Documentation:
- `SYSTEM_STATUS_VERIFIED.md` - Complete verification report
- `BRIEFING_FOR_CLAUDE_WEB.md` - Comprehensive briefing
- `README.md` - Original project documentation
- `STATUS.md` - Demo status report

### Common Tasks:

**Check Database:**
```bash
sqlite3 database/jobs.db "SELECT COUNT(*) FROM raw_jobs"
sqlite3 database/applications.db "SELECT * FROM applications"
```

**Test Agent:**
```bash
cd script
python3 job_analyzer_agent.py
```

**View API Docs:**
http://localhost:8000/docs

---

## ✅ VERIFICATION CHECKLIST

Run this to verify everything:

```bash
echo "🔍 Checking system status..."
echo ""

# Check services
curl -s http://localhost:8000/health && echo "✅ FastAPI running" || echo "❌ FastAPI not running"
curl -s http://localhost:7860 >/dev/null 2>&1 && echo "✅ Gradio running" || echo "❌ Gradio not running"
curl -s http://localhost:5678 >/dev/null 2>&1 && echo "✅ n8n running" || echo "❌ n8n not running"

# Check databases
sqlite3 database/jobs.db "SELECT COUNT(*) FROM raw_jobs" 2>/dev/null && echo "✅ jobs.db working" || echo "❌ jobs.db issue"
test -f database/applications.db && echo "✅ applications.db exists" || echo "❌ applications.db missing"

# Check resume
test -f docs/resume.txt && echo "✅ resume.txt exists" || echo "❌ resume.txt missing"

# Check agent
python3 -c "from script.job_analyzer_agent import create_job_analyzer_agent; create_job_analyzer_agent()" 2>/dev/null && echo "✅ CrewAI agent works" || echo "❌ Agent issue"

echo ""
echo "✅ Verification complete!"
```

---

## 🎯 YOUR PROJECT IS READY!

Everything is set up and working:
- ✅ Web interface running
- ✅ API backend running
- ✅ AI agents functional
- ✅ Database initialized
- ✅ Resume loaded
- ✅ Sample jobs available

**Just open http://localhost:7860 and start exploring!** 🚀

---

**Questions?** Check the documentation files or README.md for more information!
