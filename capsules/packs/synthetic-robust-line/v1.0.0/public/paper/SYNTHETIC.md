# Synthetic robust-line specification

For every unordered pair of observations with distinct x coordinates, compute the pairwise slope
(y_j - y_i) / (x_j - x_i). The estimated slope is the ordinary median of all such slopes. The
estimated intercept is the ordinary median of y_i - slope * x_i across every observation.

For an odd-length sorted list the median is its middle value. For an even-length list it is the
arithmetic mean of the two middle values. This deterministic finite-sample specification is the
entire result to reproduce.
