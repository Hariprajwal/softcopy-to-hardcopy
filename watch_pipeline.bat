@echo off
echo Starting the Soft Copy to Hard Copy Folder Watcher...
echo Drop files into pipeline\input\ to automatically process them.
python auto_pipeline.py --watch
pause
