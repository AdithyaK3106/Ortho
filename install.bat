@echo off
REM Ortho Quick Install for Windows

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Ortho Quick Install
echo ========================================
echo.

REM Step 1: Clone
if not exist "Ortho" (
    echo [1/3] Cloning Ortho...
    git clone https://github.com/AdithyaK3106/Ortho.git
    cd Ortho
) else (
    echo [1/3] Ortho already cloned, skipping...
    cd Ortho
)

REM Step 2: Install
echo [2/3] Installing Ortho...
pip install -e . >nul 2>&1

REM Step 3: Ask for repo
echo [3/3] Which repository do you want to scan?
set /p REPO_PATH="Enter path (default: current directory): "
if "!REPO_PATH!"=="" set REPO_PATH=.

REM Step 4: Scan
echo.
echo Scanning !REPO_PATH!...
cd "!REPO_PATH!"
ortho scan

REM Step 5: Setup instructions
echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next: Connect to Claude Code
echo.
echo 1. Open Claude Code (claude.dev or desktop)
echo 2. Go to Settings ^> MCP Servers ^> Add
echo 3. Fill in:
echo    - Name: ortho
echo    - Command: python
echo    - Args: [see below]
echo.

REM Calculate path
for /f "delims=" %%A in ('cd') do set CURRENT_PATH=%%A
cd ..
for /f "delims=" %%A in ('cd') do set PARENT_PATH=%%A
cd %CURRENT_PATH%

echo    Args: %PARENT_PATH%\Ortho\apps\mcp-server\ortho_mcp_server.py
echo.
echo 4. Restart Claude Code
echo 5. Ask Claude: "What violations does my code have?"
echo.
echo For details, see ONBOARD.md
echo.
pause
