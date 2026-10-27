"""Exercise the upload entrypoint with local stand-ins for Arch and rclone tools."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]

# Run the real entrypoint, sync.py, and upload.py without an Arch installation or
# network credentials. Database archives contain the fields consumed by sync.py.
FAKE_TOOL = r'''#!/usr/bin/env python3
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile

tool = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['COMMAND_LOG'], 'a') as log:
    log.write(json.dumps([tool, *args]) + '\n')

if tool == 'repo-add':
    args = [arg for arg in args if not arg.startswith('--')]
    db = Path(args[0])
    entries = {}
    if db.exists():
        with tarfile.open(db) as archive:
            entries = {m.name: archive.extractfile(m).read() for m in archive}
    for package in args[1:]:
        name = Path(package).name
        pkgname, version, release, arch = name.split('.pkg.tar.')[0].rsplit('-', 3)
        desc = f'%FILENAME%\n{name}\n%NAME%\n{pkgname}\n%VERSION%\n{version}-{release}\n'
        entries[f'{pkgname}-{version}-{release}/desc'] = desc.encode()
    with tarfile.open(db, 'w:gz') as archive:
        for name, data in entries.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    db.with_name(db.name.replace('.db.', '.files.')).write_bytes(db.read_bytes())
elif tool == 'gpg':
    if '--detach-sig' in args:
        Path(args[-1] + '.sig').write_text('new signature')
elif tool == 'rclone':
    remote = Path(os.environ['FAKE_REMOTE'])
    if args[0] == 'size':
        sys.exit(0 if (remote / args[1].rsplit('/', 1)[-1]).exists() else 3)
    if args[0] == 'copy':
        source = remote / args[1].rsplit('/', 1)[-1]
        if not source.exists():
            sys.exit(3)
        shutil.copy2(source, Path(args[2]) / source.name)
    elif args[0] == 'sync':
        for child in remote.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        shutil.copytree(Path(args[1]), remote, dirs_exist_ok=True)
'''


class RepositoryUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        shutil.copytree(ROOT / 'create-db-and-upload-action',
                        self.workspace / 'create-db-and-upload-action')
        (self.workspace / 'static').mkdir()
        (self.workspace / 'static' / 'key.asc').write_text('public key')
        self.artifacts = self.workspace / 'artifacts'
        self.artifacts.mkdir()
        self.remote = self.root / 'remote'
        self.remote.mkdir()
        self.log = self.root / 'commands.jsonl'
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        for name in ('repo-add', 'gpg', 'rclone'):
            executable = bin_dir / name
            executable.write_text(FAKE_TOOL)
            executable.chmod(0o755)
        # Only version comparison is external to the upload code under test.
        (bin_dir / 'pyalpm.py').write_text(
            'def vercmp(a, b):\n    return (a > b) - (a < b)\n')
        self.repo_name = self.root.name
        self.addCleanup((Path('/tmp') / f'{self.repo_name}.db.tar.gz').unlink,
                        missing_ok=True)
        self.env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}',
                        PYTHONPATH=str(bin_dir), HOME=str(self.root / 'home'),
                        RCLONE_CONFIG_NAME='test', RCLONE_CONFIG_CONTENT='',
                        dest_path='repo', repo_name=self.repo_name, gpg_key='test key',
                        local_path=str(self.artifacts), COMMAND_LOG=str(self.log),
                        FAKE_REMOTE=str(self.remote))
        self.env.pop('REBUILD', None)

    def seed_repository(self):
        (self.artifacts / 'updated-2-1-any.pkg.tar.zst').write_text('new package')
        for name in ('updated-1-1-any', 'retired-1-1-any', 'dependency-1-1-any'):
            package = self.remote / f'{name}.pkg.tar.zst'
            package.write_text(name)
            if not name.startswith('dependency'):
                Path(str(package) + '.sig').write_text('existing signature')
        subprocess.run(['repo-add', f'{self.repo_name}.db.tar.gz',
                        *sorted(p.name for p in self.remote.glob('*.zst'))],
                       cwd=self.remote, env=self.env, check=True)
        self.log.unlink()
        (self.remote / 'obsolete-static.txt').write_text('obsolete')

    def run_upload(self, rebuild=False):
        env = self.env | ({'REBUILD': 'true'} if rebuild else {})
        return subprocess.run(['bash', str(ROOT / 'create-db-and-upload-action/entrypoint.sh')],
                              cwd=self.workspace, env=env, capture_output=True, text=True)

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def database_packages(self):
        with tarfile.open(self.remote / f'{self.repo_name}.db.tar.gz') as archive:
            return {archive.extractfile(member).read().decode().splitlines()[1]
                    for member in archive}

    def test_regular_upload_merges_remote_packages_and_reuses_signatures(self):
        self.seed_repository()
        result = self.run_upload()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        expected = {'updated-2-1-any.pkg.tar.zst', 'retired-1-1-any.pkg.tar.zst',
                    'dependency-1-1-any.pkg.tar.zst'}
        self.assertEqual(self.database_packages(), expected)
        self.assertEqual((self.remote / 'retired-1-1-any.pkg.tar.zst.sig').read_text(),
                         'existing signature')
        self.assertEqual((self.remote / 'dependency-1-1-any.pkg.tar.zst.sig').read_text(),
                         'new signature')
        self.assertFalse((self.remote / 'updated-1-1-any.pkg.tar.zst').exists())
        self.assertTrue(any(c[:2] == ['rclone', 'copy'] for c in self.commands()))

    def test_rebuild_keeps_only_build_artifacts_and_static_files(self):
        self.seed_repository()
        (self.artifacts / 'split-1-1-any.pkg.tar.zst').write_text('split package')
        result = self.run_upload(rebuild=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        expected = {'updated-2-1-any.pkg.tar.zst', 'split-1-1-any.pkg.tar.zst'}
        self.assertEqual(self.database_packages(), expected)
        self.assertEqual({p.name for p in self.remote.glob('*.pkg.*')},
                         expected | {p + '.sig' for p in expected})
        self.assertEqual((self.remote / 'key.asc').read_text(), 'public key')
        self.assertFalse((self.remote / 'obsolete-static.txt').exists())
        rclone_commands = [c for c in self.commands() if c[0] == 'rclone']
        self.assertEqual(rclone_commands,
                         [['rclone', 'sync', './', 'test:/repo', '-c', '--copy-links']])

    def test_unsigned_rebuild_still_generates_database(self):
        self.seed_repository()
        self.env['gpg_key'] = ''
        result = self.run_upload(rebuild=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.database_packages(), {'updated-2-1-any.pkg.tar.zst'})
        self.assertFalse(list(self.remote.glob('*.sig')))

    def test_empty_rebuild_does_not_touch_remote(self):
        (self.remote / 'keep.txt').write_text('keep')
        # Signatures alone must not count as built packages.
        (self.artifacts / 'missing-1-1-any.pkg.tar.zst.sig').write_text('signature')
        result = self.run_upload(rebuild=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No built package files found for rebuild', result.stderr)
        self.assertEqual((self.remote / 'keep.txt').read_text(), 'keep')
        self.assertFalse(self.log.exists())


if __name__ == '__main__':
    unittest.main()
