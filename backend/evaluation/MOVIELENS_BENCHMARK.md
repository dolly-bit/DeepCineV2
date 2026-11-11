# MovieLens benchmark — Phase 4 robustness evaluation

Run from `backend/` with the project virtual environment active:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/test_evaluate_movielens.py -q
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000
```

The script streams MovieLens ratings, maps movie IDs to the current DeepCine catalog, and keeps the latest rating for each user/movie pair before applying the positive threshold.

## Phase 4 methodology

- Per-user chronological 60/20/20 train/validation/test split. Users need at least three positive catalog interactions.
- ALS, content user profiles, popularity counts, and genre profiles are built from training interactions only.
- Baselines: global training popularity, personalized popularity using training-derived genre affinity, content, ALS collaborative.
- RRF weights are selected from an 81-point deterministic grid using validation NDCG@10 (or the largest requested K if K=10 is absent). To keep per-user ranking computation practical, the benchmark evaluates a seeded uniform sample of up to 2,000 eligible users by default (`--evaluation-users`). The full eligible training partition is used to fit ALS and calculate training-derived popularity statistics. A seeded uniform sample of up to 2,000 eligible users is used to materialize per-user rankings and calculate validation/test metrics. The benchmark records both the full eligible population and sampled count. Set a larger value to evaluate more users, at a higher ranking/evaluation cost. Weight tuning uses up to 2,000 users from that evaluation sample.
- The held-out test partition is used only for final reporting; it does not select weights.
- ALS uses a fixed seed and BLAS thread pools are limited to one during fitting/scoring.
- Phase 4 JSON and CSV use the movielens_phase4_ prefix. Evaluation sampling, ALS initialization, validation tuning, and bootstrap resampling have independent seeds (--evaluation-seed, --als-seed, --tuning-seed, --bootstrap-seed). The legacy --seed sets all four when specific flags are omitted. Precision, recall, and NDCG include 95% percentile-bootstrap confidence intervals over sampled users. Output also includes paired user-level bootstrap confidence intervals for the test-set difference between tuned hybrid and global popularity. Bootstrap is skipped during the 81-point tuning loop.

## Important interpretation

The candidate universe remains the MovieLens/DeepCine overlap, not the full 414-title catalog. This is implicit top-N retrieval evaluation, not rating prediction. It is a per-user chronological split, not a global calendar-time split. Metrics estimate performance on the sampled users and are not exact full-population metrics. ALS and train-derived popularity use all eligible users, while recommendation lists and reported metrics are generated for the sampled evaluation users. Do not use test metrics to tune weights.


## Phase 4 robustness protocol

A single run's confidence intervals quantify user-sampling uncertainty conditional on that run. They do not establish stability across random initializations or user cohorts.

### A. Evaluation-cohort stability (hold ALS fixed)

Keep ALS seed 42 and tuning seed 42; vary only evaluation seed:

```powershell
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000 --evaluation-seed 42 --als-seed 42 --tuning-seed 42 --bootstrap-seed 42
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000 --evaluation-seed 43 --als-seed 42 --tuning-seed 42 --bootstrap-seed 42
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000 --evaluation-seed 44 --als-seed 42 --tuning-seed 42 --bootstrap-seed 42
```

### B. ALS initialization stability (hold evaluation cohort fixed)

Keep evaluation seed 42 and tuning seed 42; vary only ALS seed:

```powershell
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000 --evaluation-seed 42 --als-seed 42 --tuning-seed 42 --bootstrap-seed 42
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000 --evaluation-seed 42 --als-seed 43 --tuning-seed 42 --bootstrap-seed 42
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000 --evaluation-seed 42 --als-seed 44 --tuning-seed 42 --bootstrap-seed 42
```

Compare test NDCG@10, Precision@10, Recall@10, catalog coverage, and paired hybrid-minus-popularity confidence intervals. Do not select a model based on whichever seed gives the best test score.

### Interpretation guardrails

- If the paired 95% interval for hybrid-minus-popularity NDCG@10 includes zero, this run does not establish a statistically clear ranking improvement over popularity.
- Narrow user-bootstrap intervals do not eliminate dataset bias, catalog truncation, temporal-split limitations, or MovieLens-to-production domain shift.
- Compare run-to-run ranges across controlled seeds. A ranking advantage that disappears under small seed changes is not robust enough to claim superiority.
- Keep test data out of tuning and model selection. Use validation for decisions; test results are for final reporting.
