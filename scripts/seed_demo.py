"""
Seed demo data by running the deterministic pipeline on a curated set of real
resources spanning the 4 MVP methodologies and several resource types.

Populates drafts, draft_records, review_queue, and pipeline_state with real
LLM-produced content for the demo. Run:
  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("seed")

SEED = [
    {"title": "PRISMA 2020 statement: an updated guideline for reporting systematic reviews",
     "url": "https://doi.org/10.1136/bmj.n71", "resource_type": "reporting_guideline",
     "methodology_tags": ["systematic-review"], "doi": "10.1136/bmj.n71"},
    {"title": "Cochrane Handbook for Systematic Reviews of Interventions",
     "url": "https://training.cochrane.org/handbook", "resource_type": "book",
     "methodology_tags": ["systematic-review", "meta-analysis"]},
    {"title": "PRISMA Extension for Scoping Reviews (PRISMA-ScR)",
     "url": "https://doi.org/10.7326/M18-0850", "resource_type": "reporting_guideline",
     "methodology_tags": ["scoping-review"], "doi": "10.7326/M18-0850"},
    {"title": "Scoping studies: towards a methodological framework",
     "url": "https://doi.org/10.1080/1364557032000119616", "resource_type": "article",
     "methodology_tags": ["scoping-review"], "doi": "10.1080/1364557032000119616"},
    {"title": "A Guide to the Retrospective Chart Review",
     "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4319758/", "resource_type": "article",
     "methodology_tags": ["cohort-study", "case-control"]},
    {"title": "The RECORD Statement: Reporting of studies Conducted using Observational Routinely-collected health Data",
     "url": "https://doi.org/10.1371/journal.pmed.1001885", "resource_type": "reporting_guideline",
     "methodology_tags": ["cohort-study", "cross-sectional"], "doi": "10.1371/journal.pmed.1001885"},
    {"title": "STROBE Statement: guidelines for reporting observational studies",
     "url": "https://doi.org/10.1016/j.jclinepi.2007.11.008", "resource_type": "reporting_guideline",
     "methodology_tags": ["cohort-study", "cross-sectional", "case-control"],
     "doi": "10.1016/j.jclinepi.2007.11.008"},
    {"title": "SQUIRE 2.0 (Standards for QUality Improvement Reporting Excellence)",
     "url": "https://doi.org/10.1136/bmjqs-2015-004411", "resource_type": "reporting_guideline",
     "methodology_tags": ["quality-improvement", "clinical-audit"], "doi": "10.1136/bmjqs-2015-004411"},
    {"title": "Clinical audit: a guide for the busy clinician",
     "url": "https://www.rcgp.org.uk/clinical-audit", "resource_type": "web_guide",
     "methodology_tags": ["clinical-audit", "quality-improvement"]},
    {"title": "Covidence: systematic review software",
     "url": "https://www.covidence.org/", "resource_type": "software",
     "methodology_tags": ["systematic-review"]},
    {"title": "Using thematic analysis in psychology",
     "url": "https://doi.org/10.1191/1478088706qp063oa", "resource_type": "article",
     "methodology_tags": ["qualitative", "thematic-analysis"], "doi": "10.1191/1478088706qp063oa"},
    {"title": "Intuitive Biostatistics: A Nonmathematical Guide to Statistical Thinking",
     "url": "https://www.intuitivebiostatistics.com/", "resource_type": "book",
     "methodology_tags": ["statistics"]},
]


def main() -> int:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")

    from agents.pipeline.deterministic import run_pipeline

    outcomes = {"auto_accept": 0, "review_needed": 0, "auto_exclude": 0, "error": 0}
    for i, res in enumerate(SEED, 1):
        try:
            out = run_pipeline(res, pipeline_run_id=f"seed-{i:02d}")
            routing = out.get("routing", "error")
            outcomes[routing] = outcomes.get(routing, 0) + 1
            logger.info("[%d/%d] %-50s -> %s", i, len(SEED), res["title"][:50], routing)
        except Exception as exc:
            outcomes["error"] += 1
            logger.error("[%d/%d] %-50s -> ERROR %s", i, len(SEED), res["title"][:50], exc)

    logger.info("Seed complete: %s", outcomes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
