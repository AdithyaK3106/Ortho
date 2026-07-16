# Ortho — First 5 Minutes

Get engineering intelligence on your repository **right now**. No setup, no config.

## Install (1 minute)

```bash
git clone https://github.com/AdithyaK3106/Ortho.git
cd Ortho

# Python engine (root + all 13 workspace packages)
# Note: `pip install -e packages/*` breaks on non-package dirs — use the script:
./install.sh   # Windows: install.bat

# CLI
cd apps/cli && npm install && npm run build && cd ../..
```

The CLI now exists at `apps/cli/dist/index.js`. Run it directly, or
alias it for convenience:

```bash
alias ortho="node $(pwd)/apps/cli/dist/index.js"
```

The rest of this guide assumes `ortho` resolves via that alias (or
substitute `node apps/cli/dist/index.js` for every `ortho` command below).

## Scan Your Repo (1 minute)

```bash
cd /path/to/your/repo
ortho scan
```

Ortho reads your code, extracts symbols, imports, call graphs, detects architecture.

## Check Architecture Violations (1 minute)

```bash
ortho guardrails
```

**What you get:**
- ✅ Layer boundary violations (if any)
- ✅ Circular dependencies (if any)
- ✅ Module size hotspots
- ✅ Severity filtering: `ortho guardrails --severity error`

Example output:
```
Architecture Violations Found: 3

✗ Layer Boundary Violation: models/user.py imports from views/dashboard.py
  Severity: error
  Fix: Move shared logic to shared/ layer

✗ Circular Dependency: models/post.py ↔ models/comment.py
  Severity: warning
  Fix: Extract common types to models/types.py
```

## Plan a Feature (2 minutes)

Tell Ortho what you want to build:

```bash
ortho plan "add user authentication"
```

**What you get:**
- 📋 Classified intent (new feature, enhancement, bug fix, etc.)
- 🛣️ Implementation paths (3+ options ranked)
- ⚠️ Architecture risks (what could break)
- 📍 Recommended entry point (where to start)

Example output:
```
Feature: Add User Authentication

Recommended Path: Session-based with middleware
  1. Create auth/ layer with SessionManager
  2. Add middleware to views/auth.py
  3. Update models/user.py with password_hash
  Estimated effort: 2–3 days

Alternative Paths:
  • JWT-based stateless (2–4 days, better for mobile)
  • OAuth2 delegation (1–2 days, requires provider setup)
```

## Decide Before Changing a File (2 minutes)

Point Ortho at a file you're about to edit:

```bash
ortho decide src/models/user.py
```

**What you get:**
- 💥 Blast radius (what changes will break)
- 🔗 Affected files (imports, call sites, dependents)
- ⚠️ Guardrail risks (layer violations, cycles)
- ✅ Confidence score (how sure is Ortho)

Example output:
```
Change Impact: src/models/user.py

Affected (Direct):
  • src/views/auth.py (imports User class)
  • src/models/post.py (references User.id)

Affected (Indirect):
  • tests/test_auth.py (17 tests use User)
  • src/api/routes.py (serializes User)

Risk Assessment:
  Guardrails: OK (no layer violations)
  Complexity: MEDIUM (affects 4 modules)
  
Confidence: HIGH (0.92)
```

## Refactor with Confidence (2 minutes)

Get real bloat, coupling, and cycle findings:

```bash
ortho refactor
```

**What you get:**
- 📦 Bloated modules (>500 lines, consider splitting)
- 🔗 Tight coupling hotspots (high internal coupling)
- 🔄 Circular dependencies (break cycles first)

Example output:
```
Refactoring Recommendations

BLOATED MODULES (>500 lines):
  • src/utils/helpers.py: 823 lines
    Split into: validators/, formatters/, converters/

TIGHT COUPLING:
  • src/models/ ↔ src/views/ (17 cross-layer edges)
    Fix: Extract domain/ layer for shared types

CIRCULAR DEPENDENCIES:
  • models/post.py ↔ models/comment.py
    Break: Extract models/types.py for shared types
```

## Query What You've Learned (0 minutes)

Every command stores what it found. Search it later:

```bash
ortho memory search "layer_boundaries"
```

See all past guardrails violations (when they happened, what they were, how they changed).

```bash
ortho memory search "high confidence"
```

See all high-confidence decisions you made (for retrospective analysis).

---

## What's Happening Behind the Scenes?

1. **Scan** parses Python AST, extracts symbols, imports, calls
2. **Guardrails** checks layer boundaries, circular deps, module size
3. **Plan** classifies intent → returns ≥3 implementation paths
4. **Decide** computes blast radius from change-impact analysis
5. **Refactor** finds real bloat, coupling, cycles
6. **Memory** stores every run for future reference

No AI. No LLM calls. Pure code analysis. Fast. Local. Yours to keep.

---

## Next Steps

- **Integrate with CI/CD**: `ortho guardrails --severity error` fails the build
- **Pre-commit hook**: Auto-check violations before you commit
- **IDE extension** (coming soon): Inline layer-boundary violations in VSCode
- **MCP Server** (coming soon): Use Ortho in Claude Code for safer AI coding

---

## Need Help?

- **Stuck?** Run `ortho --help` for all commands
- **Curious?** Check `README.md` for architecture details
- **Contributing?** See `CLAUDE.md` for the ASES methodology

---

**That's it.** You now have engineering intelligence on your codebase. Use it before your next refactor, feature, or architectural change.

Happy coding. 🚀
