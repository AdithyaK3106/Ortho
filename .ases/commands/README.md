# Verification Commands

Executable shell scripts for capturing build, lint, type-check, and test evidence.

## Scripts

### `verify-ts.sh` — TypeScript Verification

Runs type checking, linting, unit tests, and regression tests for TypeScript projects (Ortho).

```bash
./verify-ts.sh task-001 .ases/evidence/task-001
```

**Produces:**
- `types-[timestamp].log` — tsc output
- `lint-[timestamp].log` — eslint output (JSON format)
- `test-[timestamp].log` — jest output + jest-report-[timestamp].json
- `regression-[timestamp].log` — full test suite
- `build-[timestamp].log` — summary

**Requirements:** Node.js, npm, tsc, eslint, jest

---

### `verify-python.sh` — Python Verification

Runs linting, type checking, unit tests, and regression tests for Python projects (Ortho variant).

```bash
./verify-python.sh task-001 .ases/evidence/task-001
```

**Produces:**
- `lint-[timestamp].log` — ruff output
- `types-[timestamp].log` — mypy output
- `test-[timestamp].log` — pytest output with coverage
- `regression-[timestamp].log` — full test suite
- `build-[timestamp].log` — summary

**Requirements:** Python, ruff, mypy, pytest

---

### `verify-android.sh` — Kotlin/Java Verification

Runs linting, building, and unit tests for Kotlin/Java projects (Expense App).

```bash
./verify-android.sh task-001 .ases/evidence/task-001
```

**Produces:**
- `lint-[timestamp].log` — ktlintCheck output
- `build-[timestamp].log` — gradle build output
- `test-[timestamp].log` — gradle test output
- `ui-tests-[timestamp].log` — note on manual UI testing requirement

**Requirements:** Gradle, ./gradlew (Android SDK)

**Note:** UI tests require an Android emulator and are marked MANUAL-REQUIRED.

---

### `capture-evidence.sh` — Master Router

Routes verification to the appropriate stack based on task type.

```bash
# TypeScript
./capture-evidence.sh task-001 typescript .ases/evidence/task-001

# Python
./capture-evidence.sh task-001 python .ases/evidence/task-001

# Android/Kotlin
./capture-evidence.sh task-001 android .ases/evidence/task-001

# All stacks
./capture-evidence.sh task-001 all .ases/evidence/task-001
```

**Usage:**
```
./capture-evidence.sh <task-id> <stack> [output-dir]

task-id:    unique identifier (e.g., task-001, task-feature-auth)
stack:      typescript | python | android | all
output-dir: path to store logs (default: .ases/evidence/<task-id>)
```

---

## Output Structure

Each verification creates timestamped log files in the output directory:

```
.ases/evidence/
└── task-001/
    ├── build-20260627_143022.log        ← Overall summary
    ├── types-20260627_143022.log        ← Type checking
    ├── lint-20260627_143022.log         ← Linting
    ├── test-20260627_143022.log         ← Unit tests + coverage
    ├── regression-20260627_143022.log   ← Full regression suite
    ├── jest-report-20260627_143022.json ← Jest JSON report (TS only)
    └── ui-tests-20260627_143022.log     ← Manual UI notes (Android only)
```

---

## Making Scripts Executable

After cloning or creating scripts:

```bash
chmod +x .ases/commands/verify-ts.sh
chmod +x .ases/commands/verify-python.sh
chmod +x .ases/commands/verify-android.sh
chmod +x .ases/commands/capture-evidence.sh
```

Or batch:
```bash
chmod +x .ases/commands/*.sh
```

---

## Integration with VERIFIER Agent

The VERIFIER agent:
1. Reads the task spec
2. Chooses appropriate stack (typescript, python, android)
3. Runs: `./capture-evidence.sh <task-id> <stack>`
4. Reads all generated log files (exact quotes into verification-report.md)
5. Produces evidence-package.md with gate sign-off

**Rule:** VERIFIER never fabricates logs. If a script fails or a tool is missing, the log reflects that. VERIFIER documents the limitation honestly.

---

## Known Limitations

| Stack | Limitation | Workaround |
|-------|-----------|-----------|
| TypeScript | Requires npm packages installed | Run `npm install` first |
| Python | Requires Python packages installed | Run `pip install -r requirements.txt` first |
| Android | UI tests require emulator | Mark as MANUAL-REQUIRED in verification-report |
| All | Tools must be in PATH | Use full paths or add to $PATH |

---

## Examples

### Example 1: Verify a TypeScript task

```bash
cd /path/to/project
.ases/commands/capture-evidence.sh task-001 typescript
# Logs saved to .ases/evidence/task-001/
```

### Example 2: Run all stacks for a feature

```bash
.ases/commands/capture-evidence.sh feature-auth all
# Runs TypeScript, Python, and Android verification
# Logs in .ases/evidence/feature-auth/
```

### Example 3: Verify with custom output directory

```bash
.ases/commands/capture-evidence.sh task-backend typescript /tmp/evidence/backend
# Logs saved to /tmp/evidence/backend/
```

---

*End of README.md*
