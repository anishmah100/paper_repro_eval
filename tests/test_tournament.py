from __future__ import annotations

from pathlib import Path

from paper_repro_eval.tournament import play_match


def _write_bot(directory: Path, body: str) -> Path:
    directory.mkdir()
    (directory / "bot.py").write_text(body, encoding="utf-8")
    script = directory / "bot.sh"
    script.write_text("#!/usr/bin/env bash\nexec python bot.py\n", encoding="utf-8")
    script.chmod(0o755)
    return directory


LEGAL_BOT = """import json,sys
moves={"U":(0,-1),"D":(0,1),"L":(-1,0),"R":(1,0)}
for line in sys.stdin:
    state=json.loads(line)
    if state.get("type")=="reset":
        continue
    w,h=state["board"];x,y=state["you"];occupied={tuple(v) for v in state["occupied"]}
    legal=[]
    for name,(dx,dy) in moves.items():
        q=(x+dx,y+dy)
        if 0<=q[0]<w and 0<=q[1]<h and q not in occupied:
            legal.append(name)
    print(json.dumps({"move":legal[0] if legal else "X"}),flush=True)
"""

ILLEGAL_BOT = """import json,sys
for line in sys.stdin:
    state=json.loads(line)
    if state.get("type")!="reset":
        print(json.dumps({"move":"X"}),flush=True)
"""

SLOW_BOT = """import json,sys,time
for line in sys.stdin:
    state=json.loads(line)
    if state.get("type")!="reset":
        time.sleep(1)
        print(json.dumps({"move":"U"}),flush=True)
"""


def test_simultaneous_match_eliminates_illegal_bot_and_preserves_replay(tmp_path: Path) -> None:
    legal = _write_bot(tmp_path / "legal", LEGAL_BOT)
    illegal = _write_bot(tmp_path / "illegal", ILLEGAL_BOT)
    result = play_match(legal, illegal, seed=7, max_turns=12)
    assert result["winner"] == 0
    assert result["errors"] == [0, 1]
    assert result["frames"][0]["protocol_errors"] == [None, None]
    assert result["frames"][0]["alive"] == [True, False]


def test_match_enforces_per_turn_timeout(tmp_path: Path) -> None:
    legal = _write_bot(tmp_path / "legal", LEGAL_BOT)
    slow = _write_bot(tmp_path / "slow", SLOW_BOT)
    result = play_match(legal, slow, seed=11, turn_timeout=0.03, max_turns=3)
    assert result["winner"] == 0
    assert result["timeouts"] == [0, 1]
    assert result["frames"][0]["protocol_errors"][1] == "timeout"


def test_swapping_sides_changes_winner_index_not_bot_identity(tmp_path: Path) -> None:
    first = _write_bot(tmp_path / "first", LEGAL_BOT)
    second = _write_bot(tmp_path / "second", ILLEGAL_BOT)
    forward = play_match(first, second, seed=19, max_turns=5)
    reverse = play_match(second, first, seed=19, max_turns=5)
    assert forward["winner"] == 0
    assert reverse["winner"] == 1
