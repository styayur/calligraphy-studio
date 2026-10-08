"""Provision or reuse the private Android release identity and GitHub secrets.

Run locally on Windows with keytool and authenticated gh. No private material is
written under the repository. The recovery file and keystore must be backed up
offline by the release owner after provisioning.
"""
import base64
import json
import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path


def restricted_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        sid = subprocess.check_output(
            ['whoami', '/user', '/fo', 'csv', '/nh'], text=True
        ).strip().split(',')[-1].strip('"')
        subprocess.run(
            ['icacls', str(path), '/inheritance:r', '/grant:r',
             f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'],
            check=True, capture_output=True, text=True,
        )


def gh_secret(name: str, value: str) -> None:
    subprocess.run(['gh', 'secret', 'set', name], input=value, text=True,
                   check=True, capture_output=True)


def main() -> None:
    if os.name != 'nt':
        raise SystemExit('Provision on the release owner Windows host.')
    primary = Path(os.environ['LOCALAPPDATA']) / 'CalligraphyStudio' / 'release-signing'
    backup = Path.home() / 'Documents' / 'CalligraphyStudio-Private-Backup' / 'android'
    restricted_directory(primary)
    restricted_directory(backup)
    key = primary / 'calligraphy-studio-release.jks'
    recovery = primary / 'android-recovery.json'
    alias = 'calligraphy-studio-release'
    if key.exists() != recovery.exists():
        raise SystemExit('Incomplete existing identity; inspect private storage before retrying.')
    if recovery.exists():
        credentials = json.loads(recovery.read_text(encoding='utf-8'))
    else:
        credentials = {
            'alias': alias,
            'store_password': secrets.token_urlsafe(48),
            'key_password': secrets.token_urlsafe(48),
        }
        environment = os.environ.copy()
        environment['CALLIGRAPHY_STORE_PASS'] = credentials['store_password']
        environment['CALLIGRAPHY_KEY_PASS'] = credentials['key_password']
        subprocess.run([
            'keytool', '-genkeypair', '-keystore', str(key), '-storetype', 'JKS',
            '-alias', alias, '-keyalg', 'RSA', '-keysize', '4096',
            '-validity', '10000', '-dname', 'CN=Calligraphy Studio Android Release',
            '-storepass:env', 'CALLIGRAPHY_STORE_PASS',
            '-keypass:env', 'CALLIGRAPHY_KEY_PASS', '-noprompt',
        ], env=environment, check=True, capture_output=True, text=True)
        recovery.write_text(json.dumps(credentials, indent=2) + '\n', encoding='utf-8')
    environment = os.environ.copy()
    environment['CALLIGRAPHY_STORE_PASS'] = credentials['store_password']
    listing = subprocess.run([
        'keytool', '-list', '-v', '-keystore', str(key),
        '-alias', credentials['alias'], '-storepass:env', 'CALLIGRAPHY_STORE_PASS',
    ], env=environment, check=True, capture_output=True, text=True).stdout
    match = re.search(r'SHA256:\s*([0-9A-F:]{95})', listing, re.I)
    if not match:
        raise SystemExit('Cannot read signing certificate SHA-256 from keytool.')
    fingerprint = match.group(1).upper()
    shutil.copy2(key, backup / key.name)
    shutil.copy2(recovery, backup / recovery.name)
    gh_secret('ANDROID_KEYSTORE_BASE64', base64.b64encode(key.read_bytes()).decode('ascii'))
    gh_secret('ANDROID_STORE_PASSWORD', credentials['store_password'])
    gh_secret('ANDROID_KEY_ALIAS', credentials['alias'])
    gh_secret('ANDROID_KEY_PASSWORD', credentials['key_password'])
    subprocess.run(['gh', 'variable', 'set', 'ANDROID_CERT_SHA256', '--body', fingerprint],
                   check=True, capture_output=True, text=True)
    print(f'Android release signing configured; certificate SHA-256: {fingerprint}')
    print(f'Private keystore: {key}')
    print(f'Private local backup: {backup}')
    print('Keep an additional encrypted offline copy of the backup for disaster recovery.')


if __name__ == '__main__':
    main()
