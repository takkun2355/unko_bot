@echo off
powershell -ExecutionPolicy Bypass -NoExit -Command ^
"& 'C:/Users/takku/Documents/bots/unko/venv/Scripts/Activate.ps1'; ^
& 'C:/Users/takku/Documents/bots/unko/venv/Scripts/python.exe' 'C:/Users/takku/Documents/bots/unko/bot_manager.py'"
