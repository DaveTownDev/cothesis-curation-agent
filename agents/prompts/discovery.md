# Discovery agent prompt

Rebuild on Gemini (Flash-Lite). Find candidate resources for a given (methodology × resource type) using the existing MCP server tools (docs/DATA_SOURCES.md). **Deterministic-and-API-first:** prefer structured API results; use the LLM only to judge relevance/dedupe candidates the APIs can't disambiguate.

For each candidate, emit raw metadata for Appraisal:
```
{ "title": string, "url": string, "source": string, "type_hint": string,
  "raw_metadata": object, "skip_reason": null | string }
```
Set `skip_reason` for anything that is not a discrete, citable resource (homepage, 404, generic department page, search results page). Do not invent resources; only return what the tools actually surface.
