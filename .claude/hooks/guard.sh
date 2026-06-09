#!/usr/bin/env bash
# PreToolUse(Bash): deny destructive / gated commands. Exit 2 = deny.
input=$(cat)
block='git .*--force|gcloud billing|gcloud projects delete|gcloud .* delete|add-iam-policy-binding|rm -rf'
if printf '%s' "$input" | grep -qiE "$block"; then
  echo "BLOCKED by guard.sh — gated to the human (push / billing / IAM / delete / force). Ask the owner to run it." >&2
  exit 2
fi
exit 0
