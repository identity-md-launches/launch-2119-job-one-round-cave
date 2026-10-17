import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import merge_choices as tool


class MergeChoicesTests(unittest.TestCase):
    def test_historical_catalog_and_witnesses(self):
        result = tool.demo()
        self.assertEqual(result['status'], 'mapped')
        choices = result['choices']
        packages, roots = tool.release_map.fmt.validate(tool.first.parse(result['merge']['merged']))
        for p, versions in choices['releases'].items():
            for v, row in versions.items():
                if row['status'] == 'viable':
                    witness = choices['witnesses'][row['witness']]
                    self.assertEqual(witness[p], v)
                    self.assertEqual(tool.release_map.checker.assignment(packages, roots, witness), witness)
        self.assertEqual(choices['releases']['requests']['2.31.0']['status'], 'excluded')
        self.assertGreater(choices['compatible_selections_found'], 1)

    def test_exact_budget_and_unknown_not_excluded(self):
        count = tool.demo()['choices']['checked_assignments']
        self.assertEqual(tool.demo(count)['status'], 'mapped')
        limited = tool.demo(count - 1)
        self.assertEqual(limited['status'], 'inconclusive')
        self.assertTrue(all(row['status'] != 'excluded'
                            for versions in limited['choices']['releases'].values()
                            for row in versions.values()))

    def test_actual_merged_catalog_not_either_branch(self):
        folder = tool.first.HERE / 'examples'
        texts = [(folder / f'{n}.json').read_text() for n in ('base', 'ours', 'theirs')]
        for text in texts:
            self.assertEqual(tool.check(text, text, text)['status'], 'mapped')
        result = tool.check(*texts)
        self.assertTrue(result['merge']['clean'])
        self.assertEqual(result['status'], 'incompatible')
        self.assertEqual(result['choices']['compatible_selections_found'], 0)
        self.assertEqual(result['choices']['witnesses'], [])

    def test_text_conflict_short_circuits(self):
        with patch.object(tool.release_map, 'release_map', side_effect=AssertionError):
            result = tool.check('base\n', 'ours\n', 'theirs\n')
        self.assertEqual(result['status'], 'text_conflict')
        self.assertIsNone(result['choices'])

    def test_invalid_catalog_and_budget(self):
        for text in ('{}', '{"roots":{},"roots":{}}', 'NaN', '[]'):
            self.assertEqual(tool.check(text, text, text)['status'], 'invalid_catalog')
        for budget in (True, 0, -1, 1000001):
            with self.assertRaises(ValueError):
                tool.demo(budget)

    def test_deterministic_and_no_solver_search(self):
        with patch.object(tool.release_map.fmt, 'solve', side_effect=AssertionError):
            self.assertEqual(tool.demo(), tool.demo())

    def test_portable_cli_inputs_unchanged(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            folder = Path(temp) / 'portable'
            shutil.copytree(Path(__file__).parent, folder)
            before = {p: p.read_bytes() for p in folder.rglob('*') if p.is_file()}
            command = [sys.executable, '-B', str(folder / 'merge_choices.py')]
            for args, code, status in [(['demo'], 0, 'mapped'),
                    (['demo', '--max-assignments', '1'], 3, 'inconclusive'),
                    (['check', *[str(folder / 'examples' / f'{n}.json')
                                 for n in ('base', 'ours', 'theirs')]], 1, 'incompatible')]:
                proc = subprocess.run(command + args, capture_output=True, text=True)
                self.assertEqual(proc.returncode, code, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)['status'], status)
            self.assertEqual(before, {p: p.read_bytes() for p in folder.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
