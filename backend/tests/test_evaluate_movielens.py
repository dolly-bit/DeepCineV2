from evaluate_movielens import (
    build_temporal_split,
    evaluate_rankings,
    bootstrap_mean_ci,
    paired_bootstrap_difference_ci,
    load_latest_ratings,
    load_movie_mapping,
    sample_evaluation_users,
    select_ranking_users,
    tune_hybrid_weights,
    rank_content_by_min_l2,
    intra_list_diversity,
    item_novelty,
    evaluate_diversity_novelty,
    evaluate_signal_diagnostics,
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
        "1,1,5.0,100\n1,1,2.0,200\n1,1,4.5,150\n2,1,4.0,100\n",
        encoding="utf-8",
    )
    latest, stats = load_latest_ratings(path, {1: 10}, chunksize=2)
    assert latest[(1, 10)] == (200, 2.0)
    assert latest[(2, 10)] == (100, 4.0)
    assert stats["ratings_rows_scanned"] == 4


def test_three_way_temporal_split_is_ordered_and_excludes_short_users():
    latest = {
        (1, 10): (100, 4.0), (1, 20): (200, 5.0),
        (1, 30): (300, 4.0), (1, 40): (400, 4.5),
        (1, 50): (500, 5.0), (2, 60): (100, 5.0),
        (2, 70): (200, 4.0),
    }
    train, validation, test, stats = build_temporal_split(latest, 4.0)
    assert train == {1: {10, 20, 30}}
    assert validation == {1: {40}}
    assert test == {1: {50}}
    assert stats["eligible_users"] == 1
    assert stats["excluded_users_fewer_than_three_positive_items"] == 1


def test_three_way_split_rejects_invalid_ratios():
    import pytest
    with pytest.raises(ValueError):
        build_temporal_split({}, train_ratio=0.8, validation_ratio=0.3, test_ratio=0.2)


def test_metrics_use_candidate_catalog_for_coverage():
    rankings = {1: [10, 20], 2: [20, 30]}
    relevant = {1: {10}, 2: {99}}
    metrics = evaluate_rankings(rankings, relevant, {10, 20, 30, 99}, [1])
    assert metrics["1"]["precision"] == 0.5
    assert metrics["1"]["recall"] == 0.5
    assert metrics["1"]["coverage"] == 0.5


def test_validation_tuning_uses_validation_labels_and_returns_weights():
    signals = {
        "content": {1: [10, 11], 2: [20, 21]},
        "collaborative": {1: [11, 10], 2: [21, 20]},
        "explicit_preferences": {1: [10, 12], 2: [20, 22]},
        "global_popularity": {1: [12, 11], 2: [22, 21]},
    }
    validation = {1: {10}, 2: {20}}
    result = tune_hybrid_weights(signals, validation, [1, 2], {10, 11, 12, 20, 21, 22})
    assert set(result["weights"]) == {"content", "collaborative", "explicit_preferences", "popularity"}
    assert result["configurations_tested"] == 81
    assert result["tuning_users_sampled"] == 2
    assert result["objective"].startswith("validation_ndcg_at_")



def test_evaluation_user_sample_is_deterministic_and_bounded():
    users = set(range(100))
    first = sample_evaluation_users(users, sample_size=12, seed=7)
    second = sample_evaluation_users(users, sample_size=12, seed=7)
    assert first == second
    assert len(first) == 12
    assert set(first).issubset(users)


def test_evaluation_user_sample_keeps_all_when_under_limit():
    assert sample_evaluation_users({3, 1, 2}, sample_size=10) == [1, 2, 3]


def test_evaluation_user_sample_rejects_non_positive_limit():
    import pytest
    with pytest.raises(ValueError):
        sample_evaluation_users({1, 2}, sample_size=0)



def test_ranking_user_subset_does_not_change_training_population():
    train = {1: {10}, 2: {20}, 3: {30}}
    assert select_ranking_users(train, [3, 1]) == [1, 3]
    assert len(train) == 3


def test_ranking_user_subset_rejects_unknown_users():
    import pytest
    with pytest.raises(ValueError):
        select_ranking_users({1: {10}}, [2])


def test_bootstrap_mean_ci_is_deterministic_and_contains_constant_mean():
    first = bootstrap_mean_ci([0.5, 0.5, 0.5], seed=17, samples=200)
    second = bootstrap_mean_ci([0.5, 0.5, 0.5], seed=17, samples=200)
    assert first == second == {"lower": 0.5, "upper": 0.5}


def test_paired_bootstrap_difference_uses_matching_users():
    left = {
        1: {"ndcg": 0.8},
        2: {"ndcg": 0.6},
        3: {"ndcg": 0.4},
    }
    right = {
        1: {"ndcg": 0.5},
        2: {"ndcg": 0.4},
        3: {"ndcg": 0.2},
    }
    ci = paired_bootstrap_difference_ci(left, right, "ndcg", seed=3, samples=200)
    repeated = paired_bootstrap_difference_ci(
        left, right, "ndcg", seed=3, samples=200
    )
    # Per-user differences are [0.3, 0.2, 0.2], so resampling need not
    # produce a zero-width interval even though the point mean is deterministic.
    assert ci == repeated
    assert ci["lower"] <= (0.3 + 0.2 + 0.2) / 3 <= ci["upper"]
    assert ci["lower"] > 0


def test_evaluate_rankings_can_skip_bootstrap_for_tuning():
    metrics = evaluate_rankings(
        {1: [10]}, {1: {10}}, {10, 20}, [1], include_ci=False
    )
    assert metrics["1"]["ndcg"] == 1.0
    assert "ndcg_ci95" not in metrics["1"]



def test_validation_and_test_cohorts_are_independently_seeded():
    users = set(range(10_000))
    validation = sample_evaluation_users(users, sample_size=500, seed=42)
    test = sample_evaluation_users(users, sample_size=500, seed=43)
    assert validation == sample_evaluation_users(users, sample_size=500, seed=42)
    assert test == sample_evaluation_users(users, sample_size=500, seed=43)
    assert validation != test
    assert len(validation) == len(test) == 500


def test_production_content_l2_uses_min_distance_and_excludes_watched():
    import numpy as np

    embeddings = np.asarray([
        [0.0, 0.0], [10.0, 0.0], [0.2, 0.0], [3.0, 0.0], [10.1, 0.0]
    ], dtype=np.float32)
    ranked = rank_content_by_min_l2(
        embeddings, [10, 20, 30, 40, 50], {10, 20},
        candidate_limit=10, neighbors_per_watched=5,
    )
    assert ranked == [50, 30, 40]


def test_production_content_l2_handles_empty_and_invalid_inputs():
    import numpy as np
    import pytest

    vectors = np.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=np.float32)
    assert rank_content_by_min_l2(vectors, [1, 2], set(), 10, 5) == []
    with pytest.raises(ValueError):
        rank_content_by_min_l2(vectors, [1], {1}, 10, 5)



def test_intra_list_diversity_uses_pairwise_jaccard_distance():
    diversity = intra_list_diversity(
        [10, 20, 30],
        {
            10: {"action", "comedy"},
            20: {"action"},
            30: {"drama"},
        },
    )
    # Distances: 0.5, 1.0, 1.0.
    assert diversity == 5 / 6


def test_intra_list_diversity_skips_pairs_with_missing_genres():
    assert intra_list_diversity([10, 20], {10: {"action"}, 20: set()}) == 0.0


def test_item_novelty_uses_smoothed_training_frequency():
    rare = item_novelty(99, {10: 9}, total_interactions=9, catalog_size=2)
    popular = item_novelty(10, {10: 9}, total_interactions=9, catalog_size=2)
    assert rare > popular


def test_diversity_novelty_evaluation_is_deterministic():
    rankings = {1: [10, 20], 2: [20, 30]}
    genres = {10: {"action"}, 20: {"action", "comedy"}, 30: {"drama"}}
    first = evaluate_diversity_novelty(
        rankings, [1, 2], genres, {10: 8, 20: 1}, 9, 3, [2],
        bootstrap_seed=7, bootstrap_samples=100,
    )
    second = evaluate_diversity_novelty(
        rankings, [1, 2], genres, {10: 8, 20: 1}, 9, 3, [2],
        bootstrap_seed=7, bootstrap_samples=100,
    )
    assert first == second
    assert first["2"]["intra_list_diversity"] > 0
    assert first["2"]["novelty_bits"] > 0



def test_signal_diagnostics_report_overlap_recall_ablation_and_cf_retention():
    signals = {
        "content": {1: [10, 11, 12], 2: [20, 21, 22]},
        "collaborative": {1: [10, 13, 14], 2: [20, 23, 24]},
        "explicit_preferences": {1: [11, 12, 15], 2: [21, 22, 25]},
        "global_popularity": {1: [15, 16, 17], 2: [25, 26, 27]},
    }
    relevant = {1: {10, 15}, 2: {20, 25}}
    result = evaluate_signal_diagnostics(
        signals,
        {
            "content": 1.0,
            "collaborative": 1.0,
            "explicit_preferences": 1.25,
            "popularity": 0.2,
        },
        relevant,
        {10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25, 26, 27},
        [1, 2],
        [1, 2],
        candidate_k=3,
        bootstrap_seed=9,
        bootstrap_samples=50,
    )
    assert result["candidate_recall"]["collaborative"]["recall"] == 1.0
    assert result["candidate_recall"]["union"]["recall"] == 1.0
    assert result["pairwise_candidate_overlap_jaccard"]["content"]["collaborative"] > 0
    assert "without_each_signal" in result["ablation"]
    assert set(result["ablation"]["without_each_signal"]) == {
        "content", "collaborative", "explicit_preferences", "global_popularity"
    }
    assert set(result["collaborative_rank_retention"]) == {"1", "2"}
    assert 0.0 <= result["collaborative_rank_retention"]["2"][
        "mean_fraction_of_top_cf_candidates_retained_in_hybrid_top_k"
    ] <= 1.0


def test_signal_diagnostics_are_deterministic():
    signals = {
        "content": {1: [1, 2]},
        "collaborative": {1: [2, 1]},
        "explicit_preferences": {1: [1, 3]},
        "global_popularity": {1: [3, 2]},
    }
    args = (
        signals,
        {"content": 1.0, "collaborative": 1.0,
         "explicit_preferences": 1.0, "popularity": 0.2},
        {1: {1}}, {1, 2, 3}, [1], [1],
    )
    first = evaluate_signal_diagnostics(
        *args, candidate_k=2, bootstrap_seed=12, bootstrap_samples=50
    )
    second = evaluate_signal_diagnostics(
        *args, candidate_k=2, bootstrap_seed=12, bootstrap_samples=50
    )
    assert first == second
