# PresentationLayer — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — Task M)
VERSION: unified-schema v1.0

## Purpose
PresentationLayer is a config artifact that holds all profession-specific and context-specific
label/terminology overrides for a given consumer context (Medical app, Legal app, Compendium, Settings UI).
Layers are read by client code at render time — they never duplicate entity data.
Overrides are loaded from `_merge/presentation_layers/<code_lower>.layer.md` at application boot.

Override resolution order: layer's own override → parent layer's override → CANONICAL (entity default)

## Source-of-Truth Fields
| Field | Type | Required | Notes |
|---|---|---|---|
| code | string | yes | UPPERCASE_SHORT PK e.g. MEDICAL, LEGAL, COMPENDIUM, SETTINGS_UI |
| name | string | yes | Display name e.g. "Medical App" |
| description | string | null | Purpose of this layer |
| parent_layer_code | string | null | FK → PresentationLayer.code — for inheritance chain. CANONICAL has no parent. |
| active | boolean | yes | Whether this layer is currently used |
| config_file_path | string | yes | Path to the .layer.md file e.g. "presentation_layers/medical.layer.md" |
| created_at | datetime | yes | |
| updated_at | datetime | yes | |

## Seed Data
| code | name | parent_layer_code | config_file_path |
|---|---|---|---|
| CANONICAL | Base (Canonical names) | null | — (entity defaults) |
| COMPENDIUM | Compendium (Research Directory) | CANONICAL | presentation_layers/compendium.layer.md |
| MEDICAL | Medical App | CANONICAL | presentation_layers/medical.layer.md |
| LEGAL | Legal App (stub) | CANONICAL | presentation_layers/legal.layer.md |
| SETTINGS_UI | Settings UI | CANONICAL | presentation_layers/settings_ui.layer.md |

## Page Mixin Fields
NOT ATTACHED — PresentationLayer is a config entity, not surfaced on Compendium.

## Relationships
- parent_layer_code: many→one → PresentationLayer (self, nullable)
- code: one→many → PresentationLayer (child layers)
