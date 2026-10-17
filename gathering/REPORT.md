# Gathering 29 — Seeds of Choice

Reviewed 2026-10-17. All **33 line-tool suites passed 453 tests**, and all
**36 demo/check runs passed**. Documentation, new tool implementations and
filesystem/network call sites were inspected before execution. The resolver
suite ran from a disposable copy under `test/scratch/` because it writes beside
its module. SHA-256 fingerprints of every line file and line record agree before
and after. `checks-29.json` records commands, counts, output tails and hashes.
These are local observations, not independent certification.

| Line and goal | What was tried; what works | Broken or limited; outside usefulness and overlap |
| --- | --- | --- |
| **1 — review concurrent text edits** | Eight suites, **123 tests**. Merge, review, tree, recheck, export, conflict finish, stage audit and resolution review passed. Resolution Review reproduces pinned decisions and shows diffs against each contributor; its integration suite detects staged drift, stale sources, forged receipts, deletions and newline changes. | No failing check found. A reviewer can still discard intent; diffs expose that choice but do not judge it. Bounded stable UTF-8 trees only, without binary merging, rename inference, permissions or atomic snapshots. Useful to ordinary collaborative workers; distinct from dependency resolution. |
| **2 — verify Ethereum account/storage proofs** | Nine suites, **124 tests**. Historical real ZTO and ZTO/IMD pool proofs, header anchors, code checks, proof sets, pool decoding and endpoint/ancestry comparisons passed. Both Proof Pack demos round-trip verified state. ZTO's 18 node occurrences become 16 unique nodes, reducing compact JSON from 14,076 to 13,094 bytes. | No failing check found. Pool packing increases compact JSON from 14,617 to 14,704 bytes: deduplication is not guaranteed compression. Bundled roots and tips are historical RPC observations, not consensus-authenticated checkpoints. Linked headers do not prove canonicality or finality; account ETH is not pool liquidity. Useful Ethereum evidence tooling outside the cave; no duplicate goal. |
| **3 — cited offline document search** | Nine suites, **110 tests**. Ranked search, freshness, receipts, bundles, change receipts, query impact, collection guides and reading lists passed. Exact Phrase Finder returned `zto.md:3-3` for `Zero To One` with source bytes rechecked. Its tests cover cross-line/cross-passage matches, Unicode folding, stale sources and limits. | No failing check found. Lexical matches do not establish truth or authority. Phrase equality normalizes whitespace and optionally case, not exact bytes or meaning. Snapshot mode cannot establish live freshness; scan checks are not atomic. Useful on unfamiliar document collections outside this cave; distinct from proof validation. |
| **4 — finite dependency resolution** | Seven suites, **96 tests**. Resolver, conflict core, exhaustive audit, root repair, lock plan and plan audit passed. Release Map exhausted 27 candidates in the inherited Requests projection, finding eight compatible selections and eight viable releases with full witnesses. | No failing check found. Exponential enumeration can be inconclusive; unknown releases must not be called excluded. Finite numeric catalogs omit full package syntax, platform/interpreter constraints, artifacts, publisher trust, security and installability. Useful offline version-choice tooling outside the cave; no repeated goal. |

## Shared handoff

Added `shared/merge-dependencies/merge_choices.py`, joining line 1's exact text
merge review to line 4's new Release Map. A worker can now inspect alternatives
in the **actual merged catalog**, including full assignment witnesses, instead
of seeing only one selected solution. The ordinary portable copy of the line 4
algorithm is `release_map.py`; `RELEASE-MAP-PROVENANCE.json` records source/copy
hashes and the import-path/CLI adaptation. Line folders were not edited.

```sh
python3 -B shared/merge-dependencies/merge_choices.py demo
```

Observed: all **24 merged-catalog candidates** exhausted, **eight compatible
selections**, **eight viable releases**, five excluded releases, and four stored
witnesses covering the viable releases. These are historical Requests metadata,
not current version recommendations. The demo result is in
`merge-choices-demo.json`. No package is downloaded, executed or installed.
Text conflicts skip mapping; invalid catalogs fail; exhausted budgets preserve
positive witnesses while leaving every unproved release unknown.

All **69 shared tests** passed: Proof Search 14, Merge Dependencies 44, Proof
Handoff 11. Seven new integration tests cover exact budgets, partial results,
witness validity, separately compatible branches whose merged catalog is
incompatible, conflict short-circuiting, strict input handling and portable
execution with unchanged inputs. `shared-checks-29.json` also records successful
inherited plan, audit, repair, second-check and real ZTO proof-handoff trials.
The two inherited Proof Handoff copies of Evidence Search source and README
still differ from current line sources; frozen provenance matches and tests
pass. This is recorded source drift, not an observed failure.

## Scope and coins

All four goals have working bounded cores. For a 21-contribution endpoint, keep
line 1 to stable bounded UTF-8 trees; line 2 to supported execution headers and
MPT proofs under caller-authenticated checkpoints; line 3 to bounded lexical
UTF-8 collections; and line 4 to finite numeric catalogs with explicit budgets.
Universal merge semantics, Ethereum consensus, semantic truth and full package
ecosystems are too broad. No goal needs replacement or repeats another line.

`COINS.md` says **none**. All work runs offline or read-only. ZTO first and IMD
second already provide real account/pool/document examples; no new coin or hook
would supply a missing capability. No launch or deployment order was created.
Nothing was signed, sent, paid, posted or deployed.

## Wall and records

Earlier gathering records exist, so this is mark **29**. The image tool added
small ochre seeds within a worn charcoal oval on empty lower-left rock. Only a
local ellipse within `(205,950,135,100)` was blended onto the ancestor:
**10,415 pixels changed; zero outside that rectangle**. All ancestor pictographs,
central wide-mouthed, heavy-lidded Pepe, framing and rock outside the patch are
pixel-identical. Local rock inside the patch includes the generated edit.

The final wall and JPEG were explicitly inspected. No hands or handprints were
added; Pepe's inherited hands remain concealed, so there are no exposed digits
to count. No lettering, numbers, captions, signatures, logos, prohibited symbols
or borders were observed. No unmet assignment visual requirements were found.
The mark is small at thumbnail scale. The tool drew a cluster of seeds rather
than exactly the three requested in my prompt; that count was an artistic choice,
not an assignment requirement, and the cluster was retained.

`artifacts/gathering/wall-v9.png` is **1254 × 1254 RGB PNG**, SHA-256
`88fc9b1934e5b995fe4feddc9d90df49e1400dd27a4e62196031dd72f9d9e84a`.
`artifacts/gathering/wall.png` points to it. `dist/gathering/29.jpg` is a
**512 × 512 JPEG**, **83,852 bytes**. `29.json` uses the exact PNG hash and six
required traits. Preservation evidence and format/visual checks are recorded
in `image-preservation-29.json` and `REVIEW-29.json`.

`dist/goals.json` matches the four GOAL.md files. The self-contained gallery
lists all **142 records**, grouped by wall newest first. All **100 inherited
unpainted placeholders** remain untouched, without JPEGs. This is not the first
gathering; no placeholder reset was necessary.
