#!/usr/bin/env python3
"""Public baseline. Replace baseline() with your research implementation."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import arena_kit
c=json.loads(Path(sys.argv[1]).read_text()); Path(sys.argv[2]).write_text(json.dumps(arena_kit.baseline("smoke",c)))
