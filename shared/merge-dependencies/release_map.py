#!/usr/bin/env python3
"""Map finite-catalog releases to complete compatible selection witnesses."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys


CHECKER = Path(__file__).resolve().parent / 'exhaustive.py'
if not CHECKER.is_relative_to(Path.cwd().resolve()):
    raise RuntimeError('run from the workspace containing the tools')
spec = importlib.util.spec_from_file_location('release_map_checker', CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
fmt = checker.fmt


def release_map(data, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise fmt.Invalid('max_assignments must be an integer from 1 to 1000000')
    packages, roots = fmt.validate(data)
    digest = hashlib.sha256(json.dumps({'packages': packages, 'roots': roots},
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    possible, todo = set(), list(roots)
    while todo:
        p = todo.pop()
        if p in possible:
            continue
        possible.add(p)
        for deps in packages.get(p, {}).values():
            todo.extend(deps)
    names = sorted(possible)
    domains, total = [], 1
    for p in names:
        versions = sorted(packages.get(p, {}), key=fmt.version)
        domain = ([v for v in versions if checker.matches(v, roots[p])]
                  if p in roots else [None] + versions)
        domains.append(domain)
        total *= len(domain)
    rows = {p: {v: {'status': 'unknown'} for v in sorted(releases, key=fmt.version)}
            for p, releases in sorted(packages.items())}
    witnesses, checked, solutions = [], 0, 0
    for values in itertools.product(*domains):
        if checked == max_assignments:
            break
        checked += 1
        supplied = {p: v for p, v in zip(names, values) if v is not None}
        reached = checker.assignment(packages, roots, supplied)
        # Require absent values for unreachable packages. This prevents counting
        # the same solution several times through irrelevant release choices.
        if reached is None or reached != supplied:
            continue
        solutions += 1
        newly_seen = [(p, v) for p, v in reached.items()
                      if rows[p][v]['status'] == 'unknown']
        if newly_seen:
            index = len(witnesses)
            witnesses.append(reached)
            for p, v in newly_seen:
                rows[p][v] = {'status': 'viable', 'witness': index}
    complete = checked == total
    if complete:
        for versions in rows.values():
            for row in versions.values():
                if row['status'] == 'unknown':
                    row['status'] = 'excluded'
    result = {'method': 'finite-release-map-v1', 'status': 'complete' if complete else 'inconclusive',
              'catalog_sha256': digest, 'max_assignments': max_assignments,
              'candidate_assignments': total, 'checked_assignments': checked,
              'compatible_selections_found': solutions,
              'missing_possible_packages': sorted(possible - packages.keys()),
              'releases': rows, 'witnesses': witnesses}
    if not complete:
        result['reason'] = 'assignment budget exhausted; unknown releases may still be viable'
    return result


