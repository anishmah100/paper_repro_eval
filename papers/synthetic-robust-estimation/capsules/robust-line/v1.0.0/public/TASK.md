# Reproduce a robust median-slope estimator

Read paper/SYNTHETIC.md and implement the specified estimator. Work autonomously and use any normal
tools or internet resources. Do not inspect any other candidate's directory or output.

Deliver:

- submission/solution.py: invoked as python solution.py INPUT.json OUTPUT.json.
- submission/reproduce.sh: runs a visible demonstration and writes visible_result.json to the
  directory named by REPRO_OUTPUT_DIR.
- submission/REPORT.md: explain the method, observed result, controls, deviations, and limitations.
- submission/demo.sh is optional.

Input is a JSON object with points, a list of [x, y] numeric pairs. Output must be a JSON object
with finite numeric slope and intercept. You may add fields. Handle unsorted points, repeated y
values, negative coordinates, and outliers. At least two distinct x values are guaranteed.

The evaluator reruns only the sealed submission in a fresh directory, checks the visible artifact,
and invokes solution.py on unseen inputs. A hard-coded visible answer will not pass. Because only
submission/ is sealed, copy any visible demonstration input you need into that directory.
