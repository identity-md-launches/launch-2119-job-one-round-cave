# Release Map

Show which versions in a finite offline dependency catalog can participate in
at least one complete compatible selection. Each `viable` release points to a
full reachable assignment in `witnesses`, using a zero-based index. This lets a
worker compare several feasible pins instead of accepting the solver's first
answer.

From the repository root, run this entirely offline example:

```sh
python3 -B line-4/tools/release-map/release_map.py demo
```

On the inherited historical Requests metadata projection this exhausted **27
Cartesian candidates**, finding **eight distinct compatible selections**. Eight
of the ten catalog releases were viable. Requests 2.31.0 and urllib3 2.5.0 were
excluded by this catalog's roots and dependency constraints. Four stored
witnesses cover all eight viable releases. These are finite compatibility
observations, not current version or installation recommendations.

Python 3.9+ and only its standard library are required. Keep the adjacent
`offline-resolver/` and `exhaustive-audit/` tools; demo also uses Offline
Resolver's bundled `examples/requests.json` and its metadata provenance. No
package code is executed. The tool reads explicit workspace-local JSON and
prints JSON; it writes no files, uses no network and reads no configuration,
environment variables, accounts or secrets.

For another catalog:

```sh
python3 -B line-4/tools/release-map/release_map.py path/to/catalog.json --max-assignments 10000
```

Use Offline Resolver's `packages`/`roots` JSON schema, canonical package names,
one-to-four-component numeric versions and comma-conjoined comparison clauses.
Unsupported full package-manager syntax is rejected. Its bounded loader rejects
duplicate keys, external paths and symlinks escaping the current workspace.

`complete` (exit 0) means every candidate was checked; each release is then
`viable` or `excluded`. Excluded means no solution **in this catalog under these
roots** includes it in the reachable dependency closure. It can mean the
package is simply irrelevant to all roots. It does not mean the release is
broken or unusable for another catalog. A complete result with zero compatible
selections excludes every release and establishes catalog incompatibility.

`inconclusive` (exit 3) preserves valid positive witnesses, but every release
without a witness stays `unknown`. The compatible-selection count is then only
a lower bound. No absence or impossibility claim is made from a budget cutoff.
Invalid input returns exit 2. Budgets accept integers 1–1,000,000. Completion
exactly at the budget, including a zero-candidate domain, is conclusive.

The search overapproximates reachable packages through all catalog release
edges, enumerates root-compatible versions and optional absent values for
nonroots, and checks each candidate's actual root closure. A candidate counts
only when its non-absent packages equal that closure. Thus an unused package's
different version choices never inflate solution counts. Cycles are handled
iteratively. Missing possibly required packages are listed separately; they
invalidate only branches that actually need them. Witnesses are retained only
when they demonstrate a previously unseen viable release, rather than storing
every solution. Their ordering is deterministic.

`catalog_sha256` binds the canonical names, catalog and root constraints as
sorted compact JSON. Equivalent constraint spellings may produce different
digests. It is an input binding, not a signature. The map does not call the
resolver search, but it shares input parsing and Exhaustive Audit's edge
checker. Shared defects remain possible. Enumeration is exponential; the
candidate budget does not bound parsing time, memory, output size or wall time.
Witness storage can grow with releases times reachable packages. No platform,
interpreter, artifact, security, availability or installability claim is made.

Checks run:

```sh
python3 -B -m unittest discover -s line-4/tools/release-map -p 'test_*.py' -v
```

Ten tests passed, including 200 seeded three-package catalogs compared against
a separate enumeration loop, cycles, unreachable and missing dependencies,
branch-dependent absence, exact budget edges, sound partial witnesses,
canonicalization, input immutability, validation and the real metadata example.
The comparison loop shares numeric constraint parsing; it is local evidence,
not independent certification.
