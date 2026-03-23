#!/bin/bash
# Level 2: Context Window Management
# Reminds you to /compact at milestones and /clear between tasks.
#
# Usage: Source this or call functions directly.
#   compact_hint     — prints a reminder when you've done 5+ tool calls
#   clear_hint       — prints a reminder to /clear between unrelated tasks
#   session_status   — shows session health

TOOL_CALL_COUNT=0
COMPACT_THRESHOLD=60   # percent — compact BEFORE auto-compaction kicks in at 90%
TASK_COUNT=0

compact_hint() {
  TOOL_CALL_COUNT=$((TOOL_CALL_COUNT + 1))
  if [ $((TOOL_CALL_COUNT % 15)) -eq 0 ]; then
    echo "⚡ [Level 2] You've made $TOOL_CALL_COUNT tool calls this session."
    echo "   Consider running /compact to free context window."
    echo "   Rule: compact at 60% usage, not 90%."
  fi
}

clear_hint() {
  TASK_COUNT=$((TASK_COUNT + 1))
  echo "🔄 [Level 2] Task #$TASK_COUNT completed."
  echo "   If the next task is unrelated, run /clear first."
}

session_status() {
  echo "📊 Session Status:"
  echo "   Tool calls this session: $TOOL_CALL_COUNT"
  echo "   Tasks completed: $TASK_COUNT"
  echo "   Compact threshold: ${COMPACT_THRESHOLD}%"
  echo ""
  echo "   Commands:"
  echo "     /compact    — compress context (do at 60%)"
  echo "     /clear      — wipe context between tasks"
  echo "     Option+T    — toggle extended thinking"
}

echo "[Level 2] Context monitor loaded. Functions: compact_hint, clear_hint, session_status"
