# CoThesis Curation Agent

A multi-agent system that discovers, appraises, classifies, and writes editorial descriptions for medical-research resources, then routes each one through a quality-control panel and an arbiter gate to either auto-publish, a human review queue, or human authoring. Built for the Google for Startups AI Agents Challenge (Track 1).

## What it does
Medical trainees must complete mandatory research projects, often with little research training and little time. The Compendium is a curated, editorially independent directory that helps them find the right resource for their methodology and stage. This system is the curation pipeline behind it: it turns raw resource metadata into published, trustworthy directory entries — each with a quality assessment, methodology and stage tags, and three layers of description (a short summary, a fuller editorial note, and a jargon-free plain-English version).

## Architecture (brief)
`sources → Discovery → Appraisal → Classification → Editorial → Reconciliation → QC evaluator panel → Arbiter → routing gate → (auto-publish | review queue | human author) → published`, with grounding via Vertex AI Search and state in Firestore. See `docs/ARCHITECTURE.md`.

## Run it
See `docs/OPERATIONS.md` for GCP setup and `docs/BUILD_PLAN.md` for the build sequence. Quick local loop: `adk web agents/` then interact at the dev UI.

## Judge access
The review console is deployed on Cloud Run with a login gate. URL and demo credentials are in the submission. The agent API and MCP server are private; judges interact through the console.

## Evaluation & observability
ADK eval sets (trajectory + LLM-as-judge + grounding) plus Cloud Trace. See `docs/EVAL.md`. The demo surfaces a live trace of one resource moving through the pipeline, the eval scoreboard, and the review console.

## License
MIT (see `LICENSE`). All code is net-new for this challenge.
