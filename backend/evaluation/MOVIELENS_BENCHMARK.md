# MovieLens Phase 2 evaluation

Run from `backend/` with the project virtual environment active:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/test_evaluate_movielens.py -q
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000
```

The script streams MovieLens ratings, maps movie IDs to the current DeepCine catalog, and keeps the latest rating for each user/movie pair before applying the positive threshold.

## Phase 2 methodology

- Per-user chronological 60/20/20 train/validation/test split. Users need at least three positive catalog interactions.
- ALS, content user profiles, popularity counts, and genre profiles are built from training interactions only.
- Baselines: global training popularity, personalized popularity using training-derived genre affinity, content, ALS collaborative.
- RRF weights are selected from an 81-point deterministic grid using validation NDCG@10 (or the largest requested K if K=10 is absent). To keep per-user ranking computation practical, the benchmark evaluates a seeded uniform sample of up to 2,000 eligible users by default (`--evaluation-users`). The full eligible training partition is used to fit ALS and calculate training-derived popularity statistics. A seeded uniform sample of up to 2,000 eligible users is used to materialize per-user rankings and calculate validation/test metrics. The benchmark records both the full eligible population and sampled count. Set a larger value to evaluate more users, at a higher ranking/evaluation cost. Weight tuning uses up to 2,000 users from that evaluation sample.
- The held-out test partition is used only for final reporting; it does not select weights.
- ALS uses a fixed seed and BLAS thread pools are limited to one during fitting/scoring.
- Phase 3 JSON and CSV use the `movielens_phase3_` prefix and include full eligible-user count, full model-fit training population, sampled evaluation-user count, split sizes, tuning configuration, validation metrics, and final test metrics.

## Important interpretation

The candidate universe remains the MovieLens/DeepCine overlap, not the full 414-title catalog. This is implicit top-N retrieval evaluation, not rating prediction. It is a per-user chronological split, not a global calendar-time split. Metrics estimate performance on the sampled users and are not exact full-population metrics. ALS and train-derived popularity use all eligible users, while recommendation lists and reported metrics are generated for the sampled evaluation users. Do not use test metrics to tune weights.
