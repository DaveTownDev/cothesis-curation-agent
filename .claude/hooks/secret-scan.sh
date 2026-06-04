#!/usr/bin/env bash
# PreToolUse(Write|Edit): block writing obvious secrets. Exit 2 = deny.
input=$(cat)
pat='AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|"private_key"|LITELLM_MASTER_KEY'
if printf '%s' "$input" | grep -qiE "$pat"; then
  echo "BLOCKED by secret-scan.sh — looks like a real secret. Use a placeholder; real values go in Secret Manager." >&2
  exit 2
fi
exit 0
