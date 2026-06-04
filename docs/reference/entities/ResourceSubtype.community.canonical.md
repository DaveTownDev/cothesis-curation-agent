# ResourceSubtype.community — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: community
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A community is an online or offline group, forum, society, or network relevant to researchers — including Reddit communities, Slack groups, professional societies, and special interest groups.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `platform_code` | string | No | → ContentPlatform.code. Platform hosting the community e.g. `reddit`, `slack`, `discord`, `facebook_groups`, `linkedin`. |
| `member_count` | integer | No | Current membership count. |
| `subscriber_count` | integer | No | Subscriber/follower count (for broadcast-style communities). |
| `membership_type` | string (enum) | No | `open` \| `invitation` \| `paid`. Whether joining is open, requires invitation, or requires payment. |
| `moderation_level` | string (enum) | No | `light` \| `moderate` \| `heavy`. Level of content moderation. |
| `services_offered` | string[] | No | Services or activities the community offers e.g. `mentoring`, `job_board`, `webinars`, `journal_club`. |
| `geographic_scope` | string (enum) | No | `local` \| `national` \| `regional` \| `global`. |
| `eligibility` | string | No | Eligibility requirements for joining. |
| `newsletter_frequency` | string | No | Newsletter cadence e.g. `weekly`, `monthly`, `irregular`. |
| `newsletter_subscribe_url` | string (uri) | No | Newsletter subscription URL. |
| `social_links` | object | No | Social media links: `{twitter, facebook, linkedin, instagram, ...}`. |
| `contact_email` | string (email) | No | Public contact email for the community. |
| `icon_url` | string (uri) | No | Community icon/avatar URL. Cluster F; canonical thumbnail_url is the standardised form. |
| `logo_url` | string (uri) | No | Community logo URL. Cluster F. |
| `person_entity_ids` | string[] | No | → Person.code[] for moderators/administrators. |

## Notes

- Community is the sparsest subtype by field count (~29 total including inherited) — the file is acknowledged as stub-like in matrix §6.6.
- Known real gaps from matrix §6.5: no first-class `authors`/`operator` field (use `person_entity_ids` for moderators), no view/visit engagement metric (member_count is present), no explicit `licence_type` or `is_open_access` (N/A conceptually for communities).
- `thumbnail_url` on the Resource base covers the canonical image field; `icon_url` and `logo_url` here are community-specific display variants.
- `geographic_scope` is also present on dataset — both use the same enum values.
