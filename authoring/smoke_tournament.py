#!/usr/bin/env python3
"""End-to-end smoke for qualifying sealed bots and isolated cross-run tournament."""

from __future__ import annotations

import json
import shutil
import stat
import time
from pathlib import Path

from paper_repro_eval.lifecycle import reproduce_run, seal_run
from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository
from paper_repro_eval.tournament import run_lightcycle_tournament
from paper_repro_eval.verification import verify_run

ROOT = Path(__file__).resolve().parents[1]
REPRODUCE = """#!/usr/bin/env bash
set -euo pipefail
printf '{"policy":"persistent-jsonl"}' > "$REPRO_OUTPUT_DIR/result.json"
printf '{"note":"fixed-field score is computed privately"}' > "$REPRO_OUTPUT_DIR/metrics.json"
python -c 'from PIL import Image;import os;Image.new("RGB",(480,360),(18,20,27)).save(os.environ["REPRO_OUTPUT_DIR"]+"/preview.png")'
"""


def main() -> None:
    repository = Repository(ROOT)
    stamp = str(int(time.time()))
    agents = [f"tournament-alpha-{stamp}", f"tournament-beta-{stamp}"]
    records = prepare_suite(repository, "visual-research-arcade-v0", agents)
    lightcycle = [record for record in records if record.capsule_id == "adversarial-tournament"]
    assert len(lightcycle) == 2
    for record in lightcycle:
        workspace = ROOT / record.workspace
        submission = workspace / "submission"
        for starter in (workspace / "starter").iterdir():
            if starter.is_file() and starter.name != "README.md":
                shutil.copy2(starter, submission / starter.name)
        reproduce = submission / "reproduce.sh"
        reproduce.write_text(REPRODUCE, encoding="utf-8")
        reproduce.chmod(reproduce.stat().st_mode | stat.S_IXUSR)
        (submission / "REPORT.md").write_text(
            "# Tournament smoke bot\n\nPublic legal-space baseline.\n",
            encoding="utf-8",
        )
        seal_run(repository, record.run_id)
        assert reproduce_run(repository, record.run_id, timeout_seconds=30).status == "success"
        verification = verify_run(repository, record.run_id)
        assert verification.status == "success"
        protocol = next(check for check in verification.checks if check.id == "bot-protocol")
        assert str(protocol.status) == "passed"
    destination = run_lightcycle_tournament(
        repository,
        "visual-research-arcade-v0",
        seeds=2,
        turn_timeout=0.25,
        agents=set(agents),
    )
    report = json.loads((destination / "tournament.json").read_text(encoding="utf-8"))
    assert len(report["standings"]) == 2
    assert len(report["matches"]) == 4
    assert (destination / "TOURNAMENT.md").is_file()
    assert (destination / "standings.csv").is_file()
    assert len(list((destination / "replays").glob("*.html"))) == 4
    print(destination)


if __name__ == "__main__":
    main()
