# MovieLens benchmark — Phase 5 independent-cohort evaluation

Run from `backend/` with the project virtual environment active:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/test_evaluate_movielens.py -q
python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv --links-path ../datasets/movielens/links.csv --ks 5,10,20 --evaluation-users 2000 --validation-seed 42 --test-seed 43 --als-seed 42 --tuning-seed 42 --bootstrap-seed 42
```

The benchmark streams MovieLens ratings, maps movie IDs to the current DeepCine catalog, and keeps the latest rating for each user/movie pair before applying the positive threshold. It remains isolated from production `watch_history`.

## Phase 5 methodology

- Per-user chronological 60/20/20 train/validation/test split. Users need at least three positive catalog interactions.
- ALS, content user profiles, popularity counts, and genre profiles are built from training interactions only.
- Baselines: global training popularity, personalized popularity using training-derived genre affinity, production-faithful content retrieval (per-watched-item nearest neighbors under raw-vector L2, merged by minimum distance), cosine-profile content, and ALS collaborative.
- The validation cohort and test cohort are independently sampled from eligible users without replacement within each cohort. Use `--validation-seed` and `--test-seed` to control them independently. The cohorts may overlap by chance; they are not forced to be disjoint.
- Recommendation rankings are materialized for the union of both cohorts. ALS and train-derived signals are fitted once on the full eligible training population.
- RRF weights are selected from an 81-point deterministic grid using validation NDCG@10 (or the largest requested K if K=10 is absent). Tuning uses up to 2,000 users from the validation cohort, selected with `--tuning-seed`.
- After validation tuning, the selected weights are frozen. Test labels are not passed to tuning and test metrics are reported only after the weights are fixed.
- The default cohort size is up to 2,000 users each (`--evaluation-users`). Increase it for more precise population estimates at higher ranking/evaluation cost.
- ALS initialization, validation sampling, test sampling, tuning-user sampling, and bootstrap resampling have independent seeds: `--als-seed`, `--validation-seed`, `--test-seed`, `--tuning-seed`, and `--bootstrap-seed`.
- The legacy `--seed` sets validation, ALS, tuning, and bootstrap seeds when their specific flags are omitted. The test seed defaults to `--seed + 1`.
- Phase 5 JSON and CSV outputs use the `movielens_phase5_` prefix. Precision, recall, and NDCG include 95% percentile-bootstrap confidence intervals over the relevant cohort. Output also includes paired user-level bootstrap intervals for the held-out test difference between tuned hybrid and global popularity.

## Interpretation guardrails

The candidate universe remains the MovieLens/DeepCine overlap, not the full 414-title catalog. This is implicit top-N retrieval evaluation, not rating prediction. The split is chronological per user, not a global calendar-time split. MovieLens users are external benchmark users, not DeepCine production users.

The validation and test cohorts are independently sampled, but they can overlap by chance. This is not a disjoint-user generalization experiment. Bootstrap intervals quantify uncertainty across sampled users conditional on the run; they do not eliminate dataset bias, catalog truncation, temporal-split limitations, or MovieLens-to-production domain shift.

Do not select weights, model settings, or a preferred random seed based on test metrics. Use validation for decisions; test results are for final reporting only.


## Content retrieval fidelity

The primary `content` signal mirrors production `recommend_for_user_content`: raw SentenceTransformer vectors are indexed with FAISS `IndexFlatL2`; each training-watched item is queried independently; candidates are merged using their minimum L2 distance to any watched item; and watched items are excluded. The benchmark searches up to `max(30 * K_max, 50)` neighbors per watched item, matching production's default of 300 neighbors when `K_max=10` and `top_k=100`.

The separate `cosine_profile_content` baseline averages normalized watched-item embeddings into one profile and ranks by cosine similarity. It is not the production content algorithm; it is retained only to compare aggregation strategies. Both methods use training interactions only.
