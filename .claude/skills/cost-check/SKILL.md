---
name: cost-check
description: Summarise current GCP spend against the $500 budget.
allowed-tools: Bash
---
1. Read recent spend (BigQuery billing export if configured, else the figure the human provides).
2. Report spend, % of $500, today's burn. If burn exceeds ~$30/day, flag a possible runaway loop and recommend Flash-Lite + caching/batch. See docs/OPERATIONS.md.
