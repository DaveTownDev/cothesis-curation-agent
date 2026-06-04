# field_maps/

Drop the per-type golden-record field maps here (from the Cowork project): `field_mapping_<type>_complete.md` for each of the 14 resource types. These define the `type_fields` written per resource type (docs/SCHEMA.md). The build uses them to populate type-specific fields; without a type's map, that type falls back to universal fields only.

14 types: article, book, book_chapter, video, podcast, software, reporting_guideline, course, web_guide, template, visual_reference, dataset, community, funding.
