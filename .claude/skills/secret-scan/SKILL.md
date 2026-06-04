---
name: secret-scan
description: Scan working tree and full history for secrets before any push.
allowed-tools: Bash
---
1. `gitleaks git -v` over the whole history.
2. `gitleaks protect --staged` on staged changes.
3. Report findings. If any: stop, tell the human to rotate the credential, then purge with `git filter-repo` before any push.
