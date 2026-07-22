#!/bin/bash
# Ortho Quick Install — clone + install + scan in one command

set -e

echo "🚀 Ortho Quick Install"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Clone
if [ ! -d "Ortho" ]; then
  echo "📦 Cloning Ortho..."
  git clone https://github.com/AdithyaK3106/Ortho.git
  cd Ortho
else
  echo "📦 Ortho already cloned, skipping..."
  cd Ortho
fi

# Step 2: Install
echo "⚙️  Installing Ortho (Python engine)..."
# Root `pip install -e .` alone does NOT install the 13 workspace packages
# (poetry-core only emits a repo-root .pth, not per-package src links) —
# each package must be installed editable explicitly.
pip install \
  -e . \
  -e shared/storage \
  -e packages/repo-intelligence \
  -e packages/context-hub \
  -e packages/arch-intelligence \
  -e packages/impact-analysis \
  -e packages/change-planner \
  -e packages/feature-planner \
  -e packages/refactoring-advisor \
  -e packages/arch-guardrails \
  -e packages/decision-engine \
  -e packages/cli-commands \
  -e packages/orchestration \
  -e packages/token-optimizer \
  > /dev/null 2>&1

ORTHO_DIR="$(pwd)"

echo "⚙️  Building Ortho CLI..."
(cd apps/cli && npm install > /dev/null 2>&1 && npm run build > /dev/null 2>&1)
ORTHO_BIN="$ORTHO_DIR/apps/cli/dist/index.js"

if [ ! -f "$ORTHO_BIN" ]; then
  echo "✗ CLI build failed — check 'cd apps/cli && npm install && npm run build' manually"
  exit 1
fi

# Step 3: Ask for repo
# `read` here would hang or read garbage under `curl ... | bash` (stdin is
# the piped script, not a terminal) -- only prompt in a real interactive
# terminal, default to the current directory otherwise. Same class of fix
# as install.ps1's Read-Host guard.
echo ""
REPO_PATH="."
if [ -t 0 ]; then
  echo "📁 Which repository do you want to scan?"
  read -p "   Enter path (default: current directory): " REPO_PATH
  REPO_PATH=${REPO_PATH:-.}
fi

# Step 4: Scan
echo "🔍 Scanning $REPO_PATH..."
cd "$REPO_PATH"
node "$ORTHO_BIN" scan > /dev/null

# Step 5: Setup instructions
echo ""
echo "✅ Done! Ortho is ready."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next: Connect to Claude Code"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open Claude Code (claude.dev or desktop app)"
echo "2. Go to Settings → MCP Servers → Add"
echo "3. Paste this:"
echo ""
echo '   Name: ortho'
echo '   Command: python'
echo "   Args: $ORTHO_DIR/apps/mcp-server/ortho_mcp_server.py"
echo ""
echo "4. Restart Claude Code"
echo "5. Ask Claude: 'What violations does my code have?'"
echo ""
echo "See ONBOARD.md for details."
