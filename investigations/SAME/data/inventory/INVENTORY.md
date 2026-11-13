# SAME-R raw data inventory (PSI-101)

Source folder: `data/` (230 files, 5.76 GB). Files are read-only inputs; nothing in the raw folder is modified.

| Category | Files | Size (MB) |
|---|---:|---:|
| coagulation_reference | 1 | 0.1 |
| engineering_document | 1 | 0.5 |
| housekeeping_timeseries | 44 | 27.7 |
| precipitator_map | 1 | 0.0 |
| reduced_moment_table | 2 | 28.6 |
| run_spreadsheet | 5 | 27.8 |
| tem_image | 3 | 1.8 |
| tem_image_archive | 70 | 1231.6 |
| tem_particle_sizing | 3 | 1.0 |
| tem_presentation | 84 | 271.1 |
| video | 16 | 4167.8 |

Runs referenced by TEM file names: 49, 50, 51, 52, 53, 54, 55, 56, 58, 60, 62, 63, 64, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 87, 93, 94, 95, 96, 97, 98, 100, 101, 105, 106, 107, 108.

Name parsing rule: the SAMERFLT sample number plus 47 equals the run number (e.g. `53T` = run 100). Files whose leading number disagrees, or that the source itself labels as wrong/mislabeled, are flagged in `label_flags`.

Hashes: SHA-256 of the whole file up to 64 MB; for larger videos/archives the hash covers file size plus the first and last MiB (`hash_kind`).

## Label warnings

- `#64 preage - 16P - Pyrell.zip`: run_64_but_sample_code_implies_63
- `#73 mis labeled pyrellpreage 26K Kapton.zip`: source_label_warning
- `#73 mislabeled pyrell postage 26K Kapton.zip`: source_label_warning
- `2010_210_10_lampwick_run55 wrong.xls`: source_label_warning
- `2010_211_13_silcon_run59 wrong seems to be 60.xls`: source_label_warning
- `96 48L Lampwick.pptx`: run_96_but_sample_code_implies_95
