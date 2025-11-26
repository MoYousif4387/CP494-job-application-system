#!/bin/bash
# Daily automated refresh of all job sources
# Runs at 6:00 AM via cron job
# Usage: ./daily_refresh.sh

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)
LOG_FILE="$LOG_DIR/refresh_${DATE}.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Start logging
echo "======================================================================" | tee -a "$LOG_FILE"
echo "🔄 DAILY JOB REFRESH - $DATE $TIME" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Run master scraper
echo "📥 Running master scraper..." | tee -a "$LOG_FILE"
python3 "$SCRIPT_DIR/master_scraper.py" 2>&1 | tee -a "$LOG_FILE"

SCRAPER_EXIT_CODE=$?

if [ $SCRAPER_EXIT_CODE -eq 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ Scraping completed successfully" | tee -a "$LOG_FILE"
else
    echo "" | tee -a "$LOG_FILE"
    echo "⚠️  Scraping completed with errors (exit code: $SCRAPER_EXIT_CODE)" | tee -a "$LOG_FILE"
fi

# Check database size
echo "" | tee -a "$LOG_FILE"
echo "📊 Database statistics:" | tee -a "$LOG_FILE"
if [ -f "$PROJECT_DIR/database/jobs.db" ]; then
    DB_SIZE=$(du -h "$PROJECT_DIR/database/jobs.db" | cut -f1)
    echo "  - Database size: $DB_SIZE" | tee -a "$LOG_FILE"

    # Count jobs in each table
    echo "  - Job counts:" | tee -a "$LOG_FILE"
    sqlite3 "$PROJECT_DIR/database/jobs.db" "SELECT 'raw_jobs: ' || COUNT(*) FROM raw_jobs" 2>/dev/null | tee -a "$LOG_FILE"
    sqlite3 "$PROJECT_DIR/database/jobs.db" "SELECT 'github_jobs: ' || COUNT(*) FROM github_jobs" 2>/dev/null | tee -a "$LOG_FILE"
    sqlite3 "$PROJECT_DIR/database/jobs.db" "SELECT 'zapply_jobs: ' || COUNT(*) FROM zapply_jobs" 2>/dev/null | tee -a "$LOG_FILE"

    TOTAL_JOBS=$(sqlite3 "$PROJECT_DIR/database/jobs.db" "SELECT (SELECT COUNT(*) FROM raw_jobs) + (SELECT COUNT(*) FROM github_jobs) + (SELECT COUNT(*) FROM zapply_jobs)" 2>/dev/null)
    echo "  - TOTAL JOBS: $TOTAL_JOBS" | tee -a "$LOG_FILE"
else
    echo "  ⚠️  Database not found" | tee -a "$LOG_FILE"
fi

# Restart services to pick up new data (optional)
echo "" | tee -a "$LOG_FILE"
echo "🔄 Services status:" | tee -a "$LOG_FILE"

# Check if FastAPI is running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "  ✅ FastAPI is running (port 8000)" | tee -a "$LOG_FILE"
    # Optional: Restart FastAPI to reload data
    # echo "  🔄 Restarting FastAPI..." | tee -a "$LOG_FILE"
    # kill $(lsof -ti:8000) 2>/dev/null
    # nohup python3 simple_api_service.py > logs/fastapi.log 2>&1 &
    # echo "  ✅ FastAPI restarted" | tee -a "$LOG_FILE"
else
    echo "  ⚠️  FastAPI not running" | tee -a "$LOG_FILE"
fi

# Check if Gradio is running
if lsof -Pi :7860 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "  ✅ Gradio is running (port 7860)" | tee -a "$LOG_FILE"
else
    echo "  ⚠️  Gradio not running" | tee -a "$LOG_FILE"
fi

# Summary
echo "" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "✅ DAILY REFRESH COMPLETED - $(date +%Y-%m-%d\ %H:%M:%S)" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📁 Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Exit with scraper's exit code
exit $SCRAPER_EXIT_CODE
