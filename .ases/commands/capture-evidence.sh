#!/bin/bash
# capture-evidence.sh — Master script to route verification to appropriate stack
# Usage: ./capture-evidence.sh <task-id> <stack> [output-dir]
# Stacks: typescript, python, android, all
# Example: ./capture-evidence.sh task-001 typescript .ases/evidence/task-001

TASK_ID="${1:?Task ID required (e.g., task-001)}"
STACK="${2:?Stack required (typescript|python|android|all)}"
OUTPUT_DIR="${3:-.ases/evidence/$TASK_ID}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$STACK" in
  typescript|ts)
    echo "Running TypeScript verification for $TASK_ID..."
    "$SCRIPT_DIR/verify-ts.sh" "$TASK_ID" "$OUTPUT_DIR"
    ;;
  python|py)
    echo "Running Python verification for $TASK_ID..."
    "$SCRIPT_DIR/verify-python.sh" "$TASK_ID" "$OUTPUT_DIR"
    ;;
  android|kotlin)
    echo "Running Android/Kotlin verification for $TASK_ID..."
    "$SCRIPT_DIR/verify-android.sh" "$TASK_ID" "$OUTPUT_DIR"
    ;;
  all)
    echo "Running all verifications for $TASK_ID..."
    "$SCRIPT_DIR/verify-ts.sh" "$TASK_ID" "$OUTPUT_DIR"
    "$SCRIPT_DIR/verify-python.sh" "$TASK_ID" "$OUTPUT_DIR"
    "$SCRIPT_DIR/verify-android.sh" "$TASK_ID" "$OUTPUT_DIR"
    ;;
  *)
    echo "ERROR: Unknown stack '$STACK'"
    echo "Usage: ./capture-evidence.sh <task-id> <typescript|python|android|all> [output-dir]"
    exit 1
    ;;
esac

echo ""
echo "Evidence captured to: $OUTPUT_DIR"
echo "Next: Read logs and populate verification-report.md with results."
