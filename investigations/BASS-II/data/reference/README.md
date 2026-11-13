# Reference data (external ground truth)

`published_rates.csv`: published flame spread rates per test and flow step.
Full sources and context in `knowledge/literature/publications.md` §2.

- B#: SDSU (http://flame.sdsu.edu/bass.html), side view (video) and top view (Nikon). Reproducibility ±5 %.
- M#: NASA/TM-20210011385 (BASS-II Summary Report) Table 5.1, measured with Spotlight-16.
- `sigma_rel`: assumed relative uncertainty (5 % stated by SDSU; 10 % for M, assumed).

**Anti-overfitting rule**: the pipeline code (`src/bass2/pipeline.py`, `research/experiment.py`)
must NOT read this directory. Only the evaluation harness (`research/harness.py`) reads it.
Do not use these values to calibrate mm/px (that would be circular).


## Who reads this directory
Evaluation side only: `src/bass2/validation.py` (report statistics), `research/harness.py` (component R) and `scripts/compare_segmenters.py` (development-time segmenter comparison on B1, B2, B3, B4, B5, B7, B12, M1). Measurement code never reads it. Because the development tests were used to choose settings, their accuracy is in-sample; `configs/holdout_tests.yaml` lists slab tests evaluated only after all settings were frozen.
