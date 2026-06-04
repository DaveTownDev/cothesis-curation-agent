# User — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: entity_User.md (primary)
VERSION: unified-schema v1.0 (merge output)
NOTE: Account / identity layer only. Personalisation in UserProfile.

## Purpose
User holds authentication, account identity, and access control data.
The User entity is system-facing — it does NOT hold research preferences, marketplace data, or professional identity. Those live in UserProfile (1:1 relationship).

## Source-of-Truth Fields
| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| code | string | yes | — | Stable human-readable PK e.g. "USR-0042" |
| email | string | yes | — | Primary login identifier |
| email_verified | boolean | yes | — | |
| auth_provider | enum | yes | — | email \| google \| apple \| microsoft |
| auth_provider_id | string | null | — | External auth provider UID |
| display_name | string | null | — | Shown in UI |
| avatar_url | string | null | — | Profile picture URL |
| role | enum | yes | — | trainee \| supervisor \| admin \| viewer |
| is_active | boolean | yes | — | Account active |
| last_login_at | datetime | null | — | |
| created_at | datetime | yes | — | |
| updated_at | datetime | yes | — | |
| deleted_at | datetime | null | — | Soft delete |

## Page Mixin Fields
NOT ATTACHED — Users are private, not surfaced on Compendium.

## Derived Fields
(none)

## Relationships
| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| code | one→one | UserProfile | user_code | |
| code | one→many | Project | user_code | Owned projects |
| code | one→many | SupervisionRelationship | trainee_code OR supervisor_code | |
