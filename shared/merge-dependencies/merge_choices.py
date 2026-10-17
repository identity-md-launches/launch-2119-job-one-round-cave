#!/usr/bin/env python3
"""Review concurrent catalog edits and map every feasible merged release."""
import argparse
import json
import sys

import check_merge as first
import release_map


def check(base, ours, theirs, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise ValueError('assignment budget must be an integer from 1 to 1000000')
    packet = first.review.packet(base, ours, theirs)
    result = {'format': 'merged-release-choices/v1', 'status': 'text_conflict',
              'merge': packet, 'choices': None,
              'limits': [
                  'Read-only review; no root is removed or pin applied.',
                  'Witnesses establish compatibility only in the supplied finite catalog.',
                  'Unknown is not excluded when enumeration is incomplete.',
                  'No platform, artifact, security or installability claim.',
                  'Enumeration shares the inherited numeric parser and edge checker.']}
    if not packet['clean']:
        return result
    try:
        catalog = first.parse(packet['merged'])
        choices = release_map.release_map(catalog, max_assignments)
    except (ValueError, TypeError, RecursionError):
        result['status'] = 'invalid_catalog'
        return result
    result['choices'] = choices
    result['status'] = ('inconclusive' if choices['status'] != 'complete' else
                        'mapped' if choices['compatible_selections_found'] else
                        'incompatible')
    return result


def demo(max_assignments=10000):
    texts = [first.review.engine.read_text(first.HERE / 'examples' / f'plan-{n}.json')
             for n in ('base', 'ours', 'theirs')]
    return check(*texts, max_assignments=max_assignments)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('demo', 'check'):
        item = sub.add_parser(name)
        if name == 'check':
            for branch in ('base', 'ours', 'theirs'):
                item.add_argument(branch)
        item.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        result = demo(args.max_assignments) if args.command == 'demo' else check(
            *(first.review.engine.read_text(p) for p in (args.base, args.ours, args.theirs)),
            max_assignments=args.max_assignments)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return {'mapped': 0, 'text_conflict': 1, 'incompatible': 1,
                'invalid_catalog': 2, 'inconclusive': 3}[result['status']]
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({'status': 'invalid', 'error': 'Invalid workspace inputs or budget.'}),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
