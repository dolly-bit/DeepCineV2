# MovieLens offline recommender benchmark

This benchmark evaluates DeepCine's current catalog against MovieLens ratings.
It is intentionally isolated from the production `watch_history` table.

## Run

From the `backend/` directory with the backend virtual environment active:

```powershell
python -m pip install -r requirements.txt
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20
```

The script streams `ratings.csv` in chunks (default 500,000 rows), maps MovieLens `movieId` to TMDB IDs using `links.csv`, and keeps only movies present in the local DeepCine catalog.

## Methodology

1. Keep the latest rating for each user/movie pair.
2. Treat ratings greater than or equal to 4.0 as positive implicit feedback (configurable).
3. Split each eligible user's positive interactions chronologically; the latest fraction is test.
4. Restrict both recommendations and held-out ground truth to the MovieLens/DeepCine catalog overlap.
5. Fit ALS and construct interaction-derived user profiles from training interactions only.
6. Compare MovieLens-positive popularity, metadata content, ALS collaborative, and reciprocal-rank-fusion hybrid recommenders.
7. Report macro Precision@K, Recall@K, NDCG@K, and catalog Coverage@K.

Results are written to `evaluation/results/` as timestamped JSON and CSV files.

## Interpretation caveats

- The benchmark is limited to the overlapping catalog, not all DeepCine movies.
- This is implicit top-N retrieval evaluation, not rating prediction.
- MovieLens users are not DeepCine users. Never import these interactions into production watch history.
- The hybrid weights are fixed; tune them only on a validation split, never on the final test set.
- Compare against baselines and report the exact dataset, threshold, split, and catalog size with every result.
