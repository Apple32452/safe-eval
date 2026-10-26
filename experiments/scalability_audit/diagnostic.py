import json,subprocess,sys,time
from audit import HERE,ROOT,matrix

out=HERE/'results';path=out/'diagnostic_checkpoint.json';config=matrix()[15]
with (out/'diagnostic_stderr.log').open('w') as err:
    child=subprocess.Popen([sys.executable,str(HERE/'audit.py'),json.dumps(config),'0',str(path.resolve())],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=err)
    start=time.perf_counter();replay=None;reason=None
    while child.poll() is None:
        time.sleep(.2)
        if path.exists():
            try:row=json.loads(path.read_text())
            except (json.JSONDecodeError,PermissionError):continue
            if row.get('phase')=='replay_running' and replay is None:replay=time.perf_counter()
        if replay and time.perf_counter()-replay>45:reason='replay_timeout_45s'
        elif time.perf_counter()-start>180:reason='worker_timeout_180s'
        if reason:child.kill();child.wait();break
row=json.loads(path.read_text()) if path.exists() else dict(config=config)
row.update(diagnostic_only=True,excluded_from_main_medians=True,exit_code=child.returncode)
if reason:row['censored']=reason
(out/'diagnostic_retry.json').write_text(json.dumps(row,indent=2));print(json.dumps(row,indent=2))
