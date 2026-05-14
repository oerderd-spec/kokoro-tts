# Wyoming OpenAI German separator patch

This folder builds a small overlay image on top of
`ghcr.io/roryeckel/wyoming_openai:latest`.

The patch keeps German dotted abbreviations, dates, ordinals and unit
abbreviations together during streaming sentence segmentation. This prevents
Home Assistant Assist from splitting chunks too early for inputs such as
`Prof. Klein`, `5 Min.`, `2 Stck.` or `1 ltr.`.

At runtime the same root-level `german_text_rules.py` file is mounted into this
container at `/app/german_text_rules.py`.
