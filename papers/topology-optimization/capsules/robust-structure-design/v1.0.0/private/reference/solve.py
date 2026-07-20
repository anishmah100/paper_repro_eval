#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[7]
raise SystemExit(subprocess.call([sys.executable,str(root/"authoring"/"arena_reference.py"),"topology",*sys.argv[1:]]))
