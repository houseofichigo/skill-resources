#!/usr/bin/env python3
"""Build an allowlisted, unpublished skills snapshot; never writes to Git."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--product', required=True, type=Path)
parser.add_argument('--audit-script', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
root = args.product.resolve()
out = args.output.resolve()
if out.exists():
    raise SystemExit('Output exists; use a new candidate directory to preserve prior versions.')
catalog = json.loads((root / 'skills/catalog.json').read_text())
names = sorted(s['name'] for s in catalog['skills'])
files = {}
reports = []
patterns = {
    'personal-path': r'/Users/|/home/[^/\s]+/',
    'private-service': r'myn8n|webhook/[a-zA-Z0-9-]+',
    'private-context': r'Sabri|Learn AI|Climate House',
    'email-address': r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}',
}
for name in names:
    if not re.fullmatch(r'hoi-[a-z0-9-]+', name):
        raise SystemExit('Invalid skill identity')
    folder = root / 'skills' / name
    result = subprocess.run([sys.executable, str(args.audit_script), str(folder),
                             '--target', 'all', '--json'], capture_output=True, text=True)
    report = json.loads(result.stdout)
    if report['finding_counts']['blocker']:
        raise SystemExit(f'Static audit blockers in {name}')
    reports.append({'skill': name, 'status': report['status'],
                    'counts': report['finding_counts'], 'findings': report['findings']})
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise SystemExit('Symlinks are excluded')
        if not path.is_file():
            continue
        data = path.read_bytes()
        text = data.decode('utf-8')
        for label, pattern in patterns.items():
            if re.search(pattern, text, re.I):
                raise SystemExit(f'{label} requires review in {name}/{path.name}; content withheld')
        files[f'skills/{name}/{path.relative_to(folder).as_posix()}'] = data
for name in ('catalog.json', 'contracts.json', 'presentation.json'):
    files[f'skills/{name}'] = (root / 'skills' / name).read_bytes()
files['LICENSE'] = (root / 'LICENSE').read_bytes()
files['README.md'] = (Path(__file__).resolve().parent.parent / 'community-docs/README.md').read_bytes()
digest = lambda data: hashlib.sha256(data).hexdigest()
source_hashes = {name: digest(data) for name, data in sorted(files.items()) if name.startswith('skills/')}
engine_hashes = {}
for base in ('src', 'scripts'):
    for path in sorted((root / base).rglob('*')):
        if path.is_file() and not path.is_symlink():
            engine_hashes[path.relative_to(root).as_posix()] = digest(path.read_bytes())
for name in ('package.json', 'package-lock.json'):
    engine_hashes[name] = digest((root / name).read_bytes())
manifest = {'status': 'unpublished-local-candidate', 'skillCount': len(names),
            'compatibility': catalog['compatibility'],
            'baseVersion': catalog['version'], 'skillChecksums': source_hashes,
            'engineSnapshotChecksums': engine_hashes,
            'limitations': ['Not a standalone engine distribution', 'No live host verification']}
files['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
files['VALIDATION.json'] = (json.dumps({'skills': reports,
    'privacyScan': 'No selected private-pattern matches in skill files',
    'allowedAttribution': ['MIT copyright notice', 'public upstream links', 'stable HOI OS identifiers'],
    'limitations': ['Heuristic static scan; not a guarantee of absence of confidential content',
                    'No fresh runtime, clean-install or live-provider checks in this build']}, indent=2) + '\n').encode()
out.mkdir(parents=True)
for name, data in files.items():
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
def archive(path, contents):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
(out / 'individual').mkdir()
for name in names:
    selected = {key.removeprefix('skills/'): data for key, data in files.items()
                if key.startswith(f'skills/{name}/')}
    selected[f'{name}/LICENSE'] = files['LICENSE']
    archive(out / 'individual' / f'{name}.zip', selected)
archive(out / 'hoi-os-community-skills.zip', files)
checksums = [f'{digest(p.read_bytes())}  {p.relative_to(out).as_posix()}'
             for p in sorted(out.rglob('*')) if p.is_file()]
(out / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n')
print(json.dumps({'skills': len(names), 'staticBlockers': 0,
                  'warnings': sum(r['counts']['warning'] for r in reports),
                  'filesVerified': len(checksums), 'status': 'unpublished'}))
