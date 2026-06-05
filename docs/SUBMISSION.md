# CoThesis Curation Agent — Devpost Submission Copy (v2)

> v2 pushes the equity angle to the front and states the dual purpose honestly: a free global archive that empowers researchers anywhere, which is also the discovery and SEO funnel for the paid product. Fields marked **[CONFIRM AFTER BUILD]** describe the building experience and should be checked before submitting. The two familiarity scores are personal self-ratings.

---

## DESCRIPTION

### Problem to solve
Knowing how to do research is unevenly distributed across the world. The trainees and early researchers who learn methodology are usually the ones who already had a research-active supervisor or a well-resourced institution. Everyone else, including trainees outside metropolitan and elite centres and researchers in low- and middle-income countries, is left to work it out alone. The knowledge exists, but it is scattered, inconsistently described, and hard to find for anyone who does not already know the formal vocabulary.

A genuinely useful, openly accessible archive of research methodology resources would close part of that gap. Building one means appraising, classifying, and writing a clear, findable description for tens of thousands of resources, in language a research-naive person can actually search. That editorial work does not scale by hand. Our own library holds 1,479 ingested resources with 2,505 more queued, and not one has reached publishable quality, because the curation is the constraint.

### Our solution
The CoThesis Curation Agent is a multi-agent system that builds and maintains a free, openly accessible global archive of research methodology resources, the CoThesis Compendium, by doing the editorial work that gates it.

An Orchestrator routes each resource through specialist agents. Discovery finds candidates through the Model Context Protocol. Appraisal scores relevance and methodological quality. Classification assigns the methodology and specialty, grounded in the CoThesis taxonomy. Editorial drafts a clear description. Reconciliation dedupes against existing entries. A quality-control panel of evaluators then scores each draft, and an arbiter routes only the uncertain ones to a human curator, so the archive scales without sacrificing trust.

Two things make the archive genuinely equitable, not just free of charge:

- **It is findable by people who do not know the jargon.** Alongside a formal description, the agents generate a plain-language layer for every resource: the questions, situations, and goals a research-naive trainee would actually search for. The archive answers a novice's words, not only an expert's. A search that works only if you already know the right term is exactly the barrier we are removing.
- **A human stays in control of quality.** Drafts are scored by the panel and only the genuinely uncertain ones reach a curator, which keeps the archive trustworthy as it grows.

The demo runs across the four CoThesis MVP methodologies: Narrative Systematic Review, Scoping Review, Retrospective Chart Review, and Clinical Audit. The wider archive covers over 200 methodologies, and the same pipeline generalises across all of them.

### Technologies used
- **Gemini 2.5** (Pro and Flash/Flash-Lite) on **Vertex AI** (global endpoint) for reasoning and quality scoring
- **Agent Development Kit (ADK) 2.1**, Python, for multi-agent orchestration with tool trajectory evaluation
- **Vertex AI Search** for taxonomy-grounded classification and semantic search
- **Model Context Protocol (MCP)** for external tool access across 17 academic APIs
- **Cloud Run** for the agent service (private, IAP) and the review console (public + login gate)
- **Cloud Trace** (OpenTelemetry via `--trace_to_cloud`) for per-span pipeline observability
- **Cloud Scheduler** for daily pipeline trigger
- **Firestore** for the draft store, review queue, and pipeline state
- **Secret Manager** for all runtime secrets
- **Next.js** and **shadcn/ui** for the human-in-the-loop review console

### Data sources
The enrichment agents connect to a wide set of external APIs, selected per resource type. Across the fourteen resource types the pipeline draws on:

- **Bibliographic and citation:** PubMed, CrossRef, OpenAlex, Unpaywall, iCite, Altmetric, DataCite
- **Books:** ISBNdb, Google Books, OpenLibrary, Springer
- **Software:** GitHub, bio.tools
- **Datasets and protocols:** Zenodo, Figshare, protocols.io
- **Media and community:** YouTube Data API, Reddit, Stack Exchange, podcast RSS feeds
- **Funding:** NIH RePORTER
- **Web extraction** for resources without a structured API: Crawl4AI, SearXNG metasearch, and Marker / Docling for PDF parsing
- **Discovery:** PubMed, bioRxiv, and ClinicalTrials.gov via the Model Context Protocol

The four MVP methodologies in the demo are article-dominant, so the article enrichment path (PubMed, CrossRef, OpenAlex, Unpaywall, iCite, Altmetric) is exercised most heavily; the other type-specific APIs are wired and configured.

Grounding:
- **CoThesis taxonomy** (a subset covering the four MVP methodologies and related specialties) plus a sample of our own ingested resource metadata, used as grounding data. CoThesis's own data, used with full rights.
- **Vertex AI Search datastore** built from that subset, indexing both the formal text and the novice-vocabulary surface.

### Findings and learnings
- The highest-leverage output was not the formal description but the plain-language layer. Generating the words a research-naive trainee would actually type is what made the archive findable for the people it is meant to serve.
- Grounding classification in our own taxonomy through Vertex AI Search produced far more reliable tags than an ungrounded model, which invented plausible but wrong categories.
- The quality-control panel plus disagreement-based routing meant a curator only ever saw the uncertain items, which is what makes a free archive at this scale sustainable for a small team.
- Multi-agent orchestration via ADK made it practical to decompose a complex editorial workflow into auditable, independently testable steps. The trace waterfall in Cloud Trace makes the pipeline explainable in a way a monolithic enrichment call never could be.

### Third-party integrations (if applicable)
- **External data APIs** used by the enrichment agents, each within its terms of use: PubMed, CrossRef, OpenAlex, Unpaywall, iCite, Altmetric, DataCite, ISBNdb, Google Books, OpenLibrary, Springer, GitHub, bio.tools, Zenodo, Figshare, protocols.io, YouTube Data API, Reddit, Stack Exchange, NIH RePORTER, and podcast RSS feeds.
- **MCP connectors** to PubMed, bioRxiv, and ClinicalTrials.gov for discovery.
- **Web extraction:** Crawl4AI, SearXNG, and Marker / Docling.
- **shadcn/ui** components for the console, used under licence.
- All grounding data is CoThesis's own. No third-party proprietary datasets are bundled in the repo.

---

## SUBMISSION QUESTIONS
*(Only visible to organisers and judges)*

**Familiarity with Google Cloud products (1–5)**
**[DAVE: set your true level.]** Suggested: 2. Core stack to date has been built elsewhere; this challenge is the first substantial build on Vertex AI, Cloud Run, and Agent Platform.

**Familiarity with Google AI Studio (1–5)**
**[DAVE: set your true level.]** Suggested: 1.

**Describe the readiness of your project for launch.**
This is a working prototype built for the challenge, and it is the genesis of a real pipeline rather than a throwaway demo. It runs the full enrichment pipeline across the four MVP methodologies, scores drafts through a quality-control panel, and feeds a human review and publish console on Cloud Run. The output is intended to populate the CoThesis Compendium, the free, openly searchable archive that is the public layer of our platform. It is not yet wired into the live archive, and the next step is to point it at the existing queue and run curated batches behind the human review gate. The compute-heavy enrichment is deliberately built on Google Cloud, where it is well suited to run at scale.

**Which specific feature of Agent Platform was most critical to your project's impact, and what is one thing it's currently missing?**
Most critical: ADK's multi-agent orchestration combined with Vertex AI Search grounding, which together produce grounded, auditable classifications instead of a single opaque enrichment step. Missing: a first-class human-in-the-loop primitive between draft and publish. We built the review-and-approve gate ourselves; a native draft-review-approve step would have removed a meaningful amount of glue code.

**If you could add one specific API capability or integration that would have saved you 2+ hours of work, what would it be?**
A managed connector to ground a Vertex AI Search datastore directly from an existing knowledge graph (in our case Neo4j), without manually exporting and flattening the taxonomy first. The export-and-load step was the slowest part of standing up grounding.

**If you have any additional information on your project, please include it here.**
We are honest about why we are building this, on both counts.

The mission is access. CoThesis exists to make research methodology reachable for people outside elite, metropolitan, and well-resourced institutions, and the Compendium is the free, public layer of that: a global archive any researcher can use at no cost, and importantly one they can find in their own words rather than needing the formal vocabulary first. The curation agent is what makes building it at the required scale possible for a small team.

The commercial logic is just as real, and we would rather state it than pretend the archive is pure altruism. A large, high-quality, openly searchable archive is the top of our funnel. It provides the discovery and SEO that bring researchers to CoThesis, our paid adaptive research mentorship product. The free archive answers "what exists and what is this called." The paid product helps a trainee work out what to do in their own project. The two reinforce each other, and the honest version is the stronger one: a free public good that is also a sustainable acquisition channel is a model that can last.
