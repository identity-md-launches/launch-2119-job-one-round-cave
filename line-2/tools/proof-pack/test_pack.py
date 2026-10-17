"""Offline real-chain roundtrip and adversarial serialization checks."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('pack', Path(__file__).with_name('pack.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
w = p.w


class ProofPack(unittest.TestCase):
    def setUp(self):
        self.bundle = w.load_bundle(p.HERE.parent / 'state-witness/examples/zto-mainnet.json')
        self.args = (w.DEMO_ROOT, w.ZTO, ['0x0', '0x1'])
        self.packed, self.state = p.pack(self.bundle, *self.args)

    def test_real_zto_lossless_smaller_and_immutable(self):
        before = copy.deepcopy(self.bundle)
        packed_before = copy.deepcopy(self.packed)
        bundle, state = p.unpack(self.packed, *self.args)
        self.assertEqual(bundle, self.bundle)
        self.assertEqual(state, self.state)
        self.assertEqual(self.bundle, before)
        self.assertEqual(self.packed, packed_before)
        self.assertLess(len(p.serialized(self.packed)), len(p.serialized(self.bundle)))
        self.assertEqual(len(self.packed['nodes']), 16)

    def test_real_pool_roundtrip(self):
        bundle = w.load_bundle(p.HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')
        args = (w.DEMO_ROOT, w.POOL_MANAGER, [entry['key'] for entry in bundle['proof']['storageProof']])
        packed, state = p.pack(bundle, *args)
        restored, checked = p.unpack(packed, *args)
        self.assertEqual(bundle, restored)
        self.assertEqual(state, checked)
        self.assertTrue(state['storage'][0]['exists'])

    def test_corrupt_node_rejected(self):
        self.packed['nodes'][0] = '0xc0'
        with self.assertRaises(w.Invalid):
            p.unpack(self.packed, *self.args)

    def test_wrong_reference_types_and_ranges(self):
        for ref in (True, False, -1, 10000, '0', None, [], {}):
            bad = copy.deepcopy(self.packed)
            bad['witness']['proof']['accountProof'][0] = ref
            with self.subTest(ref=ref), self.assertRaises(w.Invalid):
                p.unpack(bad, *self.args)

    def test_retargeted_reference_rejected(self):
        self.packed['witness']['proof']['accountProof'][0] = 1
        with self.assertRaises(w.Invalid):
            p.unpack(self.packed, *self.args)

    def test_duplicate_unused_noncanonical_dictionary(self):
        for mode in ('duplicate', 'unused', 'uppercase', 'nothex'):
            bad = copy.deepcopy(self.packed)
            if mode == 'duplicate':
                bad['nodes'].append(bad['nodes'][0])
            elif mode == 'unused':
                bad['nodes'].append('0xc0')
            elif mode == 'uppercase':
                bad['nodes'][0] = '0x' + bad['nodes'][0][2:].upper()
            else:
                bad['nodes'][0] = 'hello'
            with self.subTest(mode=mode), self.assertRaises(w.Invalid):
                p.unpack(bad, *self.args)

    def test_caller_root_address_and_slot_binding(self):
        for args in ((self.bundle['proof']['storageHash'], w.ZTO, ['0x0', '0x1']),
                     (w.DEMO_ROOT, w.POOL_MANAGER, ['0x0', '0x1']),
                     (w.DEMO_ROOT, w.ZTO, ['0x0'])):
            with self.subTest(args=args), self.assertRaises(w.Invalid):
                p.unpack(self.packed, *args)

    def test_corrupt_claim_never_packed(self):
        self.bundle['proof']['storageProof'][0]['value'] = '0x1'
        with self.assertRaises(w.Invalid):
            p.pack(self.bundle, *self.args)

    def test_embedded_metadata_does_not_anchor(self):
        self.packed['witness']['block']['stateRoot'] = self.bundle['proof']['storageHash']
        _, state = p.unpack(self.packed, *self.args)
        self.assertEqual(state, self.state)

    def test_structure_and_bounds(self):
        variants = [None, [], {}, dict(self.packed, extra=1), dict(self.packed, nodes={}),
                    dict(self.packed, format='proof-pack/2')]
        for bad in variants:
            with self.subTest(bad=type(bad)), self.assertRaises(w.Invalid):
                p.unpack(bad, *self.args)
        bad = copy.deepcopy(self.packed)
        bad['witness']['proof']['accountProof'] = [0] * 129
        with self.assertRaises(w.Invalid):
            p.unpack(bad, *self.args)

    def test_expansion_budget_before_verification(self):
        bad = copy.deepcopy(self.packed)
        bad['nodes'] = [w.hex0(w.rlp_encode([b'x' * 16000]))]
        bad['witness']['proof']['accountProof'] = [0] * 128
        with self.assertRaisesRegex(w.Invalid, 'expanded node bytes'):
            p.unpack(bad, *self.args)

    def test_strict_json(self):
        for raw in ('{"nodes":[],"nodes":[]}', '{"a":NaN}'):
            with self.assertRaises(w.Invalid):
                w.parse_json(raw)

    def test_workspace_boundary(self):
        with self.assertRaises(w.Invalid):
            w.workspace_path(Path.cwd().parent / 'outside-proof.json')

    def test_cli_failure_has_no_success_output(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = p.main(['verify', 'line-2/tools/state-witness/examples/zto-mainnet.json',
                           '--state-root', w.DEMO_ROOT, '--address', w.ZTO])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(json.loads(err.getvalue())['verified'])

    def test_empty_trie_and_empty_dictionary(self):
        proof = {'address': w.ZTO, 'nonce': '0x0', 'balance': '0x0',
                 'storageHash': w.hex0(w.EMPTY_TRIE), 'codeHash': w.hex0(w.EMPTY_CODE),
                 'accountProof': [], 'storageProof': []}
        bundle = {'format': 'state-witness/1', 'proof': proof}
        args = (w.hex0(w.EMPTY_TRIE), w.ZTO, [])
        packed, state = p.pack(bundle, *args)
        self.assertEqual(packed['nodes'], [])
        self.assertFalse(state['accountExists'])
        self.assertEqual(p.unpack(packed, *args)[0], bundle)


if __name__ == '__main__':
    unittest.main()
