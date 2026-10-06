@echo off
echo ========================================================
echo Pushing 'my-changes' branch to GitHub (trixvenom12/NER)...
echo ========================================================
cd /d "%~dp0"
git push -u origin my-changes
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ----------------------------------------------------
    echo If push failed due to permission or authentication:
    echo 1. If you need to log in, a browser prompt should appear.
    echo 2. If you don't have write access to trixvenom12/NER,
    echo    push to your own fork using:
    echo      git remote set-url origin https://github.com/YOUR_USERNAME/NER.git
    echo      git push -u origin my-changes
    echo ----------------------------------------------------
)
echo.
pause
