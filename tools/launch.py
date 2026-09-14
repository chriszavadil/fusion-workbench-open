"""Open the existing local workbench, or start its visible local console."""
from pathlib import Path
import http.client
import subprocess
import sys
import webbrowser

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:18765'

def main():
    connection=http.client.HTTPConnection('127.0.0.1',18765,timeout=2)
    try:
        connection.request('GET','/api/status')
        response=connection.getresponse();response.read()
        if response.status==200 and (response.getheader('Server') or '').startswith('FusionWorkbench'):
            webbrowser.open(URL)
            return 0
        raise RuntimeError('Local preview port is occupied by a different service; nothing was changed.')
    except (ConnectionRefusedError,TimeoutError,OSError):
        return subprocess.call([sys.executable,str(ROOT/'app/server.py'),'--port','18765','--open'],cwd=ROOT)
    finally:
        connection.close()

if __name__=='__main__':
    raise SystemExit(main())
