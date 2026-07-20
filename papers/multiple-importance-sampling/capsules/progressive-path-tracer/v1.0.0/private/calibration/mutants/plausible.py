#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[8]
sys.path.insert(0,str(root/"authoring"))
from calibrate_arenas import plausible_mutant
case=json.loads(Path(sys.argv[1]).read_text())
Path(sys.argv[2]).write_text(json.dumps(plausible_mutant("pathtracer",case)))
