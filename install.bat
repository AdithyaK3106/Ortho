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

REM Step 2: Install Python engine
echo [2/4] Installing Ortho (Python engine)...
pip install -e . >nul 2>&1

for /f "delims=" %%A in ('cd') do set ORTHO_DIR=%%A

REM Step 3: Build CLI
echo [3/4] Building Ortho CLI...
cd apps\cli
call npm install >nul 2>&1
call npm run build >nul 2>&1
cd "%ORTHO_DIR%"

if not exist "%ORTHO_DIR%\apps\cli\dist\index.js" (
    echo CLI build failed - check "cd apps\cli && npm install && npm run build" manually
    pause
    exit /b 1
)

REM Step 4: Ask for repo
echo [4/4] Which repository do you want to scan?
set /p REPO_PATH="Enter path (default: current directory): "
if "!REPO_PATH!"=="" set REPO_PATH=.

REM Step 5: Scan
echo.
echo Scanning !REPO_PATH!...
cd "!REPO_PATH!"
node "%ORTHO_DIR%\apps\cli\dist\index.js" scan

REM Step 6: Setup instructions
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
echo    Args: %ORTHO_DIR%\apps\mcp-server\ortho_mcp_server.py
echo.
echo 4. Restart Claude Code
echo 5. Ask Claude: "What violations does my code have?"
echo.
echo For details, see ONBOARD.md
echo.
pause
