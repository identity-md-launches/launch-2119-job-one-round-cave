#!/usr/bin/env python3
"""Deduplicate verified Ethereum witness nodes; standard library, offline only."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('witness_for_pack', HERE.parent / 'state-witness' / 'witness.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
MAX_PACK = 1_000_000


def node_lists(bundle):
    proof = bundle['proof']
    yield proof, 'accountProof'
    for entry in proof['storageProof']:
        yield entry, 'proof'


def serialized(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def pack(bundle, root, address, slots):
    """Verify before compacting. Only proof-node lists are replaced with integer indices."""
    w.require(isinstance(bundle, dict) and bundle.get('format') == 'state-witness/1',
              'unsupported witness format')
    w.require(len(serialized(bundle)) <= MAX_PACK, 'witness exceeds size bound')
    state = w.verify(bundle.get('proof'), root, address, slots)
    compact, nodes, indexes = copy.deepcopy(bundle), [], {}
    for owner, field in node_lists(compact):
        refs = []
        for value in owner[field]:
            raw = w.hex_data(value)
            canonical = w.hex0(raw)
            if canonical not in indexes:
                indexes[canonical] = len(nodes)
                nodes.append(canonical)
            refs.append(indexes[canonical])
        owner[field] = refs
    result = {'format': 'proof-pack/1', 'nodes': nodes, 'witness': compact}
    w.require(len(serialized(result)) <= MAX_PACK, 'packed output exceeds size bound')
    restored, checked = unpack(result, root, address, slots)
    w.require(checked == state, 'roundtrip state mismatch')
    return result, state


def unpack(packed, root, address, slots):
    """Resolve bounded integer references, then verify all expanded proofs."""
    w.require(isinstance(packed, dict) and set(packed) == {'format', 'nodes', 'witness'}
              and packed['format'] == 'proof-pack/1', 'unsupported pack structure')
    w.require(len(serialized(packed)) <= MAX_PACK, 'pack exceeds size bound')
    nodes = packed['nodes']
    w.require(isinstance(nodes, list) and len(nodes) <= 8320, 'invalid node dictionary')
    unique = set()
    for value in nodes:
        raw = w.hex_data(value, label='node bytes')
        w.require(0 < len(raw) <= 32768, 'node size outside bounds')
        w.require(value == w.hex0(raw) and value not in unique,
                  'duplicate node or noncanonical encoding')
        unique.add(value)
    bundle = copy.deepcopy(packed['witness'])
    w.require(isinstance(bundle, dict) and bundle.get('format') == 'state-witness/1',
              'unsupported embedded witness')
    proof = bundle.get('proof')
    w.require(isinstance(proof, dict) and isinstance(proof.get('storageProof'), list)
              and len(proof['storageProof']) <= 64, 'invalid embedded proof')
    w.require(all(isinstance(entry, dict) for entry in proof['storageProof']), 'invalid storage entry')
    used = set()
    expanded_bytes = 0
    for owner, field in node_lists(bundle):
        refs = owner.get(field)
        w.require(isinstance(refs, list) and len(refs) <= 128, 'invalid node reference list')
        expanded = []
        for ref in refs:
            w.require(type(ref) is int and 0 <= ref < len(nodes), 'missing node reference')
            used.add(ref)
            expanded_bytes += len(nodes[ref])
            w.require(expanded_bytes <= MAX_PACK, 'expanded node bytes exceed size bound')
            expanded.append(nodes[ref])
        owner[field] = expanded
    w.require(used == set(range(len(nodes))), 'unused dictionary node')
    w.require(len(serialized(bundle)) <= MAX_PACK, 'expanded witness exceeds size bound')
    state = w.verify(proof, root, address, slots)
    return bundle, state


def load(path):
    with w.workspace_path(path).open('rb') as stream:
        raw = stream.read(MAX_PACK + 1)
    w.require(len(raw) <= MAX_PACK, 'input exceeds size bound')
    return w.parse_json(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo')
    demo.add_argument('--pool', action='store_true')
    for command in ('pack', 'unpack', 'verify'):
        p = sub.add_parser(command)
        p.add_argument('input')
        p.add_argument('--state-root', required=True)
        p.add_argument('--address', required=True)
        p.add_argument('--slot', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            name = 'zto-pool-mainnet.json' if args.pool else 'zto-mainnet.json'
            bundle = w.load_bundle(HERE.parent / 'state-witness' / 'examples' / name)
            address = w.POOL_MANAGER if args.pool else w.ZTO
            slots = [w.hex0(w.keccak256(w.hex_data(w.ZTO_POOL_ID, 32) + (6).to_bytes(32, 'big')))] if args.pool else ['0x0', '0x1']
            packed, state = pack(bundle, w.DEMO_ROOT, address, slots)
            expanded, checked = unpack(packed, w.DEMO_ROOT, address, slots)
            occurrences = sum(len(owner[field]) for owner, field in node_lists(bundle))
            output = {'format': 'proof-pack-demo/1', 'verified': state == checked,
                      'nodeOccurrences': occurrences, 'uniqueNodes': len(packed['nodes']),
                      'originalCompactJsonBytes': len(serialized(bundle)),
                      'packedCompactJsonBytes': len(serialized(packed)), 'state': state,
                      'demo': 'Historical real RPC observation; demo root is not a consensus-authenticated checkpoint.'}
        else:
            value = load(args.input)
            if args.command == 'pack':
                output, _ = pack(value, args.state_root, args.address, args.slot)
            else:
                bundle, state = unpack(value, args.state_root, args.address, args.slot)
                output = bundle if args.command == 'unpack' else state
        print(json.dumps(output, sort_keys=True, separators=(',', ':')))
        return 0
    except (w.Invalid, OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Invalid, unreadable or unverified witness/pack.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
