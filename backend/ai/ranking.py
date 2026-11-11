"""Rank-level fusion for heterogeneous recommendation signals.

Raw scores from ALS, FAISS distances, genre affinity and popularity are on
incomparable scales. Reciprocal-rank fusion combines their orderings without
treating those raw values as calibrated probabilities.
"""


def reciprocal_rank_fusion(rankings, weights=None, top_k=20, rank_constant=60):
    """Fuse ordered candidate-ID lists and return the highest-ranked IDs."""
    if top_k <= 0:
        return []

    weights = weights or {}
    fused_scores = {}

    for signal, candidate_ids in rankings.items():
        weight = float(weights.get(signal, 1.0))
        if weight <= 0:
            continue

        seen = set()
        for rank, candidate_id in enumerate(candidate_ids, start=1):
            if candidate_id in seen:
                continue
            seen.add(candidate_id)
            fused_scores[candidate_id] = (
                fused_scores.get(candidate_id, 0.0)
                + weight / (rank_constant + rank)
            )

    return sorted(
        fused_scores,
        key=lambda candidate_id: fused_scores[candidate_id],
        reverse=True,
    )[:top_k]
