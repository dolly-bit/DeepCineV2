import unittest

from ai.ranking import reciprocal_rank_fusion


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
        ranked = reciprocal_rank_fusion({"content": [1, 1, 2]})
        self.assertEqual(ranked, [1, 2])

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


if __name__ == "__main__":
    unittest.main()
