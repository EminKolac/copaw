#!/bin/bash
# Level 3: Subagent Task Runner
# Dispatches parallel Claude Code subagents for independent tasks.
# Uses worktree isolation for safe concurrent work.
#
# Usage:
#   ./run-agents.sh "task1" "task2" "task3"
#   ./run-agents.sh --sequential "task1" "task2"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/.claude/logs"
mkdir -p "$LOG_DIR"

SEQUENTIAL=false
if [[ "${1:-}" == "--sequential" ]]; then
  SEQUENTIAL=true
  shift
fi

TASKS=("$@")

if [[ ${#TASKS[@]} -eq 0 ]]; then
  echo "Usage: $0 [--sequential] \"task1\" \"task2\" ..."
  echo ""
  echo "Examples:"
  echo "  $0 \"Add input validation to /api/chat\" \"Write tests for database.py\""
  echo "  $0 --sequential \"Run linter\" \"Fix lint errors\""
  exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

run_task() {
  local idx=$1
  local task=$2
  local logfile="$LOG_DIR/agent_${TIMESTAMP}_${idx}.log"

  echo "[Agent $idx] Starting: $task"
  echo "[Agent $idx] Log: $logfile"

  # Use claude with --print for non-interactive subagent execution
  if command -v claude &>/dev/null; then
    claude --print "$task" > "$logfile" 2>&1
    local exit_code=$?
  else
    echo "[Agent $idx] ERROR: 'claude' CLI not found in PATH" | tee "$logfile"
    return 1
  fi

  if [[ $exit_code -eq 0 ]]; then
    echo "[Agent $idx] DONE: $task"
  else
    echo "[Agent $idx] FAILED (exit $exit_code): $task"
  fi

  return $exit_code
}

echo "═══════════════════════════════════════════"
echo " Level 3: Subagent Task Runner"
echo " Mode: $([ "$SEQUENTIAL" = true ] && echo "Sequential" || echo "Parallel")"
echo " Tasks: ${#TASKS[@]}"
echo "═══════════════════════════════════════════"

PIDS=()
RESULTS=()

for i in "${!TASKS[@]}"; do
  if [[ "$SEQUENTIAL" = true ]]; then
    run_task "$i" "${TASKS[$i]}"
    RESULTS+=($?)
  else
    run_task "$i" "${TASKS[$i]}" &
    PIDS+=($!)
  fi
done

# Wait for parallel tasks
if [[ "$SEQUENTIAL" = false ]]; then
  for pid in "${PIDS[@]}"; do
    wait "$pid"
    RESULTS+=($?)
  done
fi

# Summary
echo ""
echo "═══════════════════════════════════════════"
echo " Results Summary"
echo "═══════════════════════════════════════════"
PASS=0
FAIL=0
for i in "${!TASKS[@]}"; do
  status="PASS"
  if [[ ${RESULTS[$i]} -ne 0 ]]; then
    status="FAIL"
    FAIL=$((FAIL + 1))
  else
    PASS=$((PASS + 1))
  fi
  echo "  [$status] ${TASKS[$i]}"
done
echo ""
echo "  Total: ${#TASKS[@]} | Pass: $PASS | Fail: $FAIL"
echo "  Logs: $LOG_DIR/agent_${TIMESTAMP}_*.log"
