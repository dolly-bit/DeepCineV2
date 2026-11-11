import math

from evaluate_recommenders import (
    temporal_holdout,
    precision_at_k,
    recall_at_k,
    ndcg_at_k,
    evaluate_rankings,
)


class Event:
    def __init__(self, user_id, tmdb_id, watched_at, event_id):
        self.user_id = user_id
        self.tmdb_id = tmdb_id
        self.watched_at = watched_at
        self.id = event_id


def test_temporal_holdout_keeps_latest_unique_items_for_test():
    from datetime import datetime, timedelta
    start = datetime(2026, 1, 1)
    events = [
        Event(1, 10, start, 1),
        Event(1, 10, start + timedelta(days=1), 2),  # duplicate watch
        Event(1, 20, start + timedelta(days=2), 3),
        Event(1, 30, start + timedelta(days=3), 4),
        Event(2, 40, start, 5),  # one-item users are excluded
    ]
    train, test = temporal_holdout(events, test_ratio=0.34)
    assert train == {1: {10, 20}}
    assert test == {1: {30}}


def test_ranking_metrics_known_values():
    recs = [7, 8, 9]
    relevant = {8, 9}
    assert precision_at_k(recs, relevant, 3) == 2 / 3
    assert recall_at_k(recs, relevant, 3) == 1.0
    expected_ndcg = (1 / math.log2(3) + 1 / math.log2(4)) / (
        1 + 1 / math.log2(3)
    )
    assert abs(ndcg_at_k(recs, relevant, 3) - expected_ndcg) < 1e-12


def test_evaluate_rankings_computes_macro_metrics_and_coverage():
    rankings = {1: [10, 20], 2: [20, 30]}
    test = {1: {20}, 2: {99}}
    metrics = evaluate_rankings(rankings, test, {10, 20, 30, 99}, [1])
    assert metrics["1"]["precision"] == 0.5
    assert metrics["1"]["recall"] == 0.5
    assert metrics["1"]["coverage"] == 0.5
    assert metrics["1"]["users_evaluated"] == 2
