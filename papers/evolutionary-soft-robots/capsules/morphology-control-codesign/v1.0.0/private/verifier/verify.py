from pathlib import Path
import subprocess, sys
root=Path(__file__).resolve().parents[7]
raise SystemExit(subprocess.call([sys.executable,str(root/"authoring"/"arena_verifier.py"),"--task","softrobot",*sys.argv[1:]]))
