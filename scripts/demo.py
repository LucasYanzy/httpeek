#!/usr/bin/env python3
"""Run the real CLI against synthetic data, without reading personal repositories.

Output can be saved with: python scripts/demo.py > demo/terminal.txt
Git fixture authors and data are fictional; no remote is configured.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'httpeek'

def call(args, cwd, env=None, expected=(0,)):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode not in expected:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout

def main():
    env = dict(os.environ, NO_COLOR='1', TERM='dumb', COLUMNS='100')
    env['PYTHONPATH'] = str(ROOT / 'src') + os.pathsep + str(ROOT)
    # Keep request history and all fixture state in a disposable directory.
    with tempfile.TemporaryDirectory(prefix=NAME+'-demo-') as tmp:
        work = Path(tmp)
        env['HTTPEEK_HOME'] = str(work/'history')
        if NAME == 'httpeek':
            sys.path.insert(0,str(ROOT))
            from httpeek.mock_server import make_server
            import threading
            server = make_server('127.0.0.1',0,{'mocks':[
                {'method':'GET','path':'/health','status':200,'body':{'status':'ok'}},
                {'method':'POST','path':'/items','status':201,'body':{'id':42,'created':True}},
            ]})
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base='http://127.0.0.1:'+str(server.server_address[1])
            try:
                print('Local mock server (temporary port; synthetic responses)\n')
                for method,path in [('get','/health'),('post','/items')]:
                    command=[sys.executable,'-m','httpeek',method,base+path,'--no-history','--no-color']
                    print('$ httpeek '+method+' '+base+path+' --no-history')
                    print(call(command,work,env))
                print('$ httpeek get '+base+'/health --to-curl')
                print(call([sys.executable,'-m','httpeek','get',base+'/health','--to-curl'],work,env))
            finally:server.shutdown();server.server_close();thread.join()
            return
        if NAME == 'vetagent':
            fixture=ROOT/'demo/fixtures'
            print('$ node dist/cli.js --path demo/fixtures --no-color\n')
            output=call(['node',str(ROOT/'dist/cli.js'),'--path',str(fixture),'--no-color'],ROOT,env,(1,))
            # Report contents are untouched; normalize only the absolute demo root.
            print(output.replace(str(fixture),'demo/fixtures').replace(str(ROOT),'.'))
            print('Exit code: 1 (expected: deliberately unsafe demo configuration)')
            return
        def git(*args):return call(['git',*args],work,env)
        env.update(GIT_AUTHOR_NAME='Demo Contributor',GIT_COMMITTER_NAME='Demo Contributor',
                   GIT_AUTHOR_EMAIL='contributor@example.invalid',GIT_COMMITTER_EMAIL='contributor@example.invalid')
        git('init','-q','-b','main')
        def write(path,text):
            f=work/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
        def commit(message,date):
            env['GIT_AUTHOR_DATE']=date;env['GIT_COMMITTER_DATE']=date
            git('add','.');git('-c','commit.gpgsign=false','commit','-qm',message)
        write('src/core.py','def total(items):\n    return sum(items)\n')
        write('src/app.py','from src.core import total\n\ndef checkout(items):\n    return total(items)\n')
        write('tests/test_core.py','from src.core import total\n\ndef test_total():\n    assert total([1, 2]) == 3\n')
        write('README.md','# Demo checkout\n\nSynthetic sample project.\n')
        commit('feat: add checkout total','2026-09-01T12:00:00+00:00')
        write('src/core.py','def total(items):\n    if not items:\n        return 0\n    return sum(items)\n')
        commit('fix: handle empty baskets','2026-09-08T12:00:00+00:00')
        write('src/app.py','from src.core import total\n\ndef checkout(items):\n    return round(total(items), 2)\n')
        commit('fix: round checkout amounts','2026-09-15T12:00:00+00:00')
        if NAME == 'gitlore':
            print('$ gitlore --no-color\n')
            out=call([sys.executable,'-m','gitlore','--no-color'],work,env)
        else:
            write('src/core.py','def total(items):\n    if not items:\n        return 0\n    return round(sum(items), 2)\n')
            write('tests/test_core.py','from src.core import total\n\ndef test_total():\n    assert total([1, 2]) == 3\n    assert total([]) == 0\n')
            print('$ '+NAME+' --no-color\n')
            out=call([sys.executable,'-m',NAME,'--no-color'],work,env)
        print(out.replace(str(work),'demo-project'))
        if NAME == 'gitlore':
            call([sys.executable,'-m','gitlore','--html',str(ROOT/'demo/sample-report.html')],work,env)
            f=ROOT/'demo/sample-report.html'
            f.write_text(f.read_text().replace(str(work),'demo-project'))
            print('HTML report: demo/sample-report.html')

if __name__ == '__main__':main()
