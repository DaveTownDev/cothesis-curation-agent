#!/usr/bin/env node
// Seed a test review_queue item for local dev
// Usage: npx tsx scripts/seed-review-queue.ts

import * as admin from "firebase-admin"

const projectId = process.env.GOOGLE_CLOUD_PROJECT || "cothesis-curation-agent"
if (!admin.apps.length) {
  admin.initializeApp({ projectId })
}
const db = admin.firestore()

const draftRecord = {
  resource_code: "demo-article-001",
  title: "Using thematic analysis in psychology",
  url: "https://doi.org/10.1191/1478088706qp063oa",
  resource_type_code: "article",
  resource_subtype_code: "empirical_research",
  editorial_description:
    "The foundational paper on reflexive thematic analysis, introducing the six-phase method for qualitative researchers across disciplines.",
  editorial_description_plain:
    "A guide explaining how to find patterns (themes) in interview or text data. Written for psychology researchers but useful for anyone doing qualitative research.",
  summary:
    "Braun and Clarke's 2006 paper established thematic analysis as a primary method in qualitative psychology. It outlines six phases: familiarisation, coding, theme generation, review, definition, and write-up. The paper distinguishes this approach from other qualitative methods and has become one of the most cited methodology papers across the social sciences. It is especially valued for its accessibility to researchers new to qualitative work.",
  editorial_note: null,
  methodology_codes: ["SYN-01"],
  discipline_codes: ["psychology", "social_sciences"],
  stage_codes: ["ST", "IN"],
  difficulty_level: "beginner",
  access_type: "subscription",
  skill_codes: ["FS-05", "FS-09"],
  quality_score: 76,
  ai_confidence: 85,
  relevance_score: 0.93,
  classification_confidence: 0.88,
  proposed_badges: ["essential", "best_beginners"],
  strengths: ["Highly cited", "Clear methodology steps", "Accessible writing"],
  limitations: ["Subscription access required", "Limited to text-based data"],
  requires_human_review: true,
  editorial_status: "in_review",
  quality_dimensions: {
    relevance: { score: 90, weight: 0.2, reasoning: "Core qualitative methodology resource" },
    accuracy: {
      score: 95,
      weight: 0.2,
      reasoning: "Peer-reviewed, widely replicated methodology",
    },
    authority: { score: 98, weight: 0.2, reasoning: "50,000+ citations, foundational text" },
    currency: { score: 70, weight: 0.15, reasoning: "2006 paper; method is still standard" },
    accessibility: { score: 55, weight: 0.15, reasoning: "Subscription paywall" },
    practical_utility: {
      score: 88,
      weight: 0.1,
      reasoning: "Step-by-step, immediately applicable",
    },
  },
}

async function seed() {
  await db.collection("review_queue").doc("demo-review-001").set({
    resource_code: "demo-article-001",
    routing: "review_needed",
    reason:
      "quality_score 76 (60-79 range) and ai_confidence 85 triggers human review per QC policy",
    panel_result: {
      panel_agreement: 0.82,
      ai_pattern_scanner: "pass",
      voice_reviewer: "pass",
      plain_jargon_check: "pass",
      badge_check: "pass",
    },
    draft_record: draftRecord,
    status: "pending",
    queued_at: new Date().toISOString(),
  })
  console.log("✓ Seeded review_queue/demo-review-001")
  process.exit(0)
}

seed().catch((e) => {
  console.error(e)
  process.exit(1)
})
