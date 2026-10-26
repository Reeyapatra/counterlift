"""Record actual CLI outputs as an asciinema v2 terminal cast; never synthesize results."""
import json
import os
import subprocess
import time
from pathlib import Path

path=Path('docs/demo.cast')
if path.exists(): raise SystemExit('Recording already exists; preserve earlier evidence')
commands=[['.venv/bin/counterlift','--help'],
          ['.venv/bin/counterlift','demo','--out','runs/recorded-demo','--bootstrap','50'],
          ['.venv/bin/counterlift','export','--run','runs/recorded-demo','--out','runs/recorded-public'],
          ['.venv/bin/python','scripts/check_app.py']]
started=time.monotonic()
with path.open('w') as recording:
    recording.write(json.dumps({'version':2,'width':110,'height':32,'timestamp':int(time.time()),
                                'title':'CounterLift synthetic CLI and UI smoke demonstration',
                                'env':{'SHELL':'/bin/bash','TERM':'xterm-256color'}})+'\n')
    def emit(text):
        recording.write(json.dumps([time.monotonic()-started,'o',text.replace('\n','\r\n')])+'\n');recording.flush()
    emit('SYNTHETIC SOFTWARE DEMO — no real Criteo results or live campaign impact.\n')
    for command in commands:
        emit('$ '+' '.join(command)+'\n')
        proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
                              env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
        for line in proc.stdout: emit(line)
        status=proc.wait();emit(f'Exit status: {status}\n')
        if status: raise SystemExit(status)
print(f'Actual CLI recording saved to {path}')
