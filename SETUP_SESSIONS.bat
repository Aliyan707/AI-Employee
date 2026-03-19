@echo off
echo ============================================================
echo AI Employee - Social Media Session Setup
echo ============================================================
echo.
echo This will open browser windows for LinkedIn and Facebook.
echo Log in manually. Sessions are saved for automated posting.
echo.
echo Starting setup...
echo.

cd /d "C:\Users\Cs\Desktop\AI Employee-"
python setup_social_sessions.py all

echo.
echo Press any key to close...
pause > nul
