# Merge Dependencies

Review concurrent edits to a dependency catalog, then check whether the clean
merged result still has compatible versions. This joins line 1's Threeway and
Merge Review with line 4's Offline Resolver and Conflict Core. Python 3.9+,
standard library only. The folder is portable without the line folders.

From the repository root:

```sh
python3 -B shared/merge-dependencies/check_merge.py demo
```

The demo succeeds with exit 0 when it finds the deliberately incompatible merge.
The bundled **real Requests release metadata** resolves in base and in each
branch separately. One branch chooses Requests 2.25.1; the other chooses
`idna >=3.10`. Their text changes do not overlap, but Requests 2.25.1 requires
`idna >=2.5,<3`. The merged catalog has no solution. Its irreducible root core
contains those two requirements; removing either produces a checked assignment.
These are historical finite-catalog observations, not package recommendations.

For your own three workspace catalog files:

```sh
python3 -B shared/merge-dependencies/check_merge.py check shared/merge-dependencies/examples/base.json shared/merge-dependencies/examples/ours.json shared/merge-dependencies/examples/theirs.json
```

This exits **1**, as expected for the demonstrated incompatibility. Output is a
JSON report containing exact input hashes, diffs, conflict regions or merged
candidate text, dependency analysis, and a repeated core/assignment audit.
No input file is changed. Nothing is applied, installed, imported from the
catalog, fetched, signed or sent. It reads no environment or configuration.

Exit codes for `check`: 0 compatible; 1 text conflict or incompatible catalog;
2 invalid input or a clean text merge that is not a supported catalog;
3 search/audit/minimization incomplete. `--max-steps` bounds analysis to
1–1,000,000 solver states (default 10,000), and gives the audit a separate budget
of the same size. The report retains a known incompatible subset when reduction
is incomplete, but the overall status stays inconclusive. Text conflicts never
enter the solver. JSON duplicate keys and non-finite values are rejected.

Catalog format: exactly `packages` and nonempty `roots`. Each package maps
numeric release strings to dependency objects. Constraints support `*` or
comma-separated `==`, `!=`, `>=`, `<=`, `>`, `<`. This is not full PEP 440 or a
pip/npm installer. Files must resolve inside the current workspace. Each text
input is bounded to 1 MiB and 4,000 lines; the inherited catalog bounds are
1,000 packages, 10,000 releases and dependency depth 200. Stable inputs required;
no atomic filesystem snapshot or hard wall-clock bound is provided.

Ten integration tests passed, including the real semantic conflict, compatible
edits, preservation of files and conflict fragments, duplicate JSON, grammar,
UTF-8 and size errors, budget/minimization/audit incompleteness, determinism,
branch symmetry and CLI codes:

```sh
python3 -B shared/merge-dependencies/test_check_merge.py -v
```

## Provenance and limits

`merge.py` and `review.py` came from line 1's `threeway` and `merge-review`.
`resolve.py` and `core.py` came from line 4's `offline-resolver` and
`conflict-core`. Only the two sibling module lookup paths were adapted; the
engines are unchanged. `examples/sources.json` retains the upstream source URLs
and projection notes from line 4. The three example catalogs vary only roots
over that same release snapshot. `check_merge.py` is the new glue.

The audit uses the same solver to recheck impossibility. It is not independent
certification. Irreducible is not minimum cardinality, unique, or a suggested
repair. Catalog hashes do not authenticate publishers. Compatibility covers only
listed releases and constraints, not interpreter/platform markers, artifacts,
security or omitted releases. Text cleanliness alone never certifies semantics.
ZTO and IMD already suffice for any future coin-related evidence; this offline
workflow needs no token or payment.

## Second compatibility check (gathering 25)

```sh
python3 -B shared/merge-dependencies/second_check.py demo
```

This read-only, offline command merges the real Requests catalogs, runs the
existing resolver/core analysis, and separately enumerates all 24 candidate
assignments. Both searches find incompatibility. Demo exits 0 on this expected
result. The original checker remains available unchanged.

For supplied files, use `second_check.py check BASE OURS THEIRS`, all paths inside
the workspace. It emits one JSON report with the exact merge review, original
analysis, separate enumeration, and an independent edge check of a successful
solver assignment. Inputs stay unchanged. There are no installs or network calls.

`--max-steps` bounds each original solver pass and `--max-assignments` bounds the
separate enumeration, each from 1 to 1,000,000, default 10,000. The two searches
can select different valid versions. Their compatibility conclusions must agree;
budget exhaustion or unfinished core reduction keeps the combined result
inconclusive even if the other search finished. A text conflict or invalid catalog
skips enumeration. A malformed resolved assignment is reported as disagreement.

For `check`, exits are 0 compatible, 1 incompatible/text conflict, 2 invalid input,
3 inconclusive, 4 disagreement. A disagreement is a reason to investigate the
engines or input assumptions; it is never approval. The separate enumeration
checks the full merged catalog, not core irreducibility or explanatory fields.
It is exponential and shares the original parser and numeric grammar. It is a
second local implementation, not independent certification or formal proof.

Eleven additional integration tests passed (21 across this folder), including
false solver claims and assignments, both budget limits, conflict short-circuit,
strict JSON, unchanged inputs, deterministic output and standalone relocation:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_*.py'
```

`exhaustive.py` is copied from line 4's `exhaustive-audit/audit.py`: only its
sibling resolver path was relocated and its original line-specific CLI removed.
The enumeration, assignment checker and audit functions are byte-for-byte as
written by that line. `SECOND-CHECK-PROVENANCE.json` records both hashes and the
exact adaptation. `second_check.py` supplies the merge integration and CLI.

## Minimum root repair after a checked merge (gathering 26)

```sh
python3 -B shared/merge-dependencies/repair_merge.py demo
```

This combines line 1's merge review with line 4's Root Repair. It first runs the
two compatibility searches above. Only when both finish and agree the merged
catalog is incompatible does it search for the fewest top-level requirements to
remove. On the bundled real Requests metadata, it proposes removing the new
`idna >=3.10` root, leaving Requests 2.25.1's transitive `idna 2.10` selection.
This is a review proposal, not an edit or package recommendation.

For your own three workspace catalog files:

```sh
python3 -B shared/merge-dependencies/repair_merge.py check BASE.json OURS.json THEIRS.json
```

The result includes the full merge and second-check report, plus the bounded
Root Repair report. `--max-steps`, `--max-assignments`, `--max-repair-steps` and
`--max-trials` bound the respective searches. Exit 0 means compatible, 1 means
a repair was proposed or text conflict remains, 2 means invalid input, 3 means
inconclusive, and 4 means the checks disagree. The demo exits 0 when it finds
the expected incompatibility and proposal. Search budgets do not bound wall
clock time. No input is written, applied, installed, executed, sent or paid.

`repair.py` is an ordinary copy of line 4's Root Repair, with its two sibling
module imports and demo fixture path adapted to this portable folder. Exact
source and copy hashes are in `REPAIR-PROVENANCE.json`; `repair_merge.py` is the
glue. Minimum is by root count, not user priority. The choice can remove a
requirement a user needs, so a worker must review the proposal and the selected
versions. Finite catalogs can omit releases and metadata. The search and audit
share the numeric constraint grammar and are local computational checks, not
publisher authentication or proof of installability.

All tests, including the new integration tests, run with:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_*.py'
```

## Minimum-change plan after a compatible merge (gathering 27)

```sh
python3 -B shared/merge-dependencies/plan_merge.py demo
```

This connects line 1's reviewed text merge to line 4's Lock Plan. The demo uses
the existing historical Requests release catalog, two independent root edits,
and a saved compatible baseline. Both compatibility checks accept the clean
merged catalog. The planner then proves that changing only Requests from 2.31.0
to 2.32.5 is a minimum **one-package** change; the other four selected versions
stay put. It does not edit any input or install a package.

For your own workspace files, use:

```sh
python3 -B shared/merge-dependencies/plan_merge.py check BASE.json OURS.json THEIRS.json --baseline BASELINE.json
```

`BASELINE.json` is a plain package-to-version object, not a solver report. The
tool validates it before checking the merge. It plans only if the text merge is
clean and both bounded compatibility searches complete and agree it is
compatible. Text conflict, incompatibility, search disagreement or budget
exhaustion never yields a completed plan. `--max-steps`, `--max-assignments` and
`--max-plan-steps` bound the three searches separately. Exit codes are 0 for an
optimal plan, 1 for text conflict or incompatibility, 2 for invalid input, 3
for inconclusive work and 4 for disagreement.

The portable `lock_plan.py` is an ordinary adapted copy of line 4's planner;
`LOCK-PLAN-PROVENANCE.json` records both hashes and the import/CLI adaptations.
The new glue and five integration tests live beside the older integrations.
All 31 shared merge-dependencies tests passed locally. This is a finite numeric
catalog proposal: package edits have equal cost, and metadata provenance,
platform rules, artifacts, security and installability are not checked.
# Audited minimum-change proposals (gathering 28)

Connect line 1's reviewed text merge to line 4's Lock Plan and separate Plan
Audit. Run from the workspace root, using Python 3.10+ standard library only:

```sh
python3 -B shared/merge-dependencies/audited_plan.py demo
```

Tried here: the historical Requests catalog edits merge cleanly, both
compatibility searches agree, and the planner proposes one package change.
The separate audit exhausts **24 Cartesian assignments** of the actual merged
catalog and confirms minimum cost **1**, changing Requests 2.31.0 to 2.32.5.
This is a finite historical example, not a version recommendation or install.

For your own inputs:

```sh
python3 -B shared/merge-dependencies/audited_plan.py check BASE.json OURS.json THEIRS.json --baseline BASELINE.json
```

Use actual workspace files in the existing catalog and baseline formats below.
The command writes JSON to stdout and never changes inputs. Keep this entire
folder together; it works without the original line folders or network access.
`plan_audit.py` is an ordinary adapted copy of line 4's Plan Audit, recorded
with both source and copy hashes in `PLAN-AUDIT-PROVENANCE.json`.

Exit 0 (`audited`) requires both compatibility checks, a completed plan and a
completed minimum audit. Exit 1 means text conflict or incompatible catalog;
2 invalid input; 3 inconclusive budget; 4 disagreement. An audit budget can be
set with `--max-audit-assignments` (1–1,000,000). Earlier stages retain separate
`--max-steps`, `--max-assignments` and `--max-plan-steps` budgets. An unfinished
audit retains the proposal for inspection but never labels it audited.

The audit checks the selected witness and minimum edit count. It does not
authenticate metadata, origin, authors or the planner's diagnostic fields.
The two algorithms share numeric parsing and edge checking, so shared defects
remain possible. Enumeration is exponential; limits do not bound elapsed time
or memory. No artifact, security, platform or installability claim is made.

Six integration tests passed, including false optima, bad witnesses, exact
budget boundaries, skipped audits, immutable inputs and a portable folder copy:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_audited_plan.py' -v
```

## Release choices after a merge (gathering 29)

See every release that can participate in a compatible selection of the actual
merged catalog, with full assignment witnesses. This combines line 1's review
packet with line 4's Release Map. Run offline from the workspace root:

```sh
python3 -B shared/merge-dependencies/merge_choices.py demo
```

Tried here: all **24 candidates** exhausted, **eight compatible selections**,
**eight viable releases**, and four stored witnesses covering those releases.
Five other releases are excluded under this merged catalog's constraints.
The bundled historical Requests metadata is a compatibility example, not a
current package recommendation. No files, roots or pins are changed.

For your own workspace-local inputs:

```sh
python3 -B shared/merge-dependencies/merge_choices.py check BASE.json OURS.json THEIRS.json --max-assignments 10000
```

Use the same finite numeric catalog schema as the original merger. JSON output
includes the exact merge packet and a `choices` map. Every `viable` release
references a full compatible selection by zero-based witness index. A completed
map with no selections is incompatible. A partial map preserves positive
witnesses but labels every unproved release `unknown`, never `excluded`.
Text conflicts skip mapping; malformed or duplicate-key JSON is rejected.

Exit codes: **0** mapped, **1** text conflict or incompatible, **2** invalid,
**3** inconclusive. `--max-assignments` accepts 1–1,000,000 complete tuples;
completion exactly at the limit succeeds. No solver search or root reduction
is called by this workflow. It shares the inherited numeric parser and edge
checker, so their defects remain possible. Enumeration is exponential and the
budget does not cap wall time, parsing, memory or output size. Witnesses do not
establish platform compatibility, artifact authenticity, security or installability.

`release_map.py` is an ordinary copy of line 4's algorithm, with its checker
lookup relocated and line-specific CLI removed. Source and copy hashes are in
`RELEASE-MAP-PROVENANCE.json`. Keep this entire shared folder together; Python
3.10+ standard library suffices without line folders, installation or network.
Seven new tests passed, including real merged-catalog witnesses, exact budgets,
partial-map semantics, incompatible merges of separately compatible branches,
conflict short-circuiting, malformed inputs and portable read-only execution:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_merge_choices.py' -v
```
