import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('phrases', Path(__file__).with_name('phrases.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def index(**docs):
    return {'format': p.engine.FORMAT, 'documents': [
        {'path': name, 'text': text, 'sha256': p.engine.digest(text.encode())}
        for name, text in docs.items()]}


class PhraseTests(unittest.TestCase):
    def test_boundary_and_exact_excerpt(self):
        text = 'irrelevant\r\n' * 9 + 'Zero\r\n\r\nTo\tOne.\r\n'
        hit = p.find(index(**{'zto.md': text}), 'Zero To One')['hits'][0]
        self.assertEqual((hit['line_start'], hit['line_end']), (10, 12))
        self.assertEqual(hit['text'], 'Zero\n\nTo\tOne.')
        self.assertFalse(hit['source_verified'])

    def test_literal_order_and_punctuation(self):
        data = index(**{'a.md': 'One To Zero\nZero, To One\nZero To One'})
        self.assertEqual(p.find(data, 'Zero To One')['hits'][0]['line_start'], 3)
        self.assertFalse(p.find(data, 'Zero To Two')['hits'])

    def test_unicode_casefold_offsets(self):
        data = index(**{'a.md': 'Straße\nCAFÉ\u2003frog'})
        hit = p.find(data, 'STRASSE café', ignore_case=True)['hits'][0]
        self.assertEqual(hit['citation'], 'a.md:1-2')
        self.assertFalse(p.find(data, 'STRASSE')['hits'])

    def test_no_implicit_unicode_composition(self):
        self.assertFalse(p.find(index(**{'a.md': 'e\u0301'}), 'é')['hits'])

    def test_order_truncation_and_nonoverlap(self):
        data = index(**{'z.md': 'aa', 'a.md': 'aaaa'})
        result = p.find(data, 'aa', limit=2)
        self.assertTrue(result['truncated'])
        self.assertEqual([h['normalized_offset'] for h in result['hits']], [0, 2])
        self.assertEqual({h['path'] for h in result['hits']}, {'a.md'})
        self.assertFalse(p.find(index(**{'a.md': 'aaaa'}), 'aa', limit=2)['truncated'])

    def test_immutable(self):
        data = index(**{'a.md': 'Zero To One'})
        before = copy.deepcopy(data)
        p.find(data, 'One')
        self.assertEqual(data, before)

    def test_invalid_requests(self):
        for phrase in ['', ' \n\t', 'x' * 4097, '\x00', None]:
            with self.assertRaises(p.engine.SearchError):
                p.find(index(), phrase)
        for limit in [0, 51, True, 1.5]:
            with self.assertRaises(p.engine.SearchError):
                p.find(index(), 'x', limit)
        with self.assertRaises(p.engine.SearchError):
            p.find(index(), 'x', ignore_case=1)

    def test_forged_unselected_document(self):
        data = index(**{'a.md': 'x', 'b.md': 'unrelated'})
        data['documents'][1]['text'] = 'altered'
        with self.assertRaises(p.engine.SearchError):
            p.find(data, 'x')

    def test_output_budget(self):
        with patch.object(p, 'MAX_OUTPUT_BYTES', 3):
            with self.assertRaises(p.engine.SearchError):
                p.find(index(**{'a.md': 'long source'}), 'source')

    def test_live_and_stale(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            root = Path(temp)
            source = root / 'a.md'
            source.write_text('Zero To One')
            self.assertTrue(p.scan(root, 'Zero')['hits'][0]['source_verified'])
            old = p.engine.read_bytes
            def changed(path, cap):
                raw = old(path, cap)
                if changed.calls:
                    return b'changed'
                changed.calls += 1
                return raw
            changed.calls = 0
            with patch.object(p.engine, 'read_bytes', changed):
                with self.assertRaises(p.engine.SearchError):
                    p.scan(root, 'Zero')
            source.unlink()
            source.symlink_to('missing.md')
            self.assertFalse(p.scan(root, 'Zero')['hits'])

    def test_cli_and_historical_demo(self):
        script = str(Path(p.__file__))
        demo = subprocess.run([sys.executable, '-B', script, 'demo'], capture_output=True, text=True)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertEqual(json.loads(demo.stdout)['hits'][0]['citation'], 'zto.md:3-3')
        root = str(Path(script).parents[1] / 'evidence-search/examples/docs')
        for phrase, status in [('absent phrase', 1), ('   ', 2)]:
            run = subprocess.run([sys.executable, '-B', script, 'scan', root, phrase], capture_output=True, text=True)
            self.assertEqual(run.returncode, status)
            if status == 2:
                self.assertEqual(run.stdout, '')


if __name__ == '__main__':
    unittest.main()
