# Ortho Quick Install for Windows (PowerShell) — clone + install + build in one command.
# Usage:  irm https://adithyak3106.github.io/Ortho-community/install.ps1 | iex
#
# Mirrors install.sh/install.bat exactly (same 13 editable-install package
# list, same clone-if-missing behavior) -- kept as a third copy rather than
# calling install.bat from PowerShell so a `curl | iex` one-liner doesn't
# need a second network hop or a temp .bat file on disk.

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "OK $msg" -ForegroundColor Green }
function Write-Fail($msg) {
    Write-Host "FAILED: $msg" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Ortho Quick Install" -ForegroundColor Magenta
Write-Host "===================================="

# Prereq check: fail fast with an actionable message instead of a confusing
# mid-script error several minutes into a clone+pip-install+npm-build.
$missing = @()
foreach ($cmd in @("git", "python", "pip", "node", "npm")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { $missing += $cmd }
}
if ($missing.Count -gt 0) {
    Write-Fail "Missing required tool(s): $($missing -join ', '). Install them first, then re-run this script."
}

Write-Step "Cloning Ortho..."
if (-not (Test-Path "Ortho")) {
    git clone https://github.com/AdithyaK3106/Ortho.git
    if ($LASTEXITCODE -ne 0) { Write-Fail "git clone failed" }
} else {
    Write-Host "Ortho already cloned, skipping..."
}
Set-Location Ortho

Write-Step "Installing Ortho (Python engine)..."
# Root `pip install -e .` alone does NOT install the 13 workspace packages
# (poetry-core only emits a repo-root .pth, not per-package src links) --
# each package must be installed editable explicitly. Keep this list in
# sync with install.sh/install.bat.
#
# Do NOT redirect pip's stderr here (e.g. `*> $null` or `2>&1`): in
# Windows PowerShell 5.1, redirecting a native command's stderr wraps each
# line in a NativeCommandError and sets $? to $false even when pip's real
# exit code is 0 -- pip's own harmless warnings (e.g. "Ignoring invalid
# distribution ~ympy" from an unrelated leftover site-packages entry) would
# then look like a fatal install failure and abort the whole script.
pip install -e . `
    -e shared/storage `
    -e packages/repo-intelligence `
    -e packages/context-hub `
    -e packages/arch-intelligence `
    -e packages/impact-analysis `
    -e packages/change-planner `
    -e packages/feature-planner `
    -e packages/refactoring-advisor `
    -e packages/arch-guardrails `
    -e packages/decision-engine `
    -e packages/cli-commands `
    -e packages/orchestration `
    -e packages/token-optimizer
if ($LASTEXITCODE -ne 0) { Write-Fail "pip install failed -- see the output above for the real error" }

$OrthoDir = (Get-Location).Path

Write-Step "Building Ortho CLI..."
Push-Location apps/cli
# Same PowerShell 5.1 stderr-redirection trap as pip above: npm writes
# routine notices to stderr, so no redirection here either -- rely on
# $LASTEXITCODE, and on the dist/index.js existence check below, not on
# whether output was captured.
npm install
if ($LASTEXITCODE -ne 0) { Write-Fail "npm install failed -- see the output above for the real error" }
npm run build
Pop-Location

$OrthoBin = Join-Path $OrthoDir "apps/cli/dist/index.js"
if (-not (Test-Path $OrthoBin)) {
    Write-Fail "CLI build failed -- check 'cd apps/cli; npm install; npm run build' manually"
}

Write-Ok "Ortho installed."

Write-Host ""
# Read-Host throws in a non-interactive session (CI, a piped/background
# invocation, some `irm ... | iex` contexts) instead of just returning
# empty -- fall back to the default instead of crashing after a fully
# successful install.
$RepoPath = "."
if ([Environment]::UserInteractive) {
    try {
        $input = Read-Host "Which repository do you want to scan? (default: current directory)"
        if (-not [string]::IsNullOrWhiteSpace($input)) { $RepoPath = $input }
    } catch {
        # Non-interactive session slipped through the UserInteractive check
        # (observed in practice) -- keep the default rather than fail here.
    }
}

Write-Step "Scanning $RepoPath..."
Push-Location $RepoPath
node $OrthoBin scan | Out-Null
Pop-Location

Write-Host ""
Write-Host "Done! Ortho is ready." -ForegroundColor Green
Write-Host "===================================="
Write-Host "Next: Connect to Claude Code"
Write-Host "===================================="
Write-Host ""
Write-Host "1. Open Claude Code (claude.dev or desktop app)"
Write-Host "2. Go to Settings -> MCP Servers -> Add"
Write-Host "3. Paste this:"
Write-Host ""
Write-Host "   Name: ortho"
Write-Host "   Command: python"
Write-Host "   Args: $OrthoDir/apps/mcp-server/ortho_mcp_server.py"
Write-Host ""
Write-Host "4. Restart Claude Code"
Write-Host "5. Ask Claude: 'What violations does my code have?'"
Write-Host ""
Write-Host "See ONBOARD.md for details."
