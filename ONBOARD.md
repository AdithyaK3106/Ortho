# Ortho — Start in 2 Minutes

Copy-paste these 4 commands. You'll have real architecture intelligence in your Claude Code.

---

## Step 1: Install (1 minute)

```bash
git clone https://github.com/AdithyaK3106/Ortho.git
cd Ortho

# Python engine (analysis, MCP server)
pip install -e .

# CLI (the `ortho` command itself)
cd apps/cli
npm install
npm run build
cd ../..
```

Done. There's no global install step — you run the CLI directly from
where you built it:

```bash
node apps/cli/dist/index.js --help
```

**Tip:** save yourself typing by aliasing it (add to `~/.bashrc` or
`~/.zshrc`, adjusting the path to where you cloned Ortho):

```bash
alias ortho="node /path/to/Ortho/apps/cli/dist/index.js"
```

The rest of this guide uses `ortho` — substitute the full
`node apps/cli/dist/index.js` form (or your alias) if you skipped that.

---

## Step 2: Scan Your Repo (30 seconds)

```bash
cd /path/to/your/code
ortho scan
```

Ortho learns your codebase. Done.

---

## Step 3: Connect Claude Code (1 minute)

**Claude.dev (Web):**
1. Open Settings (gear icon)
2. Click "Add MCP Server"
3. Paste this:
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
4. Replace `/path/to/Ortho` with your Ortho directory
5. Restart Claude Code

**Claude Code (Desktop):**
1. File → Preferences → Settings
2. Find "MCP Servers" → Add
3. Name: `ortho`
4. Command: `python`
5. Args: `/path/to/Ortho/apps/mcp-server/ortho_mcp_server.py`
6. Restart

Done. Ortho tools appear in Claude Code.

---

## Step 4: Try It (30 seconds)

Open Claude Code chat. Type:

```
I'm going to refactor my core module. What violations will this create?
```

Claude automatically calls `ortho_guardrails`. You get real violations instantly.

Or ask:

```
How should I add caching to this API?
```

Claude calls `ortho_plan`. You get implementation paths ranked by effort/risk.

Or:

```
What will break if I change src/models/user.py?
```

Claude calls `ortho_decide`. You get exact blast radius.

---

## That's It

You now have:
✅ Architecture violations checked  
✅ Change impact analyzed  
✅ Features planned  
✅ Refactoring opportunities found  
✅ Knowledge base (searchable by keyword)  

All in Claude Code. All local. Free forever.

---

## Didn't Work?

**"ModuleNotFoundError: No module named 'cli_commands'"**
→ Did you run `pip install -e .` from the Ortho directory? Re-run it.

**"MCP tools don't show up in Claude Code"**
→ Restart Claude Code completely (close all windows). Check the MCP config in settings.

**"Python not found"**
→ Use full path: `/usr/bin/python3` or `C:\Python312\python.exe` (Windows)

**"Ortho scan is slow"**
→ Point to a subdirectory: `ortho scan src/` instead of entire repo.

---

## What's Next?

- **Share with teammates** — send them this doc, they follow the 4 steps
- **Add to CI/CD** — catch violations before merge (see `INTEGRATION_GUIDE.md`)
- **Use memory search** — ask "What violations did we fix last week?"
- **Pre-commit hooks** — auto-check before you commit

---

## Questions?

See:
- `QUICKSTART.md` — more features (plan, decide, refactor, memory)
- `MCP_SETUP.md` — detailed setup with examples
- `PRODUCT_POSITIONING.md` — why this matters
- `INTEGRATION_GUIDE.md` — CI/CD, pre-commit, GitHub Actions

---

**You're done. Start using Ortho now.**
