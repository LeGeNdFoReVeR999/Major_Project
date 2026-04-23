@echo off
title FinShield - Quick Start

echo.
echo 🚀 Starting FinShield Application...
echo.

REM Color codes for output
REM 0A = Black bg + Light Green text
REM 0C = Black bg + Light Red text
REM 0F = Black bg + White text

if not exist backend (
    echo ❌ Backend folder not found
    pause
    exit /b 1
)

if not exist backend_ml (
    echo ❌ Backend_ML folder not found
    pause
    exit /b 1
)

if not exist frontend (
    echo ❌ Frontend folder not found
    pause
    exit /b 1
)

echo ✅ Project structure verified
echo.

REM Start Backend
echo 📦 Starting Backend Server (Port 5000)...
start cmd /k "cd backend && npm install && npm run dev"
timeout /t 2 /nobreak

REM Start ML Model
echo 🤖 Starting ML Model Server (Port 5001)...
start cmd /k "cd backend_ml && python app.py"
timeout /t 2 /nobreak

REM Start Frontend
echo 🎨 Starting Frontend (Port 3000)...
start cmd /k "cd frontend && npm install && npm start"
timeout /t 2 /nobreak

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║         🛡️ FinShield is Starting!                      ║
echo ╠════════════════════════════════════════════════════════╣
echo ║                                                        ║
echo ║  📱 Frontend:   http://localhost:3000                  ║
echo ║  🔐 Backend:    http://localhost:5000                  ║
echo ║  🤖 ML Model:   http://localhost:5001                  ║
echo ║                                                        ║
echo ║  Each service will open in a new terminal window       ║
echo ║                                                        ║
echo ║  ⏳ Wait 30-60 seconds for all servers to start        ║
echo ║  🌐 Then open http://localhost:3000 in your browser   ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.
pause
