#!/bin/bash
# Quick start script for CP494 Job Application System

echo "=================================================="
echo "🚀 CP494 Job Application System - Starting..."
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "simple_api_service.py" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    echo "Please cd to: /Users/mahmoud/job-search-ai/CP494-project/"
    exit 1
fi

echo -e "${YELLOW}📋 Pre-flight checks...${NC}"

# Check if ports are already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Port 8000 already in use (FastAPI may already be running)${NC}"
    echo "   Kill existing process? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        lsof -ti:8000 | xargs kill -9
        echo -e "${GREEN}✅ Killed process on port 8000${NC}"
    fi
fi

if lsof -Pi :7860 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Port 7860 already in use (Gradio may already be running)${NC}"
    echo "   Kill existing process? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        lsof -ti:7860 | xargs kill -9
        echo -e "${GREEN}✅ Killed process on port 7860${NC}"
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python3 found${NC}"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found (continuing anyway)${NC}"
fi

# Check key dependencies
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
python3 -c "import fastapi" 2>/dev/null && echo -e "${GREEN}✅ FastAPI installed${NC}" || echo -e "${RED}❌ FastAPI missing${NC}"
python3 -c "import gradio" 2>/dev/null && echo -e "${GREEN}✅ Gradio installed${NC}" || echo -e "${RED}❌ Gradio missing${NC}"
python3 -c "import crewai" 2>/dev/null && echo -e "${GREEN}✅ CrewAI installed${NC}" || echo -e "${RED}❌ CrewAI missing${NC}"

echo ""
echo -e "${YELLOW}🚀 Starting services...${NC}"
echo ""

# Create log directory
mkdir -p logs

# Start FastAPI in background
echo -e "${YELLOW}Starting FastAPI service on port 8000...${NC}"
nohup python3 simple_api_service.py > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo -e "${GREEN}✅ FastAPI started (PID: $FASTAPI_PID)${NC}"

# Wait a moment for FastAPI to start
sleep 3

# Check if FastAPI is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ FastAPI health check passed${NC}"
else
    echo -e "${RED}❌ FastAPI not responding (check logs/fastapi.log)${NC}"
fi

# Start Gradio in background
echo -e "${YELLOW}Starting Gradio UI on port 7860...${NC}"
cd ui
nohup python3 app.py > ../logs/gradio.log 2>&1 &
GRADIO_PID=$!
cd ..
echo -e "${GREEN}✅ Gradio started (PID: $GRADIO_PID)${NC}"

# Wait for Gradio to start
sleep 5

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 All services started!${NC}"
echo "=================================================="
echo ""
echo "📊 Service URLs:"
echo "   FastAPI:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Gradio:   http://localhost:7860"
echo "   n8n:      http://localhost:5678"
echo ""
echo "📝 Process IDs:"
echo "   FastAPI: $FASTAPI_PID"
echo "   Gradio:  $GRADIO_PID"
echo ""
echo "📋 Logs:"
echo "   FastAPI: logs/fastapi.log"
echo "   Gradio:  logs/gradio.log"
echo ""
echo "🛑 To stop services:"
echo "   kill $FASTAPI_PID $GRADIO_PID"
echo "   or run: ./STOP_SERVICES.sh"
echo ""
echo -e "${GREEN}✅ System ready! Open http://localhost:7860 in your browser${NC}"
echo ""

# Save PIDs to file for easy stopping
echo "$FASTAPI_PID" > logs/fastapi.pid
echo "$GRADIO_PID" > logs/gradio.pid
