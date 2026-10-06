"""Resolve npm's Windows command shim for CodeForge's structured process runner."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('task', choices=['typecheck', 'build'])
args = parser.parse_args()
npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
if not npm:
    parser.error('npm is required for web verification')
sys.exit(subprocess.call([npm, 'run', args.task], cwd=Path(__file__).resolve().parents[1] / 'apps/web'))
