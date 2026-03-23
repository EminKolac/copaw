#!/bin/bash
# Level 5: Eval Loop with Metrics
# Runs a series of evaluation prompts against Claude and scores the results.
#
# Usage:
#   ./eval-loop.sh                          # Run default eval suite
#   ./eval-loop.sh path/to/eval-suite.json  # Run custom eval suite
#   ./eval-loop.sh --dry-run                # Show what would run
#
# Eval suite format (JSON):
# [
#   {
#     "name": "test-name",
#     "prompt": "Do X and return Y",
#     "expect": "regex or substring to match in output",
#     "timeout": 120
#   }
# ]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/.claude/logs"
EVAL_DIR="$PROJECT_DIR/.claude/evals"
RESULTS_DIR="$EVAL_DIR/results"
DEFAULT_SUITE="$EVAL_DIR/default-suite.json"

mkdir -p "$LOG_DIR" "$EVAL_DIR" "$RESULTS_DIR"

DRY_RUN=false
SUITE_FILE="$DEFAULT_SUITE"

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  shift
fi

if [[ -n "${1:-}" ]]; then
  SUITE_FILE="$1"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$RESULTS_DIR/eval_${TIMESTAMP}.json"

# Create default eval suite if it doesn't exist
if [[ ! -f "$DEFAULT_SUITE" ]]; then
  cat > "$DEFAULT_SUITE" << 'SUITE'
[
  {
    "name": "file-read",
    "prompt": "Read the file .claude/settings.json and tell me how many permission allow entries there are. Reply with ONLY the number.",
    "expect": "[0-9]+",
    "timeout": 30
  },
  {
    "name": "code-gen",
    "prompt": "Write a Python function called fibonacci(n) that returns the nth Fibonacci number. Print ONLY the function, nothing else.",
    "expect": "def fibonacci",
    "timeout": 60
  },
  {
    "name": "git-status",
    "prompt": "Run git status and tell me the current branch name. Reply with ONLY the branch name.",
    "expect": ".",
    "timeout": 30
  }
]
SUITE
  echo "[Eval] Created default eval suite at $DEFAULT_SUITE"
fi

if [[ ! -f "$SUITE_FILE" ]]; then
  echo "ERROR: Eval suite not found: $SUITE_FILE"
  exit 1
fi

# Parse suite
TOTAL=$(python3 -c "import json; print(len(json.load(open('$SUITE_FILE'))))")

echo "═══════════════════════════════════════════"
echo " Level 5: Eval Loop"
echo " Suite: $SUITE_FILE"
echo " Tests: $TOTAL"
echo " Mode:  $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "LIVE")"
echo "═══════════════════════════════════════════"

PASS=0
FAIL=0
SKIP=0
RESULTS="[]"

for i in $(seq 0 $((TOTAL - 1))); do
  NAME=$(python3 -c "import json; print(json.load(open('$SUITE_FILE'))[$i]['name'])")
  PROMPT=$(python3 -c "import json; print(json.load(open('$SUITE_FILE'))[$i]['prompt'])")
  EXPECT=$(python3 -c "import json; print(json.load(open('$SUITE_FILE'))[$i].get('expect', '.'))")
  TIMEOUT=$(python3 -c "import json; print(json.load(open('$SUITE_FILE'))[$i].get('timeout', 120))")

  echo ""
  echo "[$((i+1))/$TOTAL] $NAME"
  echo "  Prompt: ${PROMPT:0:80}..."
  echo "  Expect: $EXPECT"

  if [[ "$DRY_RUN" = true ]]; then
    echo "  [SKIP] Dry run mode"
    SKIP=$((SKIP + 1))
    continue
  fi

  LOGFILE="$LOG_DIR/eval_${TIMESTAMP}_${NAME}.log"
  START_TIME=$(date +%s)

  # Run claude with timeout
  if command -v claude &>/dev/null; then
    timeout "${TIMEOUT}s" claude --print "$PROMPT" > "$LOGFILE" 2>&1 || true
  else
    echo "ERROR: claude CLI not found" > "$LOGFILE"
  fi

  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))
  OUTPUT=$(cat "$LOGFILE" 2>/dev/null || echo "")

  # Check if output matches expected pattern
  if echo "$OUTPUT" | grep -qE "$EXPECT"; then
    STATUS="PASS"
    PASS=$((PASS + 1))
    echo "  [PASS] (${DURATION}s)"
  else
    STATUS="FAIL"
    FAIL=$((FAIL + 1))
    echo "  [FAIL] (${DURATION}s)"
    echo "  Output: ${OUTPUT:0:200}"
  fi

  # Append to results JSON
  RESULTS=$(python3 -c "
import json
results = json.loads('$RESULTS' if '$RESULTS' != '[]' else '[]')
results.append({
  'name': '$NAME',
  'status': '$STATUS',
  'duration_s': $DURATION,
  'log': '$LOGFILE'
})
print(json.dumps(results))
" 2>/dev/null || echo "$RESULTS")
done

# Write report
python3 -c "
import json
from datetime import datetime

report = {
  'timestamp': '$TIMESTAMP',
  'suite': '$SUITE_FILE',
  'total': $TOTAL,
  'pass': $PASS,
  'fail': $FAIL,
  'skip': $SKIP,
  'pass_rate': round($PASS / max($TOTAL, 1) * 100, 1),
  'results': json.loads('$(echo "$RESULTS" | sed "s/'/\\\\'/g")' if '$DRY_RUN' == 'false' else '[]')
}
with open('$REPORT_FILE', 'w') as f:
  json.dump(report, f, indent=2)
print(json.dumps(report, indent=2))
" 2>/dev/null || true

echo ""
echo "═══════════════════════════════════════════"
echo " Eval Results"
echo "═══════════════════════════════════════════"
echo "  Total: $TOTAL"
echo "  Pass:  $PASS"
echo "  Fail:  $FAIL"
echo "  Skip:  $SKIP"
echo "  Rate:  $(python3 -c "print(f'{$PASS/max($TOTAL,1)*100:.1f}%')" 2>/dev/null || echo "N/A")"
echo "  Report: $REPORT_FILE"
echo "═══════════════════════════════════════════"
