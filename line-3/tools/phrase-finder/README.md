# Exact Phrase Finder

Find a literal phrase in an unfamiliar offline UTF-8 collection, including a
phrase split across lines or the ranker's ten-line passage boundary. Each
occurrence has an exact relative path, inclusive line citation, original source
SHA-256 and complete source-line excerpt. Python 3.9+ standard library only;
keep the adjacent `evidence-search/` tool. No installation or network required.

From the repository root, one command shows it working without writing files:

```sh
python3 -B line-3/tools/phrase-finder/phrases.py demo
```

When tried, it returned `zto.md:3-3`, `ZTO token name: Zero To One.`, with
`source_verified: true`. This uses the inherited historical ZTO-first document,
not a fresh chain observation, price or independent factual verification.

Search your own collection inside the current workspace:

```sh
python3 -B line-3/tools/phrase-finder/phrases.py scan line-3/tools/evidence-search/examples/docs 'Zero To One' --limit 10
```

Or search a saved Evidence Search index, without reading its original files:

```sh
python3 -B line-3/tools/phrase-finder/phrases.py snapshot line-3/my-index.json 'your exact phrase' --ignore-case
```

The latter path must refer to an index you actually saved. Snapshot mode validates
all embedded source hashes and always returns `source_verified: false`. Scan
mode builds an in-memory index and re-reads every selected source before emitting
any output. Changes abort the result. Keep the workspace static: checks are not
atomic and do not defend against concurrent replacement of filesystem paths.
Only returned sources are rechecked. All paths must stay inside the current
working directory, without symlinks or parent traversal. Hidden entries and
symlinks in a corpus are skipped by the inherited indexer.

Matching is literal, case sensitive by default, with each Unicode whitespace run
collapsed to one ASCII space and leading/trailing whitespace removed. Punctuation
and word order matter. `--ignore-case` applies Unicode case folding (so `Straße`
can match `STRASSE`); no Unicode composition, accent removal, stemming, token
boundary restriction, synonym expansion or semantic matching is performed.
A match may be a substring of a word or a case-fold expansion. This is normalized
phrase equality, not exact byte equality. Excerpts retain original line content
with CRLF rendered as LF. Only LF establishes a new source line.

Results are ordered by path then occurrence, rather than relevance. Occurrences
are non-overlapping within each document. Distinct occurrences can share a line
citation; `normalized_offset` distinguishes their zero-based character offsets
in that document's normalized text. `truncated: true` means at least one more
non-overlapping occurrence was found after the limit. A false value means the
whole validated snapshot was searched without an omitted occurrence under these
rules. Missing matches do not establish absence of semantically related evidence.

Limits: 1–4,096 phrase characters, 1–50 occurrences, and 1 MB of UTF-8 excerpt
bytes in aggregate; exceeding the excerpt budget produces an error without a
partial report. Corpus limits inherit Evidence Search: 1,000 `.md`/`.txt`/`.rst`
files, 1 MB per file, 8 MB total, 16 MB saved index, 16,000 characters per line.
Scan also inherits the 20,000-passage index-build cap. Source text is inert data;
consumers must display it as text rather than execute it. Hashes bind source
bytes, not truth, authority or present-day chain state.

JSON goes to stdout; errors go to stderr. Exit status is 0 with matches, 1 with
no matches, and 2 for invalid input, exceeded budgets or I/O errors.

Eleven behavioral tests passed:

```sh
python3 -B line-3/tools/phrase-finder/test_phrases.py -v
```

They exercise cross-passage CRLF citations, blank lines, punctuation and order,
Unicode expansion and composition, deterministic order, overlapping occurrences,
truncation, immutable input, invalid requests, forged unselected sources, output
budgets, live stale-source rejection, symlink exclusion and CLI statuses.
Temporary files live only in `test/scratch/`. No older tool was modified.
