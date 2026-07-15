# Testing Ortho MCP Server Locally

Verify that the MCP server and all 5 tools work before deploying to Claude Code.

---

## Quick Test (2 minutes)

```bash
cd /path/to/ortho
python -m pytest apps/mcp-server/test_mcp_server.py -v
```

Expected output:
```
23 passed in 15s
```

All 5 tools are production-ready if tests pass.

---

## What's Being Tested

### Tool: ortho_guardrails
- ✓ Basic call succeeds
- ✓ Severity filtering (error, warning)
- ✓ Nonexistent paths handled gracefully
- ✓ Structured violations field populated

### Tool: ortho_decide
- ✓ Text intent succeeds
- ✓ File paths trigger change-impact analysis
- ✓ Empty intents rejected
- ✓ Confidence filtering (0.0–1.0)
- ✓ Structured recommendations field populated

### Tool: ortho_plan
- ✓ Intent classification works
- ✓ Returns 3+ implementation paths
- ✓ Empty intents rejected
- ✓ Various intents (auth, logging, performance) work

### Tool: ortho_refactor
- ✓ Bloat/coupling/cycle detection works
- ✓ Nonexistent paths handled
- ✓ Clean repos return valid output

### Tool: ortho_memory_search
- ✓ Keyword matching works
- ✓ Empty queries handled
- ✓ Nonexistent repos handled
- ✓ Structured results field populated

### Integration Tests
- ✓ All 5 tools work in sequence (no interference)
- ✓ Error paths never raise (always return success=True/False)
- ✓ Structured fields exist on all reports

---

## Manual Test (5 minutes)

Run the MCP server locally and test a tool call:

```bash
# 1. Start the MCP server (in one terminal)
cd /path/to/ortho
python apps/mcp-server/ortho_mcp_server.py

# 2. Call a tool (in another terminal)
python << 'EOF'
import sys
from pathlib import Path

# Add packages to path
_PROJECT_ROOT = Path.cwd()
for _p in (
    _PROJECT_ROOT / 'shared' / 'storage' / 'src',
    _PROJECT_ROOT / 'packages' / 'cli-commands' / 'src',
    _PROJECT_ROOT / 'packages' / 'repo-intelligence' / 'src',
    _PROJECT_ROOT / 'packages' / 'context-hub' / 'src',
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from cli_commands.commands import CliCommands

commands = CliCommands()
repo = str(Path.cwd() / 'repos' / 'click' / 'src' / 'click')

# Test guardrails
report = commands.guardrails(repo)
print(f"Guardrails: {report.success}")
print(f"Violations: {len(report.violations) if report.violations else 0}")

# Test plan
report = commands.plan("add caching", scan_path=repo)
print(f"Plan: {report.success}")
print(f"Content: {report.content[:100]}...")
EOF
```

Expected output:
```
Guardrails: True
Violations: [count]
Plan: True
Content: Feature type: ...
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'cli_commands'"

Make sure you ran `pip install -e .` from the Ortho root:

```bash
cd /path/to/ortho
pip install -e .
pytest apps/mcp-server/test_mcp_server.py -v
```

### "AssertionError: Test repository not found"

The test fixture looks for `repos/click/src/click`. If you don't have it:

```bash
cd /path/to/ortho
# Clone the test repo
git clone https://github.com/pallets/click.git repos/click

# Or skip tests that need it:
pytest apps/mcp-server/test_mcp_server.py::TestOrthoMCPServer::test_error_handling -v
```

### "Test passed but MCP server won't start"

The MCP SDK (`mcp` package) isn't installed yet. This is expected — the test suite doesn't require it. When you integrate with Claude Code, you'll install it:

```bash
pip install mcp
python apps/mcp-server/ortho_mcp_server.py  # Should start now
```

---

## Next: Claude Code Integration

Once tests pass:

1. Install the MCP SDK: `pip install mcp`
2. Follow `MCP_SETUP.md` to configure Claude Code
3. Test in Claude Code with a real conversation

---

## Test Files

- `apps/mcp-server/test_mcp_server.py` — 23 tests covering all 5 tools
- `apps/mcp-server/ortho_mcp_server.py` — the MCP server itself

---

**All tests passing = MCP server is ready for pilot users.**

