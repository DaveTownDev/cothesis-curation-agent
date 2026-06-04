# AGENTS_SPEC — per-agent behaviour

Each agent's verbatim/working prompt lives in `agents/prompts/<agent>.md`. Build sequentially, one per phase. All agents read/write the record shape in docs/SCHEMA.md and emit canonical values (platform methodology codes, quality_score 0-100, the 6 dimensions, the canonical badge set).

## Discovery — `agents/prompts/discovery.md`
- **Role:** find candidate resources for a given methodology + resource type.
- **Tools:** the existing MCP server (17 academic APIs incl. PubMed/CrossRef/OpenAlex/Unpaywall/iCite/Altmetric; ISBNdb/Google Books/OpenLibrary; GitHub/bio.tools; Zenodo/Figshare/DataCite; YouTube/Reddit/Stack Exchange; NIH RePORTER; SearXNG; Crawl4AI). See docs/DATA_SOURCES.md for the per-type map.
- **Model:** Flash-Lite. **Principle:** deterministic-and-API-first; only call the LLM for what structured metadata can't resolve.
- **Output:** raw candidate metadata (title, url, source, type hint, raw fields) for Appraisal.
- **Acceptance:** returns discrete, citable resources (no homepages/404s); sets a skip_reason for non-resources.

## Appraisal — `agents/prompts/appraisal.md`
- **Role:** quality assessment + dimension scoring + draft of universal fields.
- **Inputs first (deterministic):** OpenAlex/PubMed/Semantic Scholar metadata (study type, citation signals); for articles, self-hosted RobotReviewer (risk-of-bias), URSE (GRADE), MedJEx (jargon). Then Flash for the rest.
- **Output:** `quality_score` (0-100), `ai_confidence` (0-100; <70 forces human review), `quality_dimensions` (the canonical 6 universal + `ebm_level` articles-only), `thesis_stage_signals`, `relevance_to_discipline_codes`, `proposed_badges`, `ai_subtype_signal`, `trainee_suitability_score`, `strengths`, `limitations`, `pipeline_run_id`, `requires_human_review`.
- **Per-type rubric:** GRADE/RoB for articles; ALiEM AIR for blogs/podcasts; rMETRIQ for educational media; DISCERN for consumer-facing; AACODS for grey literature. Apply the rubric that fits the type, not one scale for all.
- **Acceptance:** writes a draft AIAssessment with all six dimensions populated and reasoning per dimension.

## Classification — `agents/prompts/classification.md`
- **Role:** assign type/subtype/methodology/stage/skills/specialty/difficulty/access + relevance & confidence.
- **Critical:** emit **platform** methodology codes (SYN-01, SYN-02, OBS-01, EVAL-01 …), never legacy RS/OD. If working from the legacy prompt, apply the mapping in docs/TAXONOMY.md.
- **Model:** Flash-Lite. JSON-only output; retry once at temp 0 on parse failure, else route review_needed.
- **Acceptance:** outputs validate against the allowed values (docs/TAXONOMY.md); methodology codes are platform codes.

## Editorial — `agents/prompts/editorial.md`
- **Role:** write the three description fields and propose badges.
- **Four fields:** `editorial_description` (short, 1-2 sentences — canonical "short" display slot), `summary` (3-5 sentences — canonical "long" display slot; stored on AIAssessment; was: `editorial_description_long`), `editorial_description_plain` (jargon-free breakout card), `proposed_badges` (AI-suggested; was: `editorial_badges`).
- **Style anchor:** `data/editorial_examples/editorial_examples.md` — emulate the voice, not the resources.
- **Rules (all fields):** original wording (never copy the publisher blurb); never judgemental or negative about the resource, alternatives, or (implicitly) the reader; additive; contextualised to the trainee's situation and stage.
- **Plain-card rules:** plain English, no research terms; don't define general research concepts as asides; DO explain a method in plain words only when the method is the resource's subject (a how-to/course/textbook).
- **Badges:** max 3, from the canonical set (docs/SCHEMA.md). **Difficulty:** beginner/intermediate/advanced.
- **Acceptance:** `editorial_description`, `summary`, and `editorial_description_plain` all present; plain field contains no research jargon; passes the brand banned-phrase list. `editorial_note` is never AI-written.

## Reconciliation — `agents/prompts/reconciliation.md`
- **Role:** dedup against existing resources (title similarity 0.9). For MVP, on duplicate: stop (no merge). Assemble the final draft record (universal + type_fields).
- **Acceptance:** no duplicate published; assembled record validates against docs/SCHEMA.md.

## QC evaluator panel — `agents/prompts/qc_panel.md`
- **Role:** independent evaluators, one per quality dimension, plus ai-pattern-scanner, voice-reviewer, claim-verifier, ref_checker. Each scores + reasons.
- **Implementation:** ADK eval primitives (rubric criteria, final_response_match_v2, hallucinations_v1, safety_v1).
- **Output:** per-dimension scores + flags; surfaces disagreement.
- **Acceptance:** produces a structured panel result the arbiter can consume.

## Arbiter — `agents/prompts/arbiter.md`
- **Role:** composite score + panel-agreement → routing decision (auto-publish | review queue | human author) via the gate in docs/ARCHITECTURE.md. Panel disagreement escalates to human.
- **Model:** Pro.
- **Acceptance:** routes high-confidence agreement to auto-publish, low-confidence or disagreement to the review queue.

## Provenance (all agents)
Every AIAssessment carries: `model_version`, `assessment_prompt_version`, `pipeline_run_id`, `assessed_at`. Human ratification writes `editorial_reviewed_by` + `editorial_reviewed_at` to `Resource.editorial`. See docs/SCHEMA.md for the full field split. This supports the AI-transparency commitment and the publish gate.
