import unittest

from ai.ranking import reciprocal_rank_fusion, diversify_by_genre


class ReciprocalRankFusionTests(unittest.TestCase):
    def test_combines_signals_and_preserves_unique_candidates(self):
        ranked = reciprocal_rank_fusion({
            "content": [10, 20, 30],
            "collaborative": [20, 40, 10],
        }, top_k=4)
        self.assertEqual(ranked[0], 20)
        self.assertEqual(set(ranked), {10, 20, 30, 40})
        self.assertEqual(len(ranked), 4)

    def test_duplicate_in_one_signal_counts_once(self):
        self.assertEqual(reciprocal_rank_fusion({"content": [1, 1, 2]}), [1, 2])

    def test_weights_and_top_k_are_applied(self):
        ranked = reciprocal_rank_fusion(
            {"content": [1, 2], "popular": [3]},
            weights={"content": 0.1, "popular": 10},
            top_k=1,
        )
        self.assertEqual(ranked, [3])

    def test_empty_and_non_positive_top_k(self):
        self.assertEqual(reciprocal_rank_fusion({}), [])
        self.assertEqual(reciprocal_rank_fusion({"x": [1]}, top_k=0), [])

    def test_genre_mmr_moves_less_redundant_candidate_up(self):
        ranked = diversify_by_genre(
            [1, 2, 3],
            {1: {"drama", "crime"}, 2: {"drama", "crime"}, 3: {"comedy"}},
            top_k=3,
            relevance_weight=0.8,
        )
        self.assertEqual(ranked, [1, 3, 2])

    def test_genre_mmr_preserves_order_when_relevance_weight_is_one(self):
        self.assertEqual(
            diversify_by_genre(
                [3, 1, 2],
                {3: {"drama"}, 1: {"drama"}, 2: {"comedy"}},
                top_k=3,
                relevance_weight=1.0,
            ),
            [3, 1, 2],
        )

    def test_genre_mmr_deduplicates_candidates_and_is_deterministic(self):
        ids = [1, 1, 2, 3]
        genres = {1: {"a"}, 2: {"a"}, 3: {"b"}}
        first = diversify_by_genre(ids, genres, top_k=3)
        second = diversify_by_genre(ids, genres, top_k=3)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(set(first), {1, 2, 3})

    def test_genre_mmr_rejects_invalid_relevance_weight(self):
        with self.assertRaises(ValueError):
            diversify_by_genre([1, 2], {}, relevance_weight=1.5)


if __name__ == "__main__":
    unittest.main()
