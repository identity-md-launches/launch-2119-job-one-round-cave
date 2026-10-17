#!/usr/bin/env python3
"""Find literal phrases across source lines in a bounded offline collection."""
import argparse
from array import array
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location('phrase_engine', Path(__file__).absolute().parents[1] / 'evidence-search' / 'search.py')
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)
MAX_OUTPUT_BYTES = 1_000_000


def normalize(text, ignore_case=False):
    """Collapse Unicode whitespace and map each output character to a source line."""
    chars, lines = [], array('I')
    line = 1
    space = False
    for char in text:
        if char.isspace():
            if chars and not space:
                chars.append(' ')
                lines.append(line)
            space = True
        else:
            folded = char.casefold() if ignore_case else char
            chars.append(folded)
            lines.extend([line] * len(folded))
            space = False
        if char == '\n':
            line += 1
    if chars and chars[-1] == ' ':
        chars.pop()
        lines.pop()
    return ''.join(chars), lines


def find(index, phrase, limit=10, ignore_case=False):
    engine.validate_index(index)
    if not isinstance(phrase, str) or not 1 <= len(phrase) <= 4096:
        raise engine.SearchError('phrase must have 1 to 4096 characters')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise engine.SearchError('limit must be an integer between 1 and 50')
    if type(ignore_case) is not bool:
        raise engine.SearchError('ignore_case must be boolean')
    needle, _ = normalize(phrase, ignore_case)
    if not needle or '\x00' in needle:
        raise engine.SearchError('phrase must contain non-whitespace text without NUL')
    hits = []
    truncated = False
    output_bytes = 0
    for doc in sorted(index['documents'], key=lambda d: d['path']):
        text, line_map = normalize(doc['text'], ignore_case)
        source = engine.source_lines(doc['text'])
        offset = 0
        while True:
            at = text.find(needle, offset)
            if at < 0:
                break
            if len(hits) == limit:
                truncated = True
                break
            start, end = line_map[at], line_map[at + len(needle) - 1]
            excerpt = '\n'.join(source[start - 1:end])
            output_bytes += len(excerpt.encode('utf-8'))
            if output_bytes > MAX_OUTPUT_BYTES:
                raise engine.SearchError('excerpt byte budget exceeded; reduce limit or narrow phrase')
            hits.append({'path': doc['path'], 'line_start': start, 'line_end': end,
                         'citation': f"{doc['path']}:{start}-{end}",
                         'sha256': doc['sha256'], 'text': excerpt,
                         'source_verified': False,
                         'normalized_offset': at})
            offset = at + len(needle)  # Deliberately non-overlapping occurrences.
        if truncated:
            break
    return {'format': 'exact-phrase-results/v1', 'phrase': phrase,
            'normalized_phrase': needle, 'ignore_case': ignore_case,
            'indexed_documents': len(index['documents']),
            'limit': limit, 'truncated': truncated, 'hits': hits}


def scan(root, phrase, limit=10, ignore_case=False):
    root = engine.workspace_path(root)
    result = find(engine.build_index(root), phrase, limit, ignore_case)
    verified = set()
    for hit in result['hits']:
        if hit['path'] not in verified:
            raw = engine.read_bytes(engine.workspace_path(root / hit['path']), engine.MAX_FILE_BYTES)
            if engine.digest(raw) != hit['sha256']:
                raise engine.SearchError('stale source; retry with a static collection')
            verified.add(hit['path'])
        hit['source_verified'] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for name, arg in [('scan', 'root'), ('snapshot', 'index')]:
        p = subs.add_parser(name)
        p.add_argument(arg)
        p.add_argument('phrase')
        p.add_argument('--limit', type=int, default=10)
        p.add_argument('--ignore-case', action='store_true')
    subs.add_parser('demo')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            root = Path(__file__).absolute().parents[1] / 'evidence-search' / 'examples' / 'docs'
            result = scan(root, 'Zero To One')
        elif args.command == 'scan':
            result = scan(args.root, args.phrase, args.limit, args.ignore_case)
        else:
            result = find(engine.load_index(args.index), args.phrase, args.limit, args.ignore_case)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['hits'] else 1
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
