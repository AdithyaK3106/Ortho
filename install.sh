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
echo "⚙️  Installing Ortho..."
pip install -e . > /dev/null 2>&1

# Step 3: Ask for repo
echo ""
echo "📁 Which repository do you want to scan?"
read -p "   Enter path (default: current directory): " REPO_PATH
REPO_PATH=${REPO_PATH:-.}

# Step 4: Scan
echo "🔍 Scanning $REPO_PATH..."
cd "$REPO_PATH"
ortho scan > /dev/null

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
ORTHO_PATH=$(cd "$(dirname "$(pwd)")"; pwd)/Ortho/apps/mcp-server/ortho_mcp_server.py
echo "   Args: $ORTHO_PATH"
echo ""
echo "4. Restart Claude Code"
echo "5. Ask Claude: 'What violations does my code have?'"
echo ""
echo "See ONBOARD.md for details."
