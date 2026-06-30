#!/bin/bash
# verify-android.sh — Kotlin/Java verification (build, lint, unit tests)
# Usage: ./verify-android.sh [task-id] [output-dir]
# Example: ./verify-android.sh task-001 .ases/evidence/task-001

set -e

TASK_ID="${1:-unknown}"
OUTPUT_DIR="${2:-.ases/evidence/$TASK_ID}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=== Android/Kotlin Verification for $TASK_ID ===" | tee "$OUTPUT_DIR/build-$TIMESTAMP.log"

# 1. Linting (ktlint via gradle)
echo ""
echo "--- Linting (ktlintCheck) ---" | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log"
if command -v ./gradlew &> /dev/null || [ -f "./gradlew" ]; then
  ./gradlew ktlintCheck 2>&1 | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log" || echo "LINT_FAILED"
else
  echo "gradlew not found (Gradle not configured)" | tee -a "$OUTPUT_DIR/lint-$TIMESTAMP.log"
fi

# 2. Build (gradle build)
echo ""
echo "--- Building (gradle build) ---" | tee -a "$OUTPUT_DIR/build-$TIMESTAMP.log"
if command -v ./gradlew &> /dev/null || [ -f "./gradlew" ]; then
  ./gradlew build 2>&1 | tee -a "$OUTPUT_DIR/build-$TIMESTAMP.log" || echo "BUILD_FAILED"
else
  echo "gradlew not found (Gradle not configured)" | tee -a "$OUTPUT_DIR/build-$TIMESTAMP.log"
fi

# 3. Unit Tests
echo ""
echo "--- Unit Tests (gradle test) ---" | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log"
if command -v ./gradlew &> /dev/null || [ -f "./gradlew" ]; then
  ./gradlew test 2>&1 | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log" || echo "TEST_FAILED"
else
  echo "gradlew not found (cannot run tests)" | tee -a "$OUTPUT_DIR/test-$TIMESTAMP.log"
fi

# 4. Note: UI tests require emulator (manual verification)
echo ""
echo "--- UI Tests (Manual) ---" | tee -a "$OUTPUT_DIR/ui-tests-$TIMESTAMP.log"
echo "UI tests require Android emulator. Mark as MANUAL-REQUIRED in verification-report." | tee -a "$OUTPUT_DIR/ui-tests-$TIMESTAMP.log"

echo ""
echo "=== Verification Complete ===" | tee -a "$OUTPUT_DIR/build-$TIMESTAMP.log"
echo "Evidence saved to: $OUTPUT_DIR"
echo "NOTE: UI tests are not automated. See ui-tests-$TIMESTAMP.log for manual verification requirements."
