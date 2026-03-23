#!/bin/bash
# Level 4: Ralph Wiggum Stop Hook
# "I'm in danger!" — keeps Claude going when it stops prematurely.
#
# When Claude stops, this hook checks if there are incomplete todos
# and nudges it to continue. Named after Ralph Wiggum because
# Claude sometimes stops when it shouldn't ("I'm helping!").
#
# Install: Add to settings.json under hooks.Stop
#
# How it works:
# 1. Checks if there's a CLAUDE_TASK_FILE with remaining tasks
# 2. If tasks remain, outputs a continue prompt to stdout
# 3. Claude reads the hook output and resumes work

TASK_FILE="${CLAUDE_TASK_FILE:-/home/user/copaw/.claude/current-task.md}"
STOP_LOG="/home/user/copaw/.claude/logs/stop-hook.log"

mkdir -p "$(dirname "$STOP_LOG")"

timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Check for uncommitted changes that suggest incomplete work
UNCOMMITTED=$(cd /home/user/copaw && git status --porcelain 2>/dev/null | wc -l)

# Check for todo file with remaining tasks
REMAINING_TASKS=0
if [[ -f "$TASK_FILE" ]]; then
  REMAINING_TASKS=$(grep -c '^\- \[ \]' "$TASK_FILE" 2>/dev/null || echo 0)
fi

echo "[$timestamp] Stop hook fired. Uncommitted: $UNCOMMITTED, Remaining: $REMAINING_TASKS" >> "$STOP_LOG"

if [[ $REMAINING_TASKS -gt 0 ]]; then
  echo "⚠️  You stopped but there are $REMAINING_TASKS incomplete tasks in $TASK_FILE."
  echo "Continue working on the next unchecked task."
  echo "[$timestamp] CONTINUE — $REMAINING_TASKS tasks remain" >> "$STOP_LOG"
elif [[ $UNCOMMITTED -gt 0 ]]; then
  echo "⚠️  You have $UNCOMMITTED uncommitted changes."
  echo "Did you forget to commit? Review changes and commit if ready."
  echo "[$timestamp] WARN — $UNCOMMITTED uncommitted files" >> "$STOP_LOG"
else
  echo "[$timestamp] CLEAN STOP — no remaining tasks or changes" >> "$STOP_LOG"
fi
