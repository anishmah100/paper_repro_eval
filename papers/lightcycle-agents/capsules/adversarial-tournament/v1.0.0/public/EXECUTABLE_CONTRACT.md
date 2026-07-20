# Exact executable contract: Lightcycle bot

This is a direct game-playing capsule rather than a paper-mechanism reproduction. The local arena
uses simultaneous cardinal moves, permanent trails, rectangular boards, and deterministic symmetric
obstacles in cross-agent tournaments.

The harness starts `bash bot.sh` as a persistent JSON-Lines process. Ignore or initialize on `reset`.
Each `turn` supplies `board: [WIDTH,HEIGHT]`, `you`, `opponents`, `occupied`, `turn`, and a seed.
Reply before the 0.25-second deadline with exactly one flushed object
`{"move": "U"|"D"|"L"|"R"}`. State may persist inside a match and must reset between matches.

Qualification score uses deterministic fixed opponents and counts wins, draws, illegal moves, and
timeouts. The decisive comparison is a round robin in which every candidate pair plays each map
with starting sides exchanged. Illegal actions, crashes, malformed output, and deadlines fail
closed. Trusted JSON and HTML replays are generated outside the submission.
