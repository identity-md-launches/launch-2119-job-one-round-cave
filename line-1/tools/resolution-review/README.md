# Resolution Review

See exactly what a conflict resolution changes relative to **each contributor**,
and check that the staged result still matches that choice. A hash match alone
cannot show that a reviewer dropped someone's work. This tool pairs reproduced
decisions and reasons with base/ours/theirs diffs, then checks the staged tree.
Python 3.10+ standard library only. No installation or network is needed.

From the workspace root, one command demonstrates the full filesystem workflow:

```sh
python3 -B line-1/tools/resolution-review/test_review.py
```

When tried, all **16 integration tests passed**. All **107 inherited tests** also
passed. Tests cover both-contributor and one-sided resolutions, explicit deletion,
empty files, file/directory conflicts, CRLF, Unicode, final newlines, terminal
controls, stale sources, rehashed forged packets/receipts, receipt pins, staged
drift on clean paths, bounds, and read-only behavior. An additional trial used
copies of the existing Threeway tool's six real source/documentation/example
files: both competing README additions survived resolution; removing one later
produced a diff showing the lost line. Sources stayed unchanged. These are local
checks, not independent certification. Evidence: `../../CHECKS-28.json` and
`../../REAL-TRIAL-28.json`.

For a short in-memory explanation with no writes:

```sh
python3 -B line-1/tools/resolution-review/review.py --demo
```

## Review an actual resolution

First use the sibling Tree Review and Conflict Finish tools to produce a saved
merge packet, decisions, staged tree and receipt. Keep the three source trees
and original decision file. Retain the exact SHA-256 hashes of the packet and
receipt independently after reviewing them. Then run:

```sh
python3 -B line-1/tools/resolution-review/review.py PACKET BASE OURS THEIRS DECISIONS RECEIPT STAGED --packet-sha256 PACKET_HASH --receipt-sha256 RECEIPT_HASH
```

Uppercase arguments denote your actual workspace paths and retained lowercase
64-digit digests. They are not literal sample values. Store packet, decisions
and receipt outside the three input trees and the staged tree. Run from the
workspace root. The staged directory can have moved: the receipt's `output`
metadata is never followed. The CLI reads only caller-selected workspace data
and its explicitly named sibling modules. It writes nothing and runs no input
code. It does not read environment variables or use secrets.

The check validates both pins, the receipt's packet binding and its exact
decision-file hash. It snapshots the three sources once, reproduces the entire
saved review, recomputes the selected files, reasons and omissions, and compares
the resulting manifest and resolution metadata with the receipt. Only after
those checks pass does it read and audit the staged tree. A source or receipt
mismatch stops the pipeline; omitted later fields mean **not checked**, not
success. Valid JSON is not enough: a self-consistent but invented receipt fails
reproduction.

JSON output uses `resolution-review/v1`:

| Field | What to inspect |
| --- | --- |
| `matches`, `status` | Overall reproduction and stage equality, never semantic approval. |
| `source_recheck` | Original source manifests and review must reproduce. |
| `receipt_recheck` | Names fields differing from recomputed decisions/output. |
| `resolutions` | Each conflict's reason, selected state, and diffs from base/ours/theirs to the selected result. |
| `stage_audit` | Added, missing or changed files/directories after staging. |
| `stage_diffs` | Selected-to-staged differences, including drift on clean paths. |

Each comparison carries `before`, `after`, `identical`, and a unified `diff`.
File states contain byte length and exact UTF-8 SHA-256. Missing and directory
states are explicit. An empty file becoming absent can therefore have an empty
diff but `identical: false`. A directory's state describes only its kind, not
the contents below it; descendant paths and full manifests cover those. Diffs
show context and changed lines, not full files. JSON escapes terminal control
characters. Newline spelling remains part of the fingerprint.

Exit **0** means the entire chain reproduces and the stage matches (or the demo
ran); **1** means `stale-inputs`, `review-mismatch`, `receipt-mismatch`, or
`stage-drift`; **2** means invalid pins, invalid/unsupported input or an I/O error.
Errors emit an escaped diagnostic on stderr and no partial JSON on stdout.

## Bounds and limits

Keep the sibling `conflict-finish`, `candidate-export`, `stage-audit`,
`review-recheck`, `tree-review`, `merge-review`, and `threeway` folders. Their
bounded readers, deterministic merge engine and decision resolver are reused.
This is an end-to-end reproduction check, not an independent merge algorithm.
Clean export receipts are deliberately unsupported; use Stage Audit for those.

Inputs must be stable, trusted workspace trees without symlink components.
Files are UTF-8 without NUL, at most 1 MiB and 4,000 lines each. Each tree allows
128 files, 256 directories and 16 nesting levels. The three sources share an
8 MiB budget; the stage has a separate 8 MiB budget. Packet, decisions and
receipt limits are respectively 64 MiB, 16 MiB and 1 MiB. There is no atomic
snapshot, race protection, executable-bit/permission check, binary merge or
rename inference. Repeated-line diffs can be ambiguous. Hashes do not prove
authorship, semantic correctness or that a resolution preserves intent; read
the diffs and decide. No coin, price, payment, wallet or chain is needed.
