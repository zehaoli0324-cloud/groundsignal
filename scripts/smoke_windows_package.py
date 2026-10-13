"""Exercise the built EXE with no Python on PATH and isolated test settings."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time

import requests

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path, default=ROOT/'release/windows/GroundSignal/GroundSignal.exe')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(dir=ROOT/'build', prefix='package-check-') as work:
        work = Path(work)
        env = os.environ.copy()
        for key in ['PYTHONPATH', 'PYTHONHOME', 'TCL_LIBRARY', 'TK_LIBRARY']:
            env.pop(key, None)
        env['PATH'] = str(Path(env.get('SystemRoot', r'C:\Windows'))/'System32')
        env['GROUNDSIGNAL_DATA_DIR'] = str(work/'profile')
        flags = subprocess.CREATE_NO_WINDOW
        diagnostic = work/'diagnostic.json'
        subprocess.run([str(args.exe), '--diagnose', str(diagnostic)], env=env, cwd=work,
                       creationflags=flags, timeout=30, check=True)
        info = json.loads(diagnostic.read_text(encoding='utf-8'))
        assert info['frozen'] and info['template'] and info['tk']
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        session = requests.Session()
        session.trust_env = False
        vault = work/'测试笔记库'
        (vault/'.obsidian').mkdir(parents=True)
        for attempt in range(2):
            proc = subprocess.Popen([str(args.exe), '--no-browser', '--port', str(port)], cwd=work,
                                    env=env, creationflags=flags)
            try:
                for _ in range(100):
                    try:
                        state = session.get(base+'/api/state', timeout=.4).json()
                        break
                    except requests.RequestException:
                        if proc.poll() is not None:
                            raise RuntimeError('EXE exited before HTTP startup')
                        time.sleep(.1)
                else:
                    raise RuntimeError('EXE did not start in time')
                assert state['settings']['connected'] == bool(attempt)
                assert state['settings']['vault'] == (str(vault) if attempt else '')
                page = session.get(base, timeout=3).text
                assert '连接 Obsidian' in page
                token = re.search("const token='([^']+)'", page).group(1)
                headers = {'X-GroundSignal-Token': token}
                response = session.post(base+'/api/settings', headers=headers,
                                        json={'vault': str(vault), 'max_results': 3}, timeout=3)
                response.raise_for_status()
                state = session.get(base+'/api/state', timeout=3).json()
                assert state['settings']['connected']
                assert state['history'] == []
                assert not list(vault.glob('.groundsignal-check-*'))
                session.post(base+'/api/shutdown', headers=headers, json={}, timeout=3).raise_for_status()
                proc.wait(timeout=5)
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)
        session.close()
        report = {'passed': True, 'version': info['version'], 'checks': [
            'frozen executable without Python PATH', 'bundled Tcl/Tk', 'bundled HTML',
            'first launch disconnected', 'connect/write probe', 'settings persist after restart',
            'HTTP startup/shutdown'], 'clean_machine_test': False}
        (ROOT/'release/package-smoke-test.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
