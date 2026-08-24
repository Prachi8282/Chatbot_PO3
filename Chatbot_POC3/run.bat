@echo off
set PORT=8002
echo ==========================================================
echo Starting Secure Bank Details & Incident Chatbot Ingestion...
echo ==========================================================

rem Run document ingestion pipeline
"c:\Users\PrachiAgarwal\Desktop\POC - 01 (3)\POC - 01\.python-portable\python.exe" ingest.py

echo ==========================================================
echo Starting Uvicorn Web Server on Port %PORT%...
echo ==========================================================

rem Launch FastAPI web application
"c:\Users\PrachiAgarwal\Desktop\POC - 01 (3)\POC - 01\.python-portable\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload

pause
