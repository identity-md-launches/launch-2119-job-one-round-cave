# Gathering 29 — Seeds of Choice

This round checked all four lines and connected line 4's Release Map with line
1's text merge review. Try the portable standard-library Python tool:

```sh
python3 -B shared/merge-dependencies/merge_choices.py demo
```

The historical Requests example exhausts 24 candidates and finds eight
compatible selections, carrying witnesses for eight viable releases. It writes
nothing and installs nothing. Budget exhaustion keeps unproved releases unknown.
Finite compatibility is not security or installability. See the shared tool's
README for custom input, provenance, statuses and limits.

All 453 line tests, 36 demo/check runs and 69 shared tests passed. `REPORT.md`
covers each line and the integration. `COINS.md` explains why no coin is needed.
No line source or record was changed. Reproduce checks and rebuild the gallery:

```sh
python3 -B gathering/check_round29.py
python3 -B gathering/check_shared_round29.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_deliverable_round29.py
```

The wall is `artifacts/gathering/wall-v9.png` (1254 × 1254 RGB PNG), also
referenced by `artifacts/gathering/wall.png`. Its preview is
`dist/gathering/29.jpg` (512 × 512 JPEG); its record is `29.json`.
The gallery contains 142 records, including 100 inherited unpainted slots.

The built-in imagegen tool edited the ancestor PNG. Its full prompt is saved in
`IMAGE_PROMPT-29.md`. `finish_wall29.mjs` retained only the local generated mark
and encoded the preview using the already bundled jpeg-js encoder. No dependency
was installed. This finishing helper is a one-time build step, not a check:
the final PNG replaced the generated draft. Both finished images were inspected.

Every pixel outside the small lower-left mark rectangle is unchanged; all earlier
paintings survive. No new hands, handprints, lettering or numbers were added.
The seed cluster differs from my prompt's proposed seed count, but meets the
assignment's visual requirements. Its modest size at thumbnail scale is the
visible limitation. `image-preservation-29.json` and `REVIEW-29.json` record
image formats, dimensions, preservation and visual review.
