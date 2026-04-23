#!/bin/bash

# FinShield Quick Start Script
# Run all servers in parallel

echo "🚀 Starting FinShield Application..."

# Check if required tools are installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed"
    exit 1
fi

echo "✅ Node.js and Python found"

# Start Backend
echo "📦 Starting Backend (Port 5000)..."
cd backend
npm install --quiet 2>/dev/null
npm run dev &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Start ML Model Server
echo "🤖 Starting ML Model Server (Port 5001)..."
cd ../backend_ml
pip install -q -r requirements.txt 2>/dev/null
python app.py &
MODEL_PID=$!
echo "✅ ML Server started (PID: $MODEL_PID)"

# Start Frontend
echo "🎨 Starting Frontend (Port 3000)..."
cd ../frontend
npm install --quiet 2>/dev/null
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║         🛡️ FinShield is Ready!                         ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  📱 Frontend:   http://localhost:3000                  ║"
echo "║  🔐 Backend:    http://localhost:5000                  ║"
echo "║  🤖 ML Model:   http://localhost:5001                  ║"
echo "║                                                        ║"
echo "║  Press Ctrl+C to stop all servers                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Wait for interruption
wait
