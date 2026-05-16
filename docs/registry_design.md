# Registry Design

The identity registry stores known people and evidence that can support speaker attribution.

## Registry Entities

- `person`: stable human identity record.
- `voice_profile`: derived voice reference for a person.
- `face_profile`: derived face reference for a person.
- `alias`: display names, show names, or historical naming variants.
- `review_record`: human-reviewed assignment or correction.

## Required Properties

Each identity decision must be traceable to evidence:

- provider
- model version
- feature type
- candidate score
- source media
- timestamp range
- review status

## Safety Constraints

- Do not expose raw face embeddings, voice embeddings, crops, or frames through public responses.
- Do not auto-create a new known person without review.
- Do not overwrite human-reviewed registry entries.
- Prefer `unknown` or `needs_review` when evidence is weak or conflicting.

