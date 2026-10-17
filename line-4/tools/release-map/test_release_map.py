import copy
import importlib.util
import itertools
import random
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('release_map', Path(__file__).with_name('release_map.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def catalog(packages, roots=None):
    return {'packages': packages, 'roots': roots or {'app': '*'}}


class ReleaseMapTests(unittest.TestCase):
    def check_witnesses(self, data, result):
        packages, roots = m.fmt.validate(data)
        for p, versions in result['releases'].items():
            for v, row in versions.items():
                if row['status'] == 'viable':
                    witness = result['witnesses'][row['witness']]
                    self.assertEqual(witness[p], v)
                    self.assertEqual(m.checker.assignment(packages, roots, witness), witness)
                else:
                    self.assertNotIn('witness', row)

    def test_global_not_local_compatibility(self):
        data = catalog({'app': {'1': {'dep': '==1'}, '2': {'dep': '==2'}},
                        'dep': {'1': {}, '2': {}}}, {'app': '*', 'dep': '==1'})
        out = m.release_map(data)
        self.assertEqual(out['releases']['app']['2']['status'], 'excluded')
        self.assertEqual(out['compatible_selections_found'], 1)
        self.check_witnesses(data, out)

    def test_optional_branches_are_counted_once(self):
        data = catalog({'app': {'1': {}, '2': {'dep': '*'}}, 'dep': {'1': {}, '2': {}}})
        out = m.release_map(data)
        self.assertEqual(out['compatible_selections_found'], 3)
        self.assertEqual(out['checked_assignments'], 6)
        self.check_witnesses(data, out)

    def test_budget_preserves_positive_evidence(self):
        data = catalog({'app': {'1': {}, '2': {}, '3': {}}})
        out = m.release_map(data, 1)
        self.assertEqual(out['status'], 'inconclusive')
        self.assertEqual(out['releases']['app']['1']['status'], 'viable')
        self.assertEqual(out['releases']['app']['2']['status'], 'unknown')
        self.check_witnesses(data, out)
        self.assertEqual(m.release_map(data, 3)['status'], 'complete')

    def test_no_witness_before_exhaustion(self):
        data = catalog({'app': {'1': {'missing': '*'}, '2': {}}})
        out = m.release_map(data, 1)
        self.assertEqual(out['status'], 'inconclusive')
        self.assertEqual(out['compatible_selections_found'], 0)
        self.assertEqual(out['missing_possible_packages'], ['missing'])
        self.assertTrue(all(row['status'] == 'unknown' for row in out['releases']['app'].values()))
        self.assertEqual(m.release_map(data)['releases']['app']['1']['status'], 'excluded')

    def test_zero_domain_is_complete(self):
        out = m.release_map(catalog({'app': {'1': {}}}, {'app': '>2'}), 1)
        self.assertEqual((out['status'], out['candidate_assignments'], out['checked_assignments']),
                         ('complete', 0, 0))
        self.assertEqual(out['releases']['app']['1']['status'], 'excluded')

    def test_cycles_and_unreachable(self):
        data = catalog({'app': {'1': {'dep': '*'}}, 'dep': {'1': {'app': '*'}},
                        'unreachable': {'1': {}, '2': {}}})
        out = m.release_map(data)
        self.assertEqual(out['compatible_selections_found'], 1)
        self.assertEqual(out['releases']['unreachable']['1']['status'], 'excluded')
        self.check_witnesses(data, out)

    def test_aliases_and_input_immutability(self):
        data = catalog({'My_App': {'1.0': {}}}, {'my-app': '==1'})
        before = copy.deepcopy(data)
        out = m.release_map(data)
        self.assertEqual(out['releases']['my-app']['1.0']['status'], 'viable')
        self.assertEqual(data, before)
        alias = catalog({'my-app': {'1.0': {}}}, {'MY_APP': '==1'})
        self.assertEqual(out['catalog_sha256'], m.release_map(alias)['catalog_sha256'])

    def test_invalid_budget_and_catalog(self):
        for budget in (True, 0, -1, 1000001, '5', 1.0):
            with self.assertRaises(m.fmt.Invalid):
                m.release_map(catalog({'app': {'1': {}}}), budget)
        with self.assertRaises(m.fmt.Invalid):
            m.release_map(catalog({'app': {'1': {}, '1.0': {}}}))

    def test_seeded_independent_enumeration(self):
        rng = random.Random(2704)
        for _ in range(200):
            packages = {p: {v: {q: rng.choice(('*', '==1', '==2'))
                                   for q in ('app', 'b', 'c') if rng.random() < .3}
                            for v in ('1', '2') if rng.random() < .85}
                        for p in ('app', 'b', 'c')}
            data = catalog(packages)
            solutions = []
            names = sorted(packages)
            for values in itertools.product(*[[None] + list(packages[p]) for p in names]):
                selected = dict((p, v) for p, v in zip(names, values) if v is not None)
                if 'app' not in selected:
                    continue
                reached, todo, valid = set(), ['app'], True
                while todo and valid:
                    p = todo.pop()
                    if p in reached:
                        continue
                    reached.add(p)
                    for q, constraint in packages[p][selected[p]].items():
                        if q not in selected or not m.fmt.accepts(selected[q], constraint):
                            valid = False
                            break
                        todo.append(q)
                if valid and reached == set(selected):
                    solutions.append(selected)
            out = m.release_map(data)
            self.assertEqual(out['status'], 'complete')
            self.assertEqual(out['compatible_selections_found'], len(solutions))
            for p, versions in out['releases'].items():
                for v, row in versions.items():
                    expected = any(s.get(p) == v for s in solutions)
                    self.assertEqual(row['status'], 'viable' if expected else 'excluded')
            self.check_witnesses(data, out)

    def test_real_snapshot(self):
        data = m.fmt.load(Path(__file__).parent.parent / 'offline-resolver/examples/requests.json')
        out = m.release_map(data)
        self.assertEqual(out['checked_assignments'], 27)
        self.assertEqual(out['compatible_selections_found'], 8)
        self.assertEqual(out['releases']['urllib3']['2.5.0']['status'], 'excluded')
        self.assertEqual(out['releases']['requests']['2.32.5']['status'], 'viable')
        self.check_witnesses(data, out)


if __name__ == '__main__':
    unittest.main()
