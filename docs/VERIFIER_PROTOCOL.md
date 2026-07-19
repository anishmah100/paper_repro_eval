# Trusted verifier protocol

private/verifier.yaml contains a command array. The core replaces {context} and {output}.
The context JSON gives absolute paths to the fresh submission, reproduced artifacts, private pack,
hidden inputs, reference, and an initially empty evidence directory. The verifier writes:

    {
      "schema_version": 1,
      "checks": [{
        "id": "check-id",
        "status": "passed",
        "score": 1.0,
        "summary": "what was observed",
        "measurements": {},
        "evidence": ["relative/path.txt"]
      }],
      "warnings": []
    }

Every ID must occur exactly once and match private/checks.yaml. Evidence paths are relative to the
provided evidence directory and must exist. Statuses are passed, partial, failed, blocked,
or error; their score rules are schema-validated. The core blocks dependents of failed, blocked,
or errored prerequisites and computes the weighted mean of objective checks. Diagnostic checks have
no leaderboard effect. Any errored objective produces evaluator error, never a candidate zero.

Verifiers can use any language. paper_repro_eval.verifier_sdk is an optional Python convenience.
