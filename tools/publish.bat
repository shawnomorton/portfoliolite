@echo off
rem One command: process new photos, commit, and push to GitHub (Windows).
rem   tools\publish.bat "Add Iceland series"
cd /d "%~dp0\.."
echo Building optimised images...
python tools\build.py || exit /b 1
git add -A
git diff --cached --quiet && (echo Nothing new to publish. & exit /b 0)
if "%~1"=="" (git commit -m "Update portfolio") else (git commit -m "%~1")
echo Pushing to GitHub...
git push
echo Done. GitHub Pages refreshes in a minute or two.
