#!/bin/bash
# One-time setup script to configure daily automated refresh
# Run this once: ./setup_cron.sh

# Get absolute path to daily_refresh.sh
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REFRESH_SCRIPT="$SCRIPT_DIR/daily_refresh.sh"

echo "========================================================================"
echo "🕐 CRON JOB SETUP FOR DAILY REFRESH"
echo "========================================================================"
echo ""
echo "This will set up a cron job to run daily at 6:00 AM"
echo "Script to run: $REFRESH_SCRIPT"
echo ""

# Check if script exists
if [ ! -f "$REFRESH_SCRIPT" ]; then
    echo "❌ Error: daily_refresh.sh not found at $REFRESH_SCRIPT"
    exit 1
fi

# Make sure script is executable
chmod +x "$REFRESH_SCRIPT"

# Create cron job entry
CRON_ENTRY="0 6 * * * $REFRESH_SCRIPT >> $SCRIPT_DIR/../logs/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -F "$REFRESH_SCRIPT" > /dev/null; then
    echo "⚠️  Cron job already exists for this script"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep -F "$REFRESH_SCRIPT"
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted"
        exit 1
    fi

    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v -F "$REFRESH_SCRIPT" | crontab -
    echo "✅ Removed existing cron job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo ""
echo "========================================================================"
echo "✅ CRON JOB INSTALLED SUCCESSFULLY"
echo "========================================================================"
echo ""
echo "Schedule: Daily at 6:00 AM"
echo "Command:  $REFRESH_SCRIPT"
echo "Logs:     $SCRIPT_DIR/../logs/cron.log"
echo ""
echo "Current cron jobs:"
crontab -l
echo ""
echo "========================================================================"
echo ""
echo "To verify cron job:"
echo "  crontab -l"
echo ""
echo "To remove cron job:"
echo "  crontab -l | grep -v daily_refresh | crontab -"
echo ""
echo "To test manually:"
echo "  $REFRESH_SCRIPT"
echo ""
echo "========================================================================"
