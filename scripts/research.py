#!/usr/bin/env python3
"""GroundSignal bounded search, capture, candidate extraction and frozen comparison."""
import argparse
import json
from pathlib import Path
import sys

from industry_search.contracts import REPO, config_check, read_json, target_check, write_json
from industry_search.evaluation import compare
from industry_search.pipeline import execute, fresh_directory, load_run, replay
from industry_search.planning import plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('plan', 'run'):
        sub = commands.add_parser(name)
        sub.add_argument('--target', type=Path, required=True)
        sub.add_argument('--config', type=Path, default=REPO / 'config/search.default.json')
        sub.add_argument('--out', type=Path, required=True)
    demo = commands.add_parser('demo', help='Explicit synthetic fixture, zero network/model requests')
    demo.add_argument('--out', type=Path, required=True)
    for name in ('extract', 'compare'):
        sub = commands.add_parser(name)
        sub.add_argument('--run', type=Path, required=True)
        sub.add_argument('--config', type=Path, default=REPO / 'config/search.default.json')
        sub.add_argument('--out', type=Path, required=True)
        sub.add_argument('--fixture', type=Path, help='Only permitted for explicitly synthetic input')
        if name == 'compare':
            sub.add_argument('--gold', type=Path)
    validate = commands.add_parser('validate')
    validate.add_argument('--run', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'validate':
            run = load_run(args.run)
            print(json.dumps({'status': 'CONTRACT_VALID', 'run_id': run['id'],
                              'note': 'Structure and saved-text grounding only; not factual correctness.'}))
            return 0
        if args.command == 'demo':
            fixture = read_json(REPO / 'examples/search/synthetic.json')
            config = config_check(read_json(REPO / 'config/search.default.json'))
            run = execute(fixture['target'], config, args.out, fixture=fixture)
        else:
            config = config_check(read_json(args.config))
            if args.command == 'plan':
                target = target_check(read_json(args.target))
                out = fresh_directory(args.out)
                result = plan(target, config['budget'])
                write_json(out / 'plan.json', result)
                print(json.dumps({'status': 'PLAN_ONLY', 'queries': len(result['queries']), 'out': str(out)}))
                return 0
            if args.command == 'run':
                run = execute(target_check(read_json(args.target)), config, args.out)
            else:
                fixture = read_json(args.fixture) if args.fixture else None
                if args.command == 'extract':
                    run = replay(args.run, config, args.out, fixture=fixture)
                else:
                    result = compare(args.run, config, args.out,
                                     labels=read_json(args.gold) if args.gold else None, fixture=fixture)
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return 0
        print(json.dumps({'status': run['status'], 'counts': run['counts'],
                          'out': str(args.out), 'handoff': run['handoff'],
                          'note': '所有候选待审核；SYNTHETIC_ONLY 仅验证工程逻辑'}, ensure_ascii=False, indent=2))
        return 2 if run['status'] == 'NO_USABLE_DOCUMENTS' else 0
    except (ValueError, OSError, KeyError) as exc:
        # Exceptions contain only local contract/error codes; never requests URL/header dumps.
        print('研究管线停止：' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
