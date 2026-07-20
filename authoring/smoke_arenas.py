#!/usr/bin/env python3
"""Exercise prepare -> seal -> reproduce -> trusted verify for every visual arena."""
from __future__ import annotations
import json,shutil,stat,time
from pathlib import Path
from paper_repro_eval.lifecycle import reproduce_run,seal_run
from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository
from paper_repro_eval.verification import verify_run

ROOT=Path(__file__).resolve().parents[1]
TASK_BY_CAPSULE={
"competitive-editing":"poisson","multipole-control":"multipole",
"progressive-path-tracer":"pathtracer","multimaterial-simulator":"mpm",
"visual-offline-control":"world_mpc","robust-structure-design":"topology",
"adversarial-tournament":"lightcycle","inverse-smoke-control":"smoke",
"morphology-control-codesign":"softrobot","procedural-scene-recovery":"inverse_render"}

REPRO='''#!/usr/bin/env bash
set -euo pipefail
python solve.py visible-case.json "$REPRO_OUTPUT_DIR/result.json"
python arena_kit.py score TASK visible-case.json "$REPRO_OUTPUT_DIR/result.json" > "$REPRO_OUTPUT_DIR/metrics.json"
python render_result.py visible-case.json "$REPRO_OUTPUT_DIR/result.json" "$REPRO_OUTPUT_DIR/preview.png"
'''
RENDER='''import json,sys
from pathlib import Path
import arena_kit
case=json.loads(Path(sys.argv[1]).read_text());out=json.loads(Path(sys.argv[2]).read_text())
arena_kit.render("TASK",case,out,Path(sys.argv[3]))
'''
LIGHT='''#!/usr/bin/env bash
set -euo pipefail
printf '{"policy":"persistent-jsonl"}' > "$REPRO_OUTPUT_DIR/result.json"
printf '{"note":"fixed-field score is computed privately"}' > "$REPRO_OUTPUT_DIR/metrics.json"
python -c 'from PIL import Image;import os;Image.new("RGB",(480,360),(18,20,27)).save(os.environ["REPRO_OUTPUT_DIR"]+"/preview.png")'
'''

def main()->None:
    repo=Repository(ROOT);agent=f"arena-smoke-{int(time.time())}"
    records=prepare_suite(repo,"visual-research-arcade-v0",[agent]);summary=[]
    for record in records:
        task=TASK_BY_CAPSULE[record.capsule_id];workspace=ROOT/record.workspace;sub=workspace/"submission"
        shutil.copy2(workspace/"arena_kit"/"arena_kit.py",sub/"arena_kit.py")
        shutil.copy2(workspace/"resources"/"visible-case.json",sub/"visible-case.json")
        for starter_file in (workspace/"starter").iterdir():
            if starter_file.is_file() and starter_file.name!="README.md":
                shutil.copy2(starter_file,sub/starter_file.name)
        if task=="lightcycle":
            script=LIGHT
        else:
            (sub/"render_result.py").write_text(RENDER.replace("TASK",task));script=REPRO.replace("TASK",task)
        repro=sub/"reproduce.sh";repro.write_text(script);repro.chmod(repro.stat().st_mode|stat.S_IXUSR)
        (sub/"REPORT.md").write_text(f"# Smoke baseline: {task}\n\nProtocol and evidence smoke test only.\n")
        seal_run(repo,record.run_id);reproduction=reproduce_run(repo,record.run_id,timeout_seconds=45)
        verification=verify_run(repo,record.run_id)
        assert reproduction.status=="success",(task,reproduction)
        assert verification.status=="success",(task,verification)
        summary.append({"task":task,"run_id":record.run_id,"score":verification.objective_score})
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
