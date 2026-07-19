from __future__ import annotations

import shutil
from pathlib import Path

from paper_repro_eval.lifecycle import reproduce_run, seal_run
from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository
from paper_repro_eval.review import create_review_packet, suite_report
from paper_repro_eval.run_store import find_run
from paper_repro_eval.verification import verify_run


def _write_reference_submission(repository: Repository, run_id: str) -> Path:
    run = find_run(repository, run_id)
    submission = run.workspace / "submission"
    pack = repository.packs_dir / "synthetic-robust-line" / "v1.0.0"
    shutil.copy2(pack / "private" / "reference" / "solution.py", submission / "solution.py")
    shutil.copy2(pack / "public" / "resources" / "visible.json", submission / "visible.json")
    (submission / "reproduce.sh").write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'python solution.py visible.json "$REPRO_OUTPUT_DIR/visible_result.json"\n',
        encoding="utf-8",
    )
    (submission / "REPORT.md").write_text(
        "# Reproduction report\n\nMedian pairwise slopes reject the single outlier. "
        "Unlike least squares, this finite sample estimator is robust "
        "but not universally immune.\n",
        encoding="utf-8",
    )
    return submission


def test_complete_lifecycle_produces_score_and_review(repository: Repository) -> None:
    record = prepare_suite(repository, "synthetic-smoke", ["reference"])[0]
    _write_reference_submission(repository, record.run_id)
    first_seal = seal_run(repository, record.run_id)
    second_seal = seal_run(repository, record.run_id)
    assert first_seal.revision == second_seal.revision == 1
    reproduction = reproduce_run(repository, record.run_id)
    assert reproduction.status == "success"
    verification = verify_run(repository, record.run_id)
    assert verification.status == "success"
    assert verification.objective_score == 1
    assert all(check.score == 1 for check in verification.checks)
    packet = create_review_packet(repository, record.run_id)
    assert (packet / "index.html").is_file()
    assert (packet / "evidence" / "comparison.json").is_file()
    report = suite_report(repository, "synthetic-smoke")
    assert (report / "report.csv").is_file()
    assert (report / "report.json").is_file()


def test_wrong_candidate_is_a_scored_result_not_evaluator_error(repository: Repository) -> None:
    record = prepare_suite(repository, "synthetic-smoke", ["mutant"])[0]
    submission = find_run(repository, record.run_id).workspace / "submission"
    (submission / "solution.py").write_text(
        "import json,sys\njson.dump({'slope':0,'intercept':0},open(sys.argv[2],'w'))\n",
        encoding="utf-8",
    )
    (submission / "reproduce.sh").write_text(
        '#!/usr/bin/env bash\nprintf \'{"slope":0,"intercept":0}\\n\' '
        '> "$REPRO_OUTPUT_DIR/visible_result.json"\n',
        encoding="utf-8",
    )
    (submission / "REPORT.md").write_text("# Wrong on purpose\n", encoding="utf-8")
    seal_run(repository, record.run_id)
    reproduce_run(repository, record.run_id)
    verification = verify_run(repository, record.run_id)
    assert verification.status == "success"
    assert verification.objective_score == 0
    statuses = {check.id: check.status for check in verification.checks}
    assert str(statuses["visible-artifact"]) == "failed"
    assert str(statuses["hidden-exact"]) == "blocked"


def test_missing_reproduce_script_is_candidate_failure(repository: Repository) -> None:
    record = prepare_suite(repository, "synthetic-smoke", ["empty"])[0]
    seal = seal_run(repository, record.run_id)
    assert "reproduce.sh" in seal.missing_required
    reproduction = reproduce_run(repository, record.run_id)
    assert reproduction.status == "candidate-failure"
