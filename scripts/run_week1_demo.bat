@echo off
setlocal
echo Starting AI Video Attendance - Week 1 Pipeline Demo...
set PYTHONPATH=ai-service
python ai-service\app\main.py %*
pause
