"""Ranking utilities for combining and diversifying recommendation signals."""


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


def _jaccard_similarity(left, right):
    """Return genre-set Jaccard similarity; empty metadata is non-redundant."""
    left = set(left or ())
    right = set(right or ())
    if not left or not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def diversify_by_genre(
    ranked_ids,
    genres_by_item,
    top_k=20,
    relevance_weight=0.75,
):
    """Greedily rerank candidates with a genre-aware MMR objective.

    Relevance is derived from the incoming rank (not incomparable model scores).
    Redundancy is the maximum Jaccard overlap with already selected items.
    A relevance_weight of 1.0 preserves the original ranking; lower values
    trade some rank relevance for catalog variety.
    """
    if top_k <= 0 or not ranked_ids:
        return []
    if not 0.0 <= relevance_weight <= 1.0:
        raise ValueError("relevance_weight must be between 0 and 1")

    unique_ids = list(dict.fromkeys(ranked_ids))
    if relevance_weight == 1.0 or len(unique_ids) <= 1:
        return unique_ids[:top_k]

    # Rank-derived relevance is normalized to [0, 1], keeping the MMR terms
    # on a comparable scale without pretending RRF scores are probabilities.
    relevance = {
        item_id: 1.0 / (rank + 1)
        for rank, item_id in enumerate(unique_ids)
    }
    max_relevance = max(relevance.values())
    relevance = {
        item_id: score / max_relevance
        for item_id, score in relevance.items()
    }

    selected = []
    remaining = set(unique_ids)
    original_order = {item_id: rank for rank, item_id in enumerate(unique_ids)}

    while remaining and len(selected) < top_k:
        best_item = None
        best_score = float("-inf")
        for item_id in unique_ids:
            if item_id not in remaining:
                continue
            redundancy = max(
                (
                    _jaccard_similarity(
                        genres_by_item.get(item_id, ()),
                        genres_by_item.get(chosen, ()),
                    )
                    for chosen in selected
                ),
                default=0.0,
            )
            score = (
                relevance_weight * relevance[item_id]
                - (1.0 - relevance_weight) * redundancy
            )
            if (
                score > best_score
                or (
                    score == best_score
                    and best_item is not None
                    and original_order[item_id] < original_order[best_item]
                )
            ):
                best_item = item_id
                best_score = score

        selected.append(best_item)
        remaining.remove(best_item)

    return selected
