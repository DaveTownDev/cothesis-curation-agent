# Live Compendium taxonomy (runtime source of truth)

JSON files here are synced from the production Compendium site and consumed by the
curation pipeline (`agents/taxonomy.py`) and review console (`console/lib/taxonomy.ts`).

## Refresh

```bash
python -m scripts.fetch_live_taxonomy
# optional override:
COMPENDIUM_BASE_URL=https://compendium-web-production.up.railway.app python -m scripts.fetch_live_taxonomy
```

Writes `live_methodologies.json` (platform codes, uppercase) and `live_specialties.json`
(specialty slugs, lowercase), and copies both to `console/lib/data/taxonomy/` for the
Next.js bundle. MVP grounding cards remain in `data/methodologies/*.md` for Vertex AI
Search only.
