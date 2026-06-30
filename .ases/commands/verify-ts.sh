#!/bin/bash
# verify-ts.sh — TypeScript verification (build, lint, types, tests, coverage)
# Usage: ./verify-ts.sh [task-id] [output-dir]
# Example: ./verify-ts.sh task-001 .ases/evidence/task-001

set -e

TASK_ID="${1:-unknown}"
OUTPUT_DIR="${2:-.ases/evidence/$TASK_ID}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=== TypeScript Verification for $TASK_ID ===" | tee "$OUTPUT_DIR/build-$TIMESTAMP.log"

# 1. Type checking (tsc)
echo ""
echo "--- Type Checking (tsc) ---" | tee -a "$OUTPUT_DIR/types-$TIMESTAMP.log"
if command -v tsc &> /dev/null; then
  tsc --noEmit 2>&1 | tee -a "$OUTPUT_DIR/types-$TIMESTAMP.log" || echo "TYPE_CHECK_FAILED"
else
  echo "tsc not found (TypeScript not installed)" | tee -a "$OUTPUT_DIR/types-$TIMESTAMP.log"
fi

# 2. Linting (eslint)
echo ""
echo "--- Linting (eslint) ---" | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log"
if command -v eslint &> /dev/null; then
  eslint . --ext .ts,.tsx --format json 2>&1 | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log" || echo "LINT_FAILED"
else
  echo "eslint not found (ESLint not installed)" | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log"
fi

# 3. Unit Tests + Coverage (jest)
echo ""
echo "--- Unit Tests & Coverage (jest) ---" | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log"
if command -v jest &> /dev/null; then
  jest --coverage --ci --json --outputFile="$OUTPUT_DIR/jest-report-$TIMESTAMP.json" 2>&1 | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log" || echo "TEST_FAILED"
else
  echo "jest not found (Jest not installed)" | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log"
fi

# 4. Regression Tests
echo ""
echo "--- Regression Tests ---" | tee -a "$OUTPUT_DIR/regression-$TIMESTAMP.log"
if command -v jest &> /dev/null; then
  jest --testPathPattern=".*" 2>&1 | tee -a "$OUTPUT_DIR/regression-$TIMESTAMP.log" || echo "REGRESSION_FAILED"
else
  echo "jest not found (cannot run regression tests)" | tee -a "$OUTPUT_DIR/regression-$TIMESTAMP.log"
fi

echo ""
echo "=== Verification Complete ===" | tee -a "$OUTPUT_DIR/build-$TIMESTAMP.log"
echo "Evidence saved to: $OUTPUT_DIR"
