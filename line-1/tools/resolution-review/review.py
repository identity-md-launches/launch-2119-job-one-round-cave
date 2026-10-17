#!/usr/bin/env python3
"""Reproduce conflict choices and show what each contributor loses or retains."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys


def sibling(name, filename):
    path = Path(__file__).resolve().parents[1] / name / filename
    spec = importlib.util.spec_from_file_location('resolution_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


finish = sibling('conflict-finish', 'finish.py')
audit = sibling('stage-audit', 'audit.py')
r = finish.r
tree = r.tree
LIMITS = [
    'Reproduction is not approval, author authentication or semantic correctness.',
    'Diffs expose textual changes; they do not prove preservation of intent.',
    'Retain packet and receipt hashes independently of their supplier.',
    'Stable trusted workspace required; no atomic snapshot or race protection.',
    'Bounded UTF-8 trees only; no permissions, binary merges or rename inference.',
    'Read-only; receipt output metadata is never used as a filesystem path.']


def file_tree(files):
    directories = {p.as_posix() for name in files
                   for p in PurePosixPath(name).parents if p.as_posix() != '.'}
    return {'files': files, 'directories': directories}


def state(snapshot, name):
    if name in snapshot['files']:
        return tree.fingerprint(snapshot['files'][name])
    return {'kind': 'directory' if name in snapshot['directories'] else 'missing'}


def difference(before, after, name, label):
    """State transitions distinguish an empty file, absence and a directory."""
    left, right = state(before, name), state(after, name)
    return {
        'before': left, 'after': right, 'identical': left == right,
        'diff': tree.review.unified(before['files'].get(name, ''),
                                    after['files'].get(name, ''), label, 'SELECTED')}


def resolution_details(current, sources, selected, resolutions):
    entries = []
    for entry in current['files']:
        name = entry['path']
        if name not in resolutions:
            continue
        entries.append({
            'path': name, 'original_status': entry['status'],
            'reason': resolutions[name]['reason'], 'selected': state(selected, name),
            'against': {side: difference(source, selected, name, side.upper())
                        for side, source in zip(tree.SIDES, sources)}})
    return entries


def review(packet_path, inputs, decisions_path, receipt_path, staged_path,
           packet_sha256, receipt_sha256):
    """All path reads are explicit, bounded, and confined to the current workspace."""
    if len(inputs) != 3:
        raise ValueError('exactly three source trees are required')
    audit.digest(packet_sha256)
    audit.digest(receipt_sha256)
    saved, packet_hash = r.load_packet(packet_path, packet_sha256)
    receipt, receipt_hash = audit.load_receipt(receipt_path, receipt_sha256)
    if receipt['schema'] != 'conflict-finish-receipt/v1':
        raise ValueError('requires a Conflict Finish receipt')
    if receipt['packet_sha256'] != packet_hash:
        raise ValueError('receipt is bound to a different packet')
    decisions, decisions_hash = finish.read_decisions(decisions_path, packet_hash)
    if decisions_hash != receipt['decisions_sha256']:
        raise ValueError('decision bytes differ from the pinned receipt')
    budget = [0]
    sources = [tree.snapshot(path, budget) for path in inputs]
    current = tree.combine(sources)
    check = r.compare(saved, current)
    result = {
        'schema': 'resolution-review/v1', 'matches': False,
        'status': check['status'], 'source_recheck': check,
        'packet_sha256': packet_hash, 'receipt_sha256': receipt_hash,
        'decisions_sha256': decisions_hash, 'limits': LIMITS}
    if not check['matches']:
        return result
    if current['clean']:
        raise ValueError('requires a conflicted review; use Stage Audit for clean exports')
    files, omitted, resolutions = finish.resolve(current, decisions)
    selected = file_tree({name: data.decode('utf-8') for name, data in files.items()})
    expected = {
        'manifest': tree.manifest(selected),
        'files': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(files.items())},
        'omitted': omitted, 'resolutions': resolutions}
    changed_fields = [key for key, value in expected.items()
                      if r.canonical(receipt.get(key)) != r.canonical(value)]
    result['receipt_recheck'] = {'matches': not changed_fields,
                                 'changed_fields': changed_fields}
    if changed_fields:
        result['status'] = 'receipt-mismatch'
        return result
    staged = tree.snapshot(staged_path, [0])
    stage_check = audit.compare(receipt, staged)
    result.update(
        matches=stage_check['matches'],
        status='matches' if stage_check['matches'] else 'stage-drift',
        stage_audit=stage_check,
        resolutions=resolution_details(current, sources, selected, resolutions))
    # Include drift on clean paths too, not just explicitly resolved conflicts.
    names = sorted(set(stage_check['added'] + stage_check['missing'] + stage_check['changed']))
    result['stage_diffs'] = []
    for name in names:
        change = difference(selected, staged, name, 'SELECTED')
        change['diff'] = tree.review.unified(selected['files'].get(name, ''),
                                             staged['files'].get(name, ''), 'SELECTED', 'STAGED')
        result['stage_diffs'].append({'path': name, **change})
    return result


def demo():
    """Small read-only preview; integration tests exercise real files and receipts."""
    sources = [file_tree({'guide.txt': text}) for text in (
        'Review optional.\n', 'Review required.\n', 'Retain a receipt.\n')]
    current = tree.combine(sources)
    files, _, resolutions = finish.resolve(current, {'guide.txt': {
        'candidate': 'Review required.\nRetain a receipt.\n',
        'reason': 'Keep both review and receipt requirements.'}})
    selected = file_tree({name: data.decode() for name, data in files.items()})
    return {'schema': 'resolution-review-demo/v1',
            'resolutions': resolution_details(current, sources, selected, resolutions),
            'limits': LIMITS, 'note': 'In-memory preview, not a verified filesystem receipt.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='PACKET BASE OURS THEIRS DECISIONS RECEIPT STAGED')
    parser.add_argument('--packet-sha256')
    parser.add_argument('--receipt-sha256')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args(argv)
    if args.demo:
        if args.paths or args.packet_sha256 or args.receipt_sha256:
            parser.error('--demo cannot be combined with inputs or hashes')
    elif len(args.paths) != 7 or not args.packet_sha256 or not args.receipt_sha256:
        parser.error('provide seven paths and both retained hashes, or --demo')
    try:
        result = demo() if args.demo else review(
            args.paths[0], args.paths[1:4], args.paths[4], args.paths[5], args.paths[6],
            args.packet_sha256, args.receipt_sha256)
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        print('resolution-review: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if args.demo or result['matches'] else 1


if __name__ == '__main__':
    sys.exit(main())
