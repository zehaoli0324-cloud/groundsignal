#!/usr/bin/env python3
"""Offline collection evaluation. score/compare exit 3 when quality gates are not ready."""
import argparse
import json
from pathlib import Path
import sys

from industry_search.benchmark import benchmark_check, draft_benchmark, evaluate, review_template, save_report
from industry_search.contracts import REPO, digest, read_json, write_json
from industry_search.pipeline import execute, fresh_directory, load_run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init-benchmark', help='Draft only: does not copy model candidates into gold')
    init.add_argument('--run', type=Path, required=True)
    init.add_argument('--out', type=Path, required=True)
    template = sub.add_parser('review-template', help='Hash-bound UNKNOWN permissions and empty candidate reviews')
    template.add_argument('--run', type=Path, required=True)
    template.add_argument('--benchmark', type=Path, required=True)
    template.add_argument('--out', type=Path, required=True)
    for name in ('score', 'compare'):
        p = sub.add_parser(name)
        p.add_argument('--run' if name == 'score' else '--runs', type=Path, required=True,
                       **({} if name == 'score' else {'nargs': '+'}))
        p.add_argument('--benchmark', type=Path, required=True)
        p.add_argument('--policy', type=Path, default=REPO / 'config/research-eval.default.json')
        p.add_argument('--reviews', type=Path, **({} if name == 'score' else {'nargs': '+'}),
                       help='For compare, one review file per run, in the same order; otherwise omit')
        p.add_argument('--allow-draft', action='store_true')
        p.add_argument('--out', type=Path, required=True)
    demo = sub.add_parser('demo', help='Explicit synthetic scoring demonstration, zero network/models')
    demo.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'init-benchmark':
            out = fresh_directory(args.out)
            result = draft_benchmark(load_run(args.run))
            benchmark_check(result)
            write_json(out / 'benchmark.json', result)
            print(json.dumps({'status': 'ANNOTATION_DRAFT', 'out': str(out),
                              'note': 'No gold claims or relevance judgments generated.'}))
            return 0
        if args.command == 'review-template':
            result = review_template(args.run, args.benchmark)
            out = fresh_directory(args.out)
            write_json(out / 'reviews.json', result)
            print(json.dumps({'status': 'REVIEW_REQUIRED', 'out': str(out)}))
            return 0
        if args.command == 'demo':
            out = fresh_directory(args.out)
            fixture = read_json(REPO / 'examples/search/synthetic.json')
            execute(fixture['target'], read_json(REPO / 'config/search.default.json'), out / 'run', fixture=fixture)
            result = evaluate(out / 'run/run.json', REPO / 'examples/search/eval-benchmark.synthetic.json',
                              REPO / 'config/research-eval.default.json')
            save_report(result, out / 'evaluation')
            print(json.dumps({'status': result['quality_status'], 'decision': result['decision'],
                              'out': str(out), 'note': 'Exit 0 tests engineering only; no real quality pass.'}))
            return 0
        if args.command == 'score':
            result = evaluate(args.run, args.benchmark, args.policy, args.reviews, args.allow_draft)
            save_report(result, args.out)
            print(json.dumps({'status': result['quality_status'], 'decision': result['decision'],
                              'out': str(args.out)}, ensure_ascii=False))
            return 0 if result['decision'] == 'REQUIRES_HUMAN_RELEASE' else 3
        paths = args.runs
        if args.reviews and len(args.reviews) != len(paths):
            raise ValueError('compare_requires_one_review_file_per_run')
        if len({p.resolve() for p in paths}) != len(paths):
            raise ValueError('duplicate_comparison_run')
        reviews = args.reviews or [None] * len(paths)
        reports = [evaluate(p, args.benchmark, args.policy, r, args.allow_draft) for p, r in zip(paths, reviews)]
        runs = [load_run(p) for p in paths]
        if len({r['id'] for r in runs}) != len(runs):
            raise ValueError('duplicate_comparison_run_id')
        out = fresh_directory(args.out)
        for i, report in enumerate(reports):
            save_report(report, out / ('run-' + str(i + 1)))
        comparison = {'schema_version': 'groundsignal.collection-comparison.v1',
                      'selection_status': 'NO_AUTOMATIC_WINNER',
                      'benchmark_sha256': reports[0]['benchmark_sha256'],
                      'same_budget': len({digest(r['config']['budget']) for r in runs}) == 1,
                      'same_frozen_input': len({r['frozen_input_sha256'] for r in runs}) == 1,
                      'results': [{'run_id': r['run_id'], 'run_sha256': r['run_sha256'],
                                   'quality_status': r['quality_status'], 'decision': r['decision'],
                                   'retrieval_recall': r['retrieval']['reference_recall_at_k'],
                                   'precision': r['extraction']['precision'],
                                   'end_to_end_recall': r['extraction']['end_to_end_reference_recall']}
                                  for r in reports],
                      'note': 'Same target and reference benchmark are enforced; unequal budgets or inputs are not a fair model-only comparison.'}
        write_json(out / 'comparison.json', comparison)
        print(json.dumps(comparison, ensure_ascii=False, indent=2))
        return 0 if all(r['decision'] == 'REQUIRES_HUMAN_RELEASE' for r in reports) else 3
    except (ValueError, OSError, KeyError) as exc:
        print('评测停止：' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
