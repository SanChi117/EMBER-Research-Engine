#!/usr/bin/env python3
"""Portable C05 unit suite; legacy tests are patched only in ephemeral mirror.

Never rewrites evidence-bound tests in original append-only C04 archive.
"""
from __future__ import annotations
import os, pathlib, shutil, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
ORIGINAL="ENGINE=Path('/mnt/data/MTF_ROUTE_LAB_V05_LIFECYCLE_REPAIR_20261014/src/mtf_engine.py')"
LOCAL="ENGINE=Path(__file__).resolve().parents[1]/'baselines'/'mtf_engine_v05_original.py'"

def main():
    with tempfile.TemporaryDirectory(prefix='mtf_d02_compat_') as td:
        dst=pathlib.Path(td)
        shutil.copytree(ROOT/'tests',dst/'tests',ignore=shutil.ignore_patterns('__pycache__'))
        (dst/'tools').symlink_to(ROOT/'tools',target_is_directory=True)
        (dst/'baselines').symlink_to(ROOT/'baselines',target_is_directory=True)
        for fn in ('test_foundation_adversarial.py','test_foundation_adversarial_v2.py'):
            p=dst/'tests'/fn;s=p.read_text(encoding='utf8')
            if ORIGINAL not in s:raise RuntimeError('legacy fixture changed unexpectedly: '+fn)
            s=s.replace(ORIGINAL,LOCAL)
            if fn=='test_foundation_adversarial.py':
                s=s.replace('import csv,hashlib,importlib.util,json,math,os,tempfile',
                            'import csv,hashlib,importlib.util,json,math,os,tempfile,sys')
                s=s.replace('engine=importlib.util.module_from_spec(sp);sp.loader.exec_module(engine)',
                            'engine=importlib.util.module_from_spec(sp);sys.modules[sp.name]=engine;sp.loader.exec_module(engine)')
            p.write_text(s,encoding='utf8')
        cp=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(dst/'tests'),'-v'],
                          text=True,capture_output=True,cwd=dst)
        print(cp.stdout,end='');print(cp.stderr,end='',file=sys.stderr)
        return cp.returncode
if __name__=='__main__':raise SystemExit(main())
