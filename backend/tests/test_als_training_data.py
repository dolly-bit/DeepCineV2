from types import SimpleNamespace

import pytest

from train_collaborative_model import filter_eligible_watch_events


def event(user_id, tmdb_id):
    return SimpleNamespace(user_id=user_id, tmdb_id=tmdb_id)


def test_keeps_only_users_with_minimum_distinct_movie_count():
    events = [
        event(1, 10), event(1, 20), event(1, 30),
        event(2, 10), event(2, 20), event(2, 30),
        event(3, 10), event(3, 20),
    ]
    eligible = filter_eligible_watch_events(
        events, min_users=2, min_interactions_per_user=3
    )
    assert {row.user_id for row in eligible} == {1, 2}
    assert len(eligible) == 6


def test_repeated_watches_do_not_satisfy_distinct_movie_threshold():
    events = [
        event(1, 10), event(1, 10), event(1, 10),
        event(2, 20), event(2, 30), event(2, 40),
        event(3, 20), event(3, 30), event(3, 40),
    ]
    with pytest.raises(ValueError, match="Insufficient interaction data"):
        filter_eligible_watch_events(
            events, min_users=2, min_interactions_per_user=3
        )


def test_rejects_too_few_eligible_users():
    events = [
        event(1, 10), event(1, 20), event(1, 30),
        event(2, 10), event(2, 20), event(2, 30),
    ]
    with pytest.raises(ValueError, match="at least 5 eligible users"):
        filter_eligible_watch_events(events)


def test_rejects_empty_watch_history():
    with pytest.raises(ValueError, match="No WatchHistory rows"):
        filter_eligible_watch_events([])


@pytest.mark.parametrize("min_users,min_items", [(0, 1), (1, 0), (-1, 2)])
def test_rejects_invalid_thresholds(min_users, min_items):
    with pytest.raises(ValueError, match="thresholds must be positive"):
        filter_eligible_watch_events(
            [event(1, 10)],
            min_users=min_users,
            min_interactions_per_user=min_items,
        )
