from evaluate_movielens import (
    build_temporal_split,
    evaluate_rankings,
    load_latest_ratings,
    load_movie_mapping,
)


def test_movie_mapping_restricts_to_catalog_overlap(tmp_path):
    path = tmp_path / "links.csv"
    path.write_text(
        "movieId,imdbId,tmdbId\n1,111,10\n2,222,20\n3,333,\n",
        encoding="utf-8",
    )
    assert load_movie_mapping(path, {10, 99}) == {1: 10}


def test_latest_rating_wins_before_positive_threshold(tmp_path):
    path = tmp_path / "ratings.csv"
    path.write_text(
        "userId,movieId,rating,timestamp\n"
        "1,1,5.0,100\n"
        "1,1,2.0,200\n"
        "1,1,4.5,150\n"
        "2,1,4.0,100\n",
        encoding="utf-8",
    )
    latest, stats = load_latest_ratings(path, {1: 10}, chunksize=2)
    assert latest[(1, 10)] == (200, 2.0)
    assert latest[(2, 10)] == (100, 4.0)
    assert stats["ratings_rows_scanned"] == 4


def test_temporal_split_excludes_single_positive_users():
    latest = {
        (1, 10): (100, 4.0),
        (1, 20): (200, 5.0),
        (1, 30): (300, 4.0),
        (2, 10): (100, 5.0),
        (2, 20): (200, 2.0),
    }
    train, test, stats = build_temporal_split(latest, 4.0, 0.2)
    assert train == {1: {10, 20}}
    assert test == {1: {30}}
    assert stats["users_with_at_least_two_positive_movies"] == 1


def test_metrics_use_overlap_catalog_for_coverage():
    rankings = {1: [10, 20], 2: [20, 30]}
    test = {1: {10}, 2: {99}}
    metrics = evaluate_rankings(rankings, test, {10, 20, 30, 99}, [1])
    assert metrics["1"]["precision"] == 0.5
    assert metrics["1"]["recall"] == 0.5
    assert metrics["1"]["coverage"] == 0.5
