"""Rank-level fusion for heterogeneous recommendation signals."""


def reciprocal_rank_fusion(rankings, weights=None, top_k=20, rank_constant=60):
    """Fuse ordered candidate lists without mixing incomparable raw scores."""
    if top_k <= 0:
        return []

    weights = weights or {}
    scores = {}
    for signal, candidates in rankings.items():
        weight = float(weights.get(signal, 1.0))
        if weight <= 0:
            continue
        seen = set()
        for rank, candidate in enumerate(candidates, start=1):
            if candidate in seen:
                continue
            seen.add(candidate)
            scores[candidate] = (
                scores.get(candidate, 0.0) + weight / (rank_constant + rank)
            )

    return sorted(scores, key=scores.get, reverse=True)[:top_k]
