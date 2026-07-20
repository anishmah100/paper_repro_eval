# dm_control: Software and Tasks for Continuous Control

- Authors: Saran Tunyasuvunakool, Alistair Muldal, Yotam Doron, Siqi Liu, Steven Bohez, Josh Merel, Tom Erez, Timothy Lillicrap, Nicolas Heess, Yuval Tassa
- Published: 2020
- Primary source: https://arxiv.org/abs/2006.12983

This directory stores paper-level source notes shared by every capsule. Before calibration, archive
the legally redistributable paper or an integrity-pinned retrieval record here. The public task may
use normal internet access; the private verifier must pin every dependency and fixture it relies on.

## Benchmark interpretation

The upstream MuJoCo model procedurally generates the evaluated linked-pole systems.

The capsule deliberately adds a competitive transfer problem so models can be ranked on the quality
of the resulting artifact, not only on whether they copied the source method.
