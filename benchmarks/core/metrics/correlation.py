"""Spearman rank correlation, stdlib-only (no scipy/numpy dependency)."""


def _rank(values: list[float]) -> list[float]:
    """Average (fractional) ranks, ties get the mean rank of their tied group."""
    indexed = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # 1-indexed
        for m in range(i, j + 1):
            ranks[indexed[m]] = avg_rank
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    """Spearman rank correlation coefficient between two equal-length series.

    Returns 0.0 for degenerate inputs (fewer than 2 points, or a series with
    zero variance in rank) rather than raising -- correlation is undefined
    there, and 0.0 (no signal) is the honest default for a benchmark metric.
    """
    n = len(x)
    if n != len(y) or n < 2:
        return 0.0

    rx = _rank(list(x))
    ry = _rank(list(y))

    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n

    cov = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry))
    var_x = sum((a - mean_rx) ** 2 for a in rx)
    var_y = sum((b - mean_ry) ** 2 for b in ry)

    denom = (var_x * var_y) ** 0.5
    if denom == 0.0:
        return 0.0
    return round(cov / denom, 4)
