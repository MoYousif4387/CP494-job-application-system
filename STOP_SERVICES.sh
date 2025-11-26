#!/bin/bash
# Stop all CP494 services

echo "🛑 Stopping CP494 Job Application System services..."

# Kill by PID files if they exist
if [ -f "logs/fastapi.pid" ]; then
    PID=$(cat logs/fastapi.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Stopped FastAPI (PID: $PID)"
    else
        echo "⚠️  FastAPI process not found"
    fi
    rm logs/fastapi.pid
fi

if [ -f "logs/gradio.pid" ]; then
    PID=$(cat logs/gradio.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Stopped Gradio (PID: $PID)"
    else
        echo "⚠️  Gradio process not found"
    fi
    rm logs/gradio.pid
fi

# Fallback: kill by port
if lsof -ti:8000 >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9
    echo "✅ Killed process on port 8000 (FastAPI)"
fi

if lsof -ti:7860 >/dev/null 2>&1; then
    lsof -ti:7860 | xargs kill -9
    echo "✅ Killed process on port 7860 (Gradio)"
fi

echo ""
echo "✅ All services stopped"
