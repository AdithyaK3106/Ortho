# Ortho MCP Server — Claude Code Integration

Connect Ortho to Claude Code in **2 minutes**. No auth, no cloud, all local.

---

## What This Does

After setup, Claude Code will have 5 new tools:

- 🛡️ **ortho_guardrails** — Check architecture violations
- 🎯 **ortho_decide** — Change impact + strategy  
- 📋 **ortho_plan** — Feature planning
- ♻️ **ortho_refactor** — Refactoring opportunities
- 🔍 **ortho_memory_search** — Query what you've learned

Claude can call these during conversation:
```
You: "Should I refactor this module?"
→ Claude calls ortho_refactor automatically
→ Claude: "Yes, here are the findings: [bloat analysis]"
```

---

## Installation (2 minutes)

### 1. Install Ortho

```bash
git clone https://github.com/AdithyaK3106/Ortho.git
cd Ortho
pip install -e .
```

### 2. Scan Your Repository

```bash
cd /path/to/your/repo
ortho scan
```

This builds `.ortho/ortho.db` (local knowledge base).

### 3. Configure Claude Code

**Option A: Claude.dev (Web)**

Settings → Add MCP Server → Paste:

```json
{
  "mcpServers": {
    "ortho": {
      "command": "python",
      "args": ["/path/to/Ortho/apps/mcp-server/ortho_mcp_server.py"]
    }
  }
}
```

Replace `/path/to/Ortho` with your actual Ortho directory.

**Option B: Claude Code (Desktop)**

File → Preferences → Settings → Add MCP Server:

```
Name: ortho
Command: python
Args: /path/to/Ortho/apps/mcp-server/ortho_mcp_server.py
```

**Option C: `.claude/claude.dev.json`** (if it exists in your workspace)

```json
{
  "mcpServers": {
    "ortho": {
      "command": "python",
      "args": ["/path/to/Ortho/apps/mcp-server/ortho_mcp_server.py"]
    }
  }
}
```

### 4. Restart Claude Code

Close and reopen Claude Code. Ortho should appear in the Tools panel.

---

## Usage Examples

### Example 1: Check Architecture Before Refactoring

```
You: "I want to split core.py into smaller modules. What violations will this create?"

Claude:
→ Calls ortho_guardrails
→ "Your repo has 2 existing violations. Splitting core.py won't create new ones.
   Here's a safe split plan: [specific recommendation]"
```

### Example 2: Plan a Feature

```
You: "I need to add user authentication. What's the safest approach?"

Claude:
→ Calls ortho_plan
→ "Your repo uses a layered architecture. Here are 3 implementation paths:
   1. Session-based [low effort, low risk]
   2. JWT stateless [medium effort, low risk]
   3. OAuth delegation [low effort, medium risk]"
```

### Example 3: Analyze Change Impact

```
You: "I'm changing src/models/user.py. What will break?"

Claude:
→ Calls ortho_decide with file path
→ "This change will affect 4 modules, 12 tests. Risk: MEDIUM.
   Recommendation: Update models/user.py, then run tests for [list]."
```

### Example 4: Find Refactoring Opportunities

```
You: "What should we refactor first?"

Claude:
→ Calls ortho_refactor
→ "3 opportunities found:
   1. core.py is bloated (3681 lines) — split by feature
   2. models/ ↔ views/ are tightly coupled — extract shared types
   3. Circular dep: models/post.py ↔ models/comment.py — extract types layer"
```

### Example 5: Learn From Past Decisions

```
You: "Have we done anything with guardrails before?"

Claude:
→ Calls ortho_memory_search with "guardrails"
→ "Yes, 5 past guardrails runs found these violations:
   - Layer boundary (core → api): Fixed 3 weeks ago
   - Module sizing (auth.py): Still pending"
```

---

## Troubleshooting

### "ortho_mcp_server.py not found"

Make sure you cloned Ortho and replaced `/path/to/Ortho` with the actual path:

```bash
# Find your Ortho directory
which ortho
# Should show: /path/to/Ortho/...

# Use that path in Claude Code settings
```

### "Ortho module not found"

The MCP server needs the Ortho packages installed:

```bash
cd /path/to/Ortho
pip install -e .
```

### "ortho_guardrails: No violations found"

Good! Your repo is clean. Try:

```bash
ortho memory search "guardrails"  # See past violations
ortho refactor                     # Find refactoring opportunities
```

### "MCP tools don't show up in Claude Code"

1. Restart Claude Code (close all windows)
2. Check settings → MCP Servers → "ortho" is listed
3. Check Python is in your PATH: `python --version`

### "Scan is slow"

Point to a subdirectory instead of the monorepo root:

```
ortho scan /path/to/your-app  # Faster than ortho scan /entire-org
```

---

## What Happens in the Background

1. Claude Code loads `ortho_mcp_server.py`
2. Server imports Ortho's `CliCommands` engine
3. When Claude calls a tool, the server invokes the corresponding method
4. Results come back formatted for Claude to read/synthesize

**No cloud. No auth. All local.**

Every scan result stored in `.ortho/ortho.db` (your repo's hidden directory).

---

## Privacy & Data

- ✅ **Local-first** — all code analysis happens on your machine
- ✅ **No telemetry** — Ortho doesn't phone home
- ✅ **No uploads** — your code never leaves your computer
- ✅ **Encrypted at rest** — `.ortho/ortho.db` is SQLite (you control it)

---

## Next Steps

1. **Set it up** (2 minutes) — follow the Installation steps above
2. **Try it** — ask Claude Code a question that uses Ortho tools
3. **Integrate** — add `ortho scan` to your CI/CD, or git hooks
4. **Share** — tell teammates about Ortho

---

## Questions?

- **How do I update Ortho?** `git pull` in the Ortho directory, then restart Claude Code
- **Can multiple people use the same `.ortho/` database?** Yes, but concurrent writes are not atomic (see roadmap)
- **Does this work with other Claude tools?** Yes! Ortho is just another MCP server; you can add more
- **Can I customize the guardrails?** Coming in Phase 8+ (custom rule definitions)

---

## Advanced: Multiple Repositories

If you work across multiple repos:

```bash
# Each repo gets its own .ortho/ directory
cd /repo/A && ortho scan
cd /repo/B && ortho scan

# In Claude Code, use the ortho_memory_search to see all past work
# across all repos you've scanned
```

---

**That's it. You're ready.**

Ask Claude Code anything about your codebase now — it will call Ortho automatically and give you architecture-aware answers.

