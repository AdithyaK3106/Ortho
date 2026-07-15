# Ortho Integration Guide — All Tools

Quick reference for integrating Ortho with popular AI coding tools and CI/CD systems.

---

## 1. Claude Code (MCP Server) ⭐ **START HERE**

### Status
- Engine: ✅ Complete (all 5 tools real and tested)
- MCP Spec: ✅ Complete (see `docs/mcp-server-contract.md`)
- Server Implementation: 🚧 Needs to be built

### How It Works
Claude Code calls Ortho MCP tools directly mid-conversation. No manual copying/pasting.

### Setup (Developer)

```bash
# 1. Install Ortho
pip install -e .

# 2. Scan your repo
cd /path/to/repo
ortho scan

# 3. Configure Claude Code to use MCP server
# (Settings → Add MCP Server → Select "ortho" → Choose workspace root)

# 4. Use in conversation
# Claude: [calls ortho_guardrails automatically]
# Claude: "Here are the architecture violations. Should I fix them first?"
```

### Available Tools (Exposed via MCP)
- `ortho_guardrails(path: str)` → Check violations
- `ortho_decide(intent: str, scan_path: str)` → Change impact + strategy
- `ortho_plan(intent: str, scan_path: str)` → Feature planning
- `ortho_refactor(path: str)` → Refactoring opportunities
- `ortho_memory_search(query: str)` → Searchable knowledge base

### Build MCP Server
See `docs/mcp-server-contract.md` for exact schemas and implementation guide.

---

## 2. GitHub Copilot (VSCode Extension) 🚧

### Status
- Engine: ✅ Complete
- VSCode Extension: 🚧 Not yet built

### How It Works
Inline violations as you type. Red squiggles on forbidden imports, layer violations.

### Planned Setup

```bash
# 1. Install Ortho extension in VSCode
# (From VSCode Extensions: search "Ortho")

# 2. Configure workspace
# .vscode/settings.json:
{
  "ortho.scanPath": "/path/to/repo",
  "ortho.severityFilter": "error",
  "ortho.autoScan": true
}

# 3. VSCode shows violations inline
# src/api/routes.py:42: ⚠️ Forbidden import (API ← Data)
```

### Roadmap
- Phase 7.2: First version (layer violations only)
- Phase 7.3: Full integration (quick fixes, refactoring)

---

## 3. Pre-commit Hook (Git) ✅ **Works Today**

### Status
- Engine: ✅ Complete
- Hook Template: Ready to use

### How It Works
Blocks commits if architecture violations exceed threshold.

### Setup

```bash
# 1. Install Ortho
pip install -e .

# 2. Scan repo once
ortho scan

# 3. Create .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**File: `.git/hooks/pre-commit`**
```bash
#!/bin/bash
set -e

# Run Ortho guardrails, fail on errors
ortho guardrails --severity error

if [ $? -ne 0 ]; then
  echo "✗ Fix architecture violations before committing"
  exit 1
fi

# Optional: warnings are OK, errors block
# ortho guardrails --severity error || exit 1

echo "✓ Architecture check passed"
exit 0
```

**Or use husky (npm projects):**
```bash
npm install husky --save-dev
npx husky install
npx husky add .husky/pre-commit "ortho guardrails --severity error"
```

### Developer Experience
```bash
$ git commit -m "Refactor: split core.py"
→ Ortho runs automatically
→ If violations: commit blocked, fix, retry
→ If clean: commit succeeds
```

---

## 4. GitHub Actions CI/CD ✅ **Works Today**

### Status
- Engine: ✅ Complete
- Action Template: Ready to use

### How It Works
Runs Ortho on every push/PR, fails CI if violations.

### Setup

**File: `.github/workflows/ortho-check.yml`**
```yaml
name: Ortho Architecture Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  ortho-guardrails:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Ortho
        run: pip install -e .
      
      - name: Scan repository
        run: ortho scan
      
      - name: Check architecture violations
        run: ortho guardrails --severity error
      
      - name: Report findings (if failed)
        if: failure()
        run: ortho guardrails > /tmp/ortho-report.txt && echo "See report below:" && cat /tmp/ortho-report.txt
```

### Developer Experience
```bash
$ git push
→ GitHub Actions triggers
→ Ortho scans automatically
→ If violations: PR check fails, fix, push again
→ If clean: PR check passes
```

---

## 5. GitLab CI ✅ **Works Today**

### How It Works
Similar to GitHub Actions, runs on every push/MR.

**File: `.gitlab-ci.yml`**
```yaml
stages:
  - check

ortho-guardrails:
  stage: check
  image: python:3.11
  script:
    - pip install -e .
    - ortho scan
    - ortho guardrails --severity error
  only:
    - merge_requests
    - main
    - develop
```

---

## 6. Jenkins ✅ **Works Today**

### How It Works
Runs as a Jenkins pipeline stage.

**File: `Jenkinsfile`**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'python -m venv venv'
                sh 'source venv/bin/activate && pip install -e .'
            }
        }
        
        stage('Ortho Check') {
            steps {
                sh 'source venv/bin/activate && ortho scan'
                sh 'source venv/bin/activate && ortho guardrails --severity error'
            }
        }
    }
    
    post {
        failure {
            sh 'source venv/bin/activate && ortho guardrails | tee ortho-report.txt'
        }
    }
}
```

---

## 7. Local Development (Manual) ✅ **Works Today**

### How It Works
Developers run Ortho manually, integrate findings into their workflow.

### Setup
```bash
# One-time
cd /path/to/repo
pip install -e /path/to/ortho
ortho scan

# Before each feature
ortho guardrails                           # What's wrong now?
ortho plan "add user authentication"       # What should I build?
ortho decide src/models/user.py            # What will break?

# After refactoring
ortho refactor                             # What needs attention?

# Review history
ortho memory search "layer_boundaries"     # What violations did I fix?
ortho memory search "high confidence"      # What decisions did I make?
```

---

## 8. JetBrains IDE (IntelliJ, PyCharm) 🚧

### Status
- Engine: ✅ Complete
- Plugin: 🚧 Planned for Phase 7.3+

### Planned Setup
```
IntelliJ → Preferences → Plugins → Install "Ortho"
→ Configure workspace → Set scan path
→ Violations show as gutter warnings
```

---

## 9. Slack Integration (Team Notifications) 🚧

### Planned Features
- Daily summary: "3 new violations, 1 bloat hotspot"
- PR checks: "@channel: Architecture review failed on #1234"
- Memory highlights: "Top 5 things we learned this week"

### Planned Setup
```bash
ortho scan
ortho guardrails | slack-notify \
  --channel "#architecture" \
  --mention "@team"
```

---

## Comparison Table

| Integration | Status | Setup Time | Real-time | Automation |
|------------|--------|-----------|-----------|-----------|
| CLI (manual) | ✅ | 5 min | Yes | Manual |
| Pre-commit hook | ✅ | 5 min | Yes | Auto on commit |
| GitHub Actions | ✅ | 10 min | No | Auto on push/PR |
| GitLab CI | ✅ | 10 min | No | Auto on push/MR |
| Jenkins | ✅ | 15 min | No | Auto on trigger |
| Claude Code (MCP) | 🚧 | 10 min | Yes | Auto in chat |
| VSCode Extension | 🚧 | 5 min | Yes | Auto on type |
| JetBrains Plugin | 🚧 | 5 min | Yes | Auto on type |
| Slack | 🚧 | 15 min | No | Auto on scan |

---

## Quick Start (TL;DR)

### For Individual Developers
```bash
pip install -e .
cd /path/to/repo
ortho scan
ortho guardrails
# Now use with Claude Code (when MCP available)
```

### For Teams
```bash
# Add to .github/workflows/ortho-check.yml (above)
# Commit & push
# PRs now have architecture checks
```

### For Enterprises
```bash
# Deploy: .github/workflows/ + .git/hooks/pre-commit
# Monitor: ortho memory search across all repos
# Enforce: custom rules (Phase 8+)
```

---

## Troubleshooting

### "Ortho scan is too slow"
- Reduce scope: point to a subdirectory, not entire monorepo
- Use `--exclude` flag (coming in Phase 7.2+)

### "Too many false positives"
- Check `ortho guardrails --severity error` (filter to errors only)
- Review `docs/architecture/adr-015-layer-boundaries.md` for what's a real violation

### "I want custom rules"
- Coming in Phase 8+ (custom guardrail definitions)
- For now: contribute your pattern to core rules (GitHub issues)

### "Can't access `.ortho/` from CI/CD"
- Ensure write permissions in CI environment
- Check disk space (large repos generate ~50MB databases)

---

## Support

- **Issues:** GitHub issues with `[integration]` tag
- **Discussions:** GitHub discussions for design questions
- **Docs:** This guide + `QUICKSTART.md` + `PRODUCT_POSITIONING.md`

