# Round 27 — Release Map

[Release Map](tools/release-map/README.md) identifies every catalog release
that can participate in a complete compatible selection, with witnesses and
explicit unknown results when its enumeration budget runs out.

```sh
python3 -B line-4/tools/release-map/release_map.py demo
```

The historical Requests snapshot has eight compatible selections among 27
candidates. Ten tests passed, including 200 seeded catalog comparisons.
[Round 27 notes](README-27.md) describe the tool, mark and limitations.

# Round 26 — Plan Audit

[Plan Audit](tools/plan-audit/README.md) checks a minimum-package-edit claim with
bounded Cartesian enumeration, without importing the planner or its scoring.

```sh
python3 -B line-4/tools/plan-audit/audit_plan.py demo
```

The historical Requests demo exhausts all 27 assignments and confirms the
one-package minimum. All 13 new tests and 14 inherited Exhaustive Audit tests
passed. Budget exhaustion stays inconclusive; shared parsing and edge checking
remain trust dependencies. This is finite-catalog compatibility, not installability.

The mark is a branching pebble path: compare the shorter change with the longer
one. Output is `artifacts/line-4/wall-v8.png`, continued at `wall.png`; record and
512-pixel preview are `dist/line-4/26.json` and `26.jpg`. The PNG remains
1254 × 1254; every pixel outside the added patch is unchanged. Formats,
preservation and visual limitations are recorded in [IMAGE-26.json](IMAGE-26.json)
and [REVIEW-26.json](REVIEW-26.json).

# Round 24 — Root Repair

[Root Repair](tools/root-repair/README.md) finds a minimum-cardinality set of root
requirements to drop, then checks a compatible assignment for the retained roots.

```sh
python3 -B line-4/tools/root-repair/repair.py demo
```

The offline real Requests snapshot needs one root removal (`idna >=3.10`), found
in three trials and ten search states. All 12 new tests passed, including 250
seeded exhaustive comparisons. The search is bounded and can return inconclusive;
minimum cardinality relies on the inherited solver. No catalog is changed.

The mark is three ochre stones in a charcoal loop, with one stone set aside.
[IMAGE-24.json](IMAGE-24.json) records dimensions, formats and pixel preservation;
[REVIEW-24.json](REVIEW-24.json) records local visual checks. Output is
`artifacts/line-4/wall-v6.png`, continued at `wall.png`; record and preview are
`dist/line-4/24.json` and `24.jpg`.

# Line 4 — parts that fit

Round 22 adds [Conflict Core](tools/conflict-core/README.md): isolate an
irreducible set of conflicting root requirements, with compatible assignments
for removing each member and a catalog-bound audit command.

```sh
python3 -B line-4/tools/conflict-core/core.py demo
```

The real Requests/idna example reduces four roots to two. All 15 new and 17
original tests pass. Round 22's wall adds two incompatible ochre pieces inside a
charcoal loop and one unnecessary pebble outside. [REVIEW-22.json](REVIEW-22.json)
records image dimensions, preservation measurements and limitations. The new
record is `dist/line-4/22.json`; the required export is
`artifacts/line-4/wall-v4.png`. The original goal and earlier tools are preserved.

The goal is finite offline dependency resolution, with an explanation when the
catalog cannot satisfy the requested constraints. The first working piece is
[Offline Resolver](tools/offline-resolver/README.md). From the repository root:

```sh
python3 -B line-4/tools/offline-resolver/resolve.py demo
```

It resolved a bundled snapshot of real Requests dependencies in six search states.
Seventeen behavioral tests passed, including 400 randomly generated catalogs
cross-checked by exhaustive enumeration. Package execution and installation are
outside this tool's scope. Unsupported constraint syntax is rejected; budget
exhaustion returns `inconclusive`, not `unsatisfiable`. Details and limitations
are in the tool README.

## Mark 01 — Parts That Fit

Pepe sorts ochre stones beside converging charcoal paths: finding compatible parts
that can work together. This first painting leaves much of the lit rock open.
The scene uses charcoal, red/yellow ochre, and chalk on the original warm cave.

- Wall: `artifacts/line-4/wall.png`, square RGB PNG, 1254 × 1254.
- Preview: `dist/line-4/01.jpg`, RGB JPEG, 512 × 512.
- Record: `dist/line-4/01.json`, with the finished PNG's SHA-256 URL.
- Review: `REVIEW.json`, with dimensions, formats, checks, and visual limitations.

The built-in image tool edited the supplied bare cave. The prompt is saved in
[IMAGE_PROMPT.md](IMAGE_PROMPT.md). Visual review checks the original framing,
major cracks, crystals and warm light, recognizable heavy-lidded Pepe and wide
mouth, five digits per hand, and absence of writing and forbidden symbols.
AI editing does not guarantee byte-identical background texture. This is a local
visual review; the verifier's byte checks do not certify appearance.
