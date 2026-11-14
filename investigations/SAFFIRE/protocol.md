# Saffire protocol v1

Data and selection decisions are documented in `DATA_PLAN.md`. Preparation, extraction, the relevance rubric, tests and processed data were frozen at `baseline-v1` for the experiment. Only `train.py` was editable during the search.

The budget is 15 attempts including the baseline. Each attempt requires passing tests, a commit and a clean Git tree. The experiment gate compares all changes against `baseline-v1`, runs the protected evaluator with a 60 s timeout and decides keep/discard using RMSE.

The minimum improvement is 0.1% of the best RMSE. Adding parameters requires at least 2% relative improvement per added parameter. Fitted parameters include the intercept and group locations or coefficients. Fixed penalties are described explicitly. Held-out targets must not be used to tune hyperparameters inside the external evaluation.

Interpretable candidate features include material groups, nominal/log thickness, a nonpositive silicone-thickness effect, airflow/dilution and programmed ignition conditions. Test IDs and per-test outcomes must not be encoded. A held-out categorical level needs a fallback derived solely from training data, without access to its target.

During the original search, results and logs were kept outside Git so restoring a candidate did not remove the evidence. Discarded commits were preserved under `refs/autoresearch/attempt-XX`. Only committed experimental state was restored. At completion, `baseline-v1..best_commit` was verified to contain only `train.py`.

The subsequent explanation and publication phase includes results, records and figures in Git. It can add or translate documentation and report generators while preserving the completed experimental commits and their evaluations. Historical comparison uses `2af682a96609f938a023eb5bf94d62441d4e0d4d`, not later publication commits. Translating this document does not change the experimental rules or restart the run.

Candidate selection repeatedly uses the same leave-one-out evaluation. The selected error is therefore optimistic. Nine rows in one flight do not provide an independent test set or establish causal effects or transfer to other missions.
