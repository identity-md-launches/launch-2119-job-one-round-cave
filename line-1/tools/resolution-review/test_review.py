"""Offline filesystem integration tests; disposable data lives in test/scratch."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('resolution_review', HERE / 'review.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.inputs = [self.root / side for side in m.tree.SIDES]
        for folder, text in zip(self.inputs, ('base', 'ours', 'theirs')):
            folder.mkdir()
            (folder / 'guide.txt').write_bytes(('first\r\n' + text + '\r\n').encode())
            (folder / 'clean.txt').write_bytes(b'unchanged\n')
        self.packet = self.root / 'packet.json'
        self.decisions = self.root / 'decisions.json'
        self.receipt = self.root / 'receipt.json'
        self.staged = self.root / 'staged'
        self.choices = {'guide.txt': {'candidate': 'first\r\nours and theirs\r\n',
                                      'reason': 'Keep both contributions.'}}
        self.prepare()

    def prepare(self):
        self.packet.write_text(json.dumps(m.tree.from_directories(self.inputs)), encoding='utf-8')
        self.packet_hash = hashlib.sha256(self.packet.read_bytes()).hexdigest()
        self.decisions.write_text(json.dumps({
            'schema': 'conflict-finish/v1', 'packet_sha256': self.packet_hash,
            'decisions': self.choices}), encoding='utf-8')

    def stage(self):
        self.value = m.finish.finish(self.packet, self.inputs, self.decisions,
                                     self.staged, self.packet_hash)
        self.pin_receipt()

    def pin_receipt(self):
        self.receipt.write_text(json.dumps(self.value), encoding='utf-8')
        self.receipt_hash = hashlib.sha256(self.receipt.read_bytes()).hexdigest()

    def review(self, **changes):
        args = dict(packet_path=self.packet, inputs=self.inputs, decisions_path=self.decisions,
                    receipt_path=self.receipt, staged_path=self.staged,
                    packet_sha256=self.packet_hash, receipt_sha256=self.receipt_hash)
        args.update(changes)
        return m.review(**args)

    def cli(self, pin=None):
        return subprocess.run([
            sys.executable, '-B', str(HERE / 'review.py'), str(self.packet),
            *map(str, self.inputs), str(self.decisions), str(self.receipt), str(self.staged),
            '--packet-sha256', self.packet_hash,
            '--receipt-sha256', pin or self.receipt_hash], capture_output=True, text=True)

    def test_combined_choice_shows_both_diffs_without_writes(self):
        self.stage()
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.review()
        self.assertTrue(result['matches'])
        self.assertEqual(result['status'], 'matches')
        chosen = result['resolutions'][0]
        self.assertEqual(chosen['reason'], 'Keep both contributions.')
        self.assertIn('-ours\r\n', chosen['against']['ours']['diff'])
        self.assertIn('+ours and theirs\r\n', chosen['against']['theirs']['diff'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_one_side_choice_exposes_other_side_loss(self):
        self.choices['guide.txt']['candidate'] = 'first\r\nours\r\n'
        self.prepare()
        self.stage()
        chosen = self.review()['resolutions'][0]
        self.assertTrue(chosen['against']['ours']['identical'])
        self.assertFalse(chosen['against']['theirs']['identical'])
        self.assertIn('-theirs\r\n', chosen['against']['theirs']['diff'])

    def test_empty_file_is_different_from_delete(self):
        self.choices['guide.txt']['candidate'] = ''
        self.prepare()
        self.stage()
        chosen = self.review()['resolutions'][0]
        self.assertEqual(chosen['selected']['kind'], 'file')
        self.assertEqual(chosen['selected']['bytes'], 0)
        (self.staged / 'guide.txt').unlink()
        result = self.review()
        self.assertEqual(result['status'], 'stage-drift')
        self.assertEqual(result['stage_diffs'][0]['diff'], '')
        self.assertEqual(result['stage_diffs'][0]['after']['kind'], 'missing')

    def test_delete_modify_choice_and_missing_side(self):
        (self.inputs[2] / 'guide.txt').unlink()
        self.choices['guide.txt']['candidate'] = None
        self.prepare()
        self.stage()
        chosen = self.review()['resolutions'][0]
        self.assertEqual(chosen['original_status'], 'delete-modify-conflict')
        self.assertEqual(chosen['selected'], {'kind': 'missing'})
        self.assertTrue(chosen['against']['theirs']['identical'])
        self.assertIn('-ours\r\n', chosen['against']['ours']['diff'])

    def test_file_directory_conflict_is_explicit(self):
        path = self.inputs[2] / 'guide.txt'
        path.unlink()
        path.mkdir()
        (path / 'child.txt').write_text('child\n')
        self.choices['guide.txt']['candidate'] = None
        self.choices['guide.txt/child.txt'] = {'candidate': 'child\n', 'reason': 'Keep nested file.'}
        self.prepare()
        self.stage()
        result = self.review()
        self.assertTrue(result['matches'])
        chosen = result['resolutions'][0]
        self.assertEqual(chosen['selected']['kind'], 'directory')
        self.assertEqual(chosen['against']['ours']['before']['kind'], 'file')

    def test_drift_on_clean_paths_and_directories(self):
        self.stage()
        (self.staged / 'clean.txt').write_text('dropped original\n')
        (self.staged / 'new.txt').write_text('new\n')
        (self.staged / 'empty').mkdir()
        result = self.review()
        self.assertFalse(result['matches'])
        self.assertEqual([x['path'] for x in result['stage_diffs']], ['clean.txt', 'new.txt'])
        self.assertIn('-unchanged\n', result['stage_diffs'][0]['diff'])
        self.assertEqual(result['stage_audit']['added_directories'], ['empty'])

    def test_stale_inputs_stop_before_staged_read(self):
        self.stage()
        (self.inputs[1] / 'clean.txt').write_text('later edit\n')
        result = self.review(staged_path=self.root / 'does-not-exist')
        self.assertEqual(result['status'], 'stale-inputs')
        self.assertEqual(result['source_recheck']['changed_inputs'], ['ours'])
        self.assertNotIn('resolutions', result)

    def test_rehashed_altered_packet_is_not_accepted(self):
        report = json.loads(self.packet.read_text())
        report['files'][0]['candidate'] = 'forged'
        self.packet.write_text(json.dumps(report))
        self.packet_hash = hashlib.sha256(self.packet.read_bytes()).hexdigest()
        # Build a real receipt first, then rebind it and the decisions to the altered packet.
        altered = self.packet.read_bytes()
        self.prepare()
        self.stage()
        self.packet.write_bytes(altered)
        self.packet_hash = hashlib.sha256(altered).hexdigest()
        choices = json.loads(self.decisions.read_text())
        choices['packet_sha256'] = self.packet_hash
        self.decisions.write_text(json.dumps(choices))
        self.value['packet_sha256'] = self.packet_hash
        self.value['decisions_sha256'] = hashlib.sha256(self.decisions.read_bytes()).hexdigest()
        self.pin_receipt()
        self.assertEqual(self.review()['status'], 'review-mismatch')

    def test_rehashed_receipt_cannot_change_reason_or_omission(self):
        self.stage()
        original = copy.deepcopy(self.value)
        for field in ('resolutions', 'omitted'):
            self.value = copy.deepcopy(original)
            if field == 'resolutions':
                self.value[field]['guide.txt']['reason'] = 'A different reason'
            else:
                self.value[field] = ['clean.txt']
            self.pin_receipt()
            result = self.review()
            self.assertEqual(result['status'], 'receipt-mismatch')
            self.assertEqual(result['receipt_recheck']['changed_fields'], [field])

    def test_forged_self_consistent_output_manifest_is_rejected(self):
        self.stage()
        bogus = m.file_tree({'guide.txt': 'replacement\n', 'clean.txt': 'unchanged\n'})
        self.value['files'] = {name: {k: v for k, v in m.tree.fingerprint(text).items() if k != 'kind'}
                               for name, text in bogus['files'].items()}
        self.value['manifest'] = m.tree.manifest(bogus)
        self.pin_receipt()
        result = self.review()
        self.assertEqual(result['status'], 'receipt-mismatch')
        self.assertEqual(result['receipt_recheck']['changed_fields'], ['manifest', 'files'])

    def test_decision_and_pin_binding(self):
        self.stage()
        wrong = hashlib.sha256(b'other retained bytes').hexdigest()
        for kwargs in ({'packet_sha256': wrong}, {'receipt_sha256': wrong}):
            with self.assertRaises(ValueError):
                self.review(**kwargs)
        self.decisions.write_bytes(self.decisions.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'decision bytes'):
            self.review()

    def test_unterminated_unicode_and_terminal_controls(self):
        self.choices['guide.txt'] = {'candidate': 'café\x1b[31m', 'reason': 'Reason\x1b[0m'}
        self.prepare()
        self.stage()
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('\x1b', result.stdout)
        data = json.loads(result.stdout)
        self.assertIn('No newline at end of file', data['resolutions'][0]['against']['ours']['diff'])

    def test_symlinks_binary_and_outside_paths_rejected(self):
        self.stage()
        link = self.root / 'link'
        link.symlink_to(self.staged, target_is_directory=True)
        for path in (link, Path('/'), self.staged / '..' / 'staged'):
            with self.assertRaises(ValueError):
                self.review(staged_path=path)
        for data in (b'\x00', b'\xff', b'x' * (m.tree.review.engine.MAX_BYTES + 1)):
            (self.staged / 'guide.txt').write_bytes(data)
            with self.assertRaises(ValueError):
                self.review()

    def test_malformed_duplicate_receipt_and_wrong_packet_binding(self):
        self.stage()
        self.value['packet_sha256'] = hashlib.sha256(b'unrelated packet').hexdigest()
        self.pin_receipt()
        with self.assertRaisesRegex(ValueError, 'different packet'):
            self.review()
        self.receipt.write_bytes(b'{"schema":1,"schema":2}')
        self.receipt_hash = hashlib.sha256(self.receipt.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.review()

    def test_output_metadata_not_followed(self):
        self.stage()
        self.value['output'] = '/not/a/workspace/path'
        self.pin_receipt()
        self.assertTrue(self.review()['matches'])

    def test_cli_statuses_and_read_only_demo(self):
        self.stage()
        self.assertEqual(self.cli().returncode, 0)
        (self.staged / 'guide.txt').unlink()
        drift = self.cli()
        self.assertEqual(drift.returncode, 1, drift.stderr)
        self.assertEqual(json.loads(drift.stdout)['status'], 'stage-drift')
        error = self.cli(hashlib.sha256(b'wrong receipt pin').hexdigest())
        self.assertEqual(error.returncode, 2)
        self.assertEqual(error.stdout, '')
        demo = subprocess.run([sys.executable, '-B', str(HERE / 'review.py'), '--demo'],
                              capture_output=True, text=True)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertEqual(json.loads(demo.stdout)['schema'], 'resolution-review-demo/v1')


if __name__ == '__main__':
    unittest.main()
