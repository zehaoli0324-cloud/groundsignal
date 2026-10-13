"""Run with the isolated build environment's Python to produce a shareable ZIP."""
from importlib import metadata
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
from runtime_paths import VERSION


def main():
    if sys.platform != 'win32':
        raise SystemExit('Windows builds must run on Windows')
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
                    '--name', 'GroundSignal', '--paths', str(ROOT/'scripts'),
                    '--add-data', str(ROOT/'templates/collector.html')+';templates',
                    '--distpath', str(ROOT/'release/windows'), '--workpath', str(ROOT/'build/pyinstaller'),
                    '--specpath', str(ROOT/'build'), str(ROOT/'launch-collector.pyw')], check=True, cwd=ROOT)
    output = ROOT/'release/windows/GroundSignal'
    shutil.copy2(ROOT/'packaging/测试版使用说明.txt', output/'先读我.txt')
    licenses = output/'第三方许可'
    licenses.mkdir(exist_ok=True)
    versions = {}
    for package in ['requests', 'beautifulsoup4', 'soupsieve', 'certifi', 'urllib3', 'idna',
                    'charset-normalizer', 'typing-extensions', 'PyYAML', 'pyinstaller']:
        dist = metadata.distribution(package)
        versions[package] = dist.version
        for file in dist.files or []:
            if any(word in file.name.lower() for word in ['license', 'copying', 'notice']) and file.suffix not in {'.py', '.pyc'}:
                source = Path(dist.locate_file(file))
                if source.is_file():
                    shutil.copy2(source, licenses/(package+'-'+file.name))
    # Python's license is bundled by PyInstaller; Tcl/Tk licenses are in their data directories.
    (output/'build-info.json').write_text(json.dumps({'version': VERSION, 'python': sys.version,
                                                   'dependencies': versions}, indent=2), encoding='utf-8')
    archive = shutil.make_archive(str(ROOT/'release'/f'GroundSignal-{VERSION}-windows-x64'), 'zip',
                                  root_dir=output.parent, base_dir=output.name)
    digest = hashlib.sha256(Path(archive).read_bytes()).hexdigest()
    Path(archive+'.sha256').write_text(digest+'  '+Path(archive).name+'\n', encoding='utf-8')
    print(json.dumps({'zip': archive, 'bytes': Path(archive).stat().st_size, 'sha256': digest}, indent=2))


if __name__ == '__main__':
    main()
