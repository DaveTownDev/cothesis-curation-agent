"""
CLI: pull pending enrichment queue items and run the agent pipeline.

Usage:
  # Dry-run (shows items, no writes):
  python -m scripts.run_batch --dry-run

  # Live run with OIDC token from ADC (local dev):
  AGENT_BEARER_TOKEN=$(gcloud auth print-identity-token) python -m scripts.run_batch

  # Override batch size:
  python -m scripts.run_batch --batch-size 25

Environment variables:
  DATABASE_PUBLIC_URL   Railway Postgres URL (from Doppler dave-ai-stack/prd)
  AGENT_SERVICE_URL     Cloud Run agent URL (default: https://cothesis-agent-791873451733.us-central1.run.app)
  AGENT_BEARER_TOKEN    Bearer token for the private agent service
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_DEFAULT_AGENT_URL = "https://cothesis-agent-791873451733.us-central1.run.app"


def _get_adc_token() -> str:
    """Get an OIDC identity token from ADC for calling the private Cloud Run agent."""
    import subprocess
    result = subprocess.run(
        ["gcloud", "auth", "print-identity-token"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a batch from the enrichment queue")
    parser.add_argument("--dry-run", action="store_true", help="Show items without processing")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_PUBLIC_URL", "")
    if not db_url:
        logger.error("DATABASE_PUBLIC_URL not set — get it from Doppler dave-ai-stack/prd")
        return 1

    # The deterministic orchestrator runs in-process and uses ADC for Vertex AI.
    # No agent URL / bearer token needed — it does not call the LlmAgent /run endpoint.
    import psycopg2
    import psycopg2.extras
    from scripts.batch import run_batch

    conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        result = run_batch(
            conn=conn,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    finally:
        conn.close()

    logger.info("batch complete: processed=%d failed=%d", result.processed, result.failed)
    return 1 if result.failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
