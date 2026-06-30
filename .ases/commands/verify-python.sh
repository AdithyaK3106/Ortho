#!/bin/bash
# verify-python.sh — Python verification (lint, types, tests, coverage)
# Usage: ./verify-python.sh [task-id] [output-dir]
# Example: ./verify-python.sh task-001 .ases/evidence/task-001

set -e

TASK_ID="${1:-unknown}"
OUTPUT_DIR="${2:-.ases/evidence/$TASK_ID}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=== Python Verification for $TASK_ID ===" | tee "$OUTPUT_DIR/build-$TIMESTAMP.log"

# 1. Linting (ruff)
echo ""
echo "--- Linting (ruff) ---" | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log"
if command -v ruff &> /dev/null; then
  ruff check . 2>&1 | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log" || echo "LINT_FAILED"
else
  echo "ruff not found (ruff not installed)" | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log"
fi

# 2. Type checking (mypy)
echo ""
echo "--- Type Checking (mypy) ---" | tee -a "$OUTPUT_DIR/types-$TIMESTAMP.log"
if command -v mypy &> /dev/null; then
  mypy . --strict 2>&1 | tee -a "$OUTPUT_DIR/types-$TIMESTAMP.log" || echo "TYPE_CHECK_FAILED"
else
  echo "mypy not found (mypy not installed)" | tee -a "$OUTPUT_DIR/types-$TIMESTAMP.log"
fi

# 3. Unit Tests + Coverage (pytest)
echo ""
echo "--- Unit Tests & Coverage (pytest) ---" | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log"
if command -v pytest &> /dev/null; then
  pytest --tb=short --cov=. --cov-report=term-missing 2>&1 | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log" || echo "TEST_FAILED"
else
  echo "pytest not found (pytest not installed)" | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log"
fi

# 4. Regression Tests
echo ""
echo "--- Regression Tests ---" | tee -a "$OUTPUT_DIR/regression-$TIMESTAMP.log"
if command -v pytest &> /dev/null; then
  pytest 2>&1 | tee -a "$OUTPUT_DIR/regression-$TIMESTAMP.log" || echo "REGRESSION_FAILED"
else
  echo "pytest not found (cannot run regression tests)" | tee -a "$OUTPUT_DIR/regression-$TIMESTAMP.log"
fi

echo ""
echo "=== Verification Complete ===" | tee -a "$OUTPUT_DIR/build-$TIMESTAMP.log"
echo "Evidence saved to: $OUTPUT_DIR"
