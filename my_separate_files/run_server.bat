@echo off
echo Starting NER Logistics Intelligence Platform...
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
pause
