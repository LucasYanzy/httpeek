#!/usr/bin/env python3
"""Dependency-free checks for the committed repository presentation.

This catches common publication mistakes, not every possible private datum.
History identities and package archives are audited separately before release.
"""
from pathlib import Path
import re,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=['README.md','README.zh-CN.md','LICENSE','CONTRIBUTING.md','PRIVACY.md','SECURITY.md',
          'assets/logo.svg','assets/demo.png','assets/demo.gif','assets/social-preview.png',
          'demo/terminal.txt','scripts/demo.py','.github/workflows/ci.yml']
errors=[]
for name in REQUIRED:
    if not (ROOT/name).is_file() or (ROOT/name).stat().st_size == 0:errors.append(name+': required file missing or empty')
for name in ['README.md','README.zh-CN.md']:
    if not (ROOT/name).exists():continue
    text=(ROOT/name).read_text()
    for target in re.findall(r'\]\(([^)]+)\)|(?:src|href)="([^"]+)"',text):
        link=next((v for v in target if v),'').split('#',1)[0].split('?',1)[0]
        if not link or re.match(r'[a-z]+://|mailto:',link):continue
        if not (ROOT/link).exists():errors.append(name+': broken local link '+link)
    if '```mermaid' not in text:errors.append(name+': missing architecture diagram')
paths=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-co','--exclude-standard','-z']).decode().split('\0')
for rel in set(paths):
    f=ROOT/rel
    if not rel or not f.is_file():continue
    try:text=f.read_text()
    except (UnicodeError,OSError):continue
    # Match complete home directories, not generic /path/to/project examples.
    for label,pattern in [
        ('personal absolute path',r'/' + r'Users/[^/\s"\x27]+|[A-Za-z]:\\Users\\[^\\\s]+'),
        ('personal email',r'[\w.+-]+@(?:outlook|gmail|hotmail|yahoo|qq|163)\.[A-Za-z]+'),
        ('placeholder repository',r'github\.com/(?:your[-_]?(?:org|user|name)|diffblast/diffblast|httpeek/httpeek)(?:[/\s"\x27]|$)'),
    ]:
        for i,line in enumerate(text.splitlines(),1):
            if re.search(pattern,line):errors.append(rel+':'+str(i)+': '+label)
    if f.name in {'.env','.env.local','cookies.json','history.jsonl'}:
        # Deliberately synthetic scanner fixtures are kept out of distributed packages.
        if not rel.startswith(('test/fixtures/','demo/fixtures/')):errors.append(rel+': local state must not be published')
card=ROOT/'assets/social-preview.png'
if card.exists():
    data=card.read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',data[16:24])!=(1280,640):errors.append('social preview must be 1280x640 PNG')
if errors:
    print('\n'.join(errors));sys.exit(1)
print('Publication checks passed: required files, README links, preview size and common personal-data patterns.')
