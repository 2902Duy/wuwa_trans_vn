@echo off
cd /d C:\Users\tduy2\Documents\antigravity\silly-darwin
set PYTHONIOENCODING=utf-8
if not exist .runlogs mkdir .runlogs
echo Starting wiki editor at http://127.0.0.1:8765
echo Keep this window open while using the editor.
D:\Program\Python\python.exe tools\wiki_editor\server.py
pause
