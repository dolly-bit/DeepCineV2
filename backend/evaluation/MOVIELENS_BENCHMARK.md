# MovieLens Phase 2 evaluation

Run from `backend/` with the project virtual environment active:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/test_evaluate_movielens.py -q
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20
```

The script streams MovieLens ratings, maps movie IDs to the current DeepCine catalog, and keeps the latest rating for each user/movie pair before applying the positive threshold.

## Phase 2 methodology

- Per-user chronological 60/20/20 train/validation/test split. Users need at least three positive catalog interactions.
- ALS, content user profiles, popularity counts, and genre profiles are built from training interactions only.
- Baselines: global training popularity, personalized popularity using training-derived genre affinity, content, ALS collaborative.
- RRF weights are selected by a deterministic grid search using validation NDCG@10 (or the largest requested K if K=10 is absent).
- The held-out test partition is used only for final reporting; it does not select weights.
- ALS uses a fixed seed and BLAS thread pools are limited to one during fitting/scoring.
- JSON and CSV include split sizes, tuning configuration, validation metrics, and final test metrics.

## Important interpretation

The candidate universe remains the MovieLens/DeepCine overlap, not the full 414-title catalog. This is implicit top-N retrieval evaluation, not rating prediction. It is a per-user chronological split, not a global calendar-time split. Do not use test metrics to tune weights.
