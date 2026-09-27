# Illuminated code artwork

The approved Anti-Dark-Code mark combines code brackets with a beam of light.
Its black-and-gold palette echoes the owner's GitHub profile logo. The charcoal tile works on light and dark host backgrounds. The small icon
removes the glass reflection and uses heavier strokes for legibility.

- `illuminated-code.svg`: editable full-size vector source.
- `illuminated-code.png`: transparent 512 x 512 plugin logo export.
- `illuminated-code-small.svg`: simplified editable vector source.
- `illuminated-code-small.png`: transparent 128 x 128 composer icon export.

PNG files are lossless browser renders of the matching SVG at the stated size,
with no page margin and a transparent canvas. No fonts or external resources
are required. The repository license applies to these original assets.

Codex uses the same files through `agents/openai.yaml` (skill-relative paths)
and the generated plugin manifests (repository-relative paths). Regenerate
manifest fields with `adc_packaging.py --write`; do not edit only a generated
manifest. Published release tags and archives retain their original artwork.
