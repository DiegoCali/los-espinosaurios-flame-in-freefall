# Empirical format probe (done on real files, 2026-11-12)

Files probed: `BASS_GMT50_SAMPLE_147_TEST_B1.mp4`, `BASS_GMT50_SAMPLE_227_TEST_F1_Still_Sequence.mp4`,
`GMT2014_202_BASS_S220M_TPO5b.zip`, `GMT2014_050_BASS_S227M_TPF1_ProofSheet.pdf`.

## Data access (NASA PSI public API)

| What | Endpoint |
|---|---|
| Full investigation metadata (JSON, ~680 KB, `added` list with 694 files) | `GET https://psi.nasa.gov/geode-py/ws/repo/investigations/PSI-25` |
| S3 presigned URL for a file (plain text, expires) | `GET https://psi.nasa.gov/geode-py/ws/studies/PSI-25/download?file=<file_name url-encoded>&redirect=false` |

- The `remote_url` field of legacy files (`psi.ndc.nasa.gov/...`) is **not publicly accessible**; always use the `download` endpoint.
- License: CC0-1.0. DOI: `10.60555/4qc4-de67`. Total size ≈ 274.6 GB (Raw Data 685 files).
- Implemented in `src/bass2/download.py`.

## Main video (`BASS_GMT###_SAMPLE_###_TEST_XX.mp4`)

- H.264 High, **720×480, 29.97 fps**, progressive, yuv420p, ~1 Mb/s, with an AAC audio track (crew/ambient audio).
- **Non-square pixel: SAR 10:11 (DAR 15:11)** → it is digitized NTSC video. A horizontal pixel measures 10/11 of a vertical one.
  Every horizontal pixel measurement must be multiplied by 10/11 before converting to mm, or the frame rescaled to 654×480.
- **Telemetry burned into the video (OSD)** in the top strip (rows ≈ 25–85 px):
  `FUEL  AIR  FAN  RAD` / values (e.g. `-1  5  61  1.10`) / `MM/DD/YY HH:MM:SS`.
  - Meanings confirmed by the NASA documents (see `bass2_dataset.md`):
    `AIR` = air velocity in cm/s (anemometer; NASA docs state a lag ≈ 1 min, the BASS-II telemetry shows ≈ 15–25 s after a fan step; `U = 1.0066·AIR`),
    `FAN` = 10 × fan voltage, `FUEL` = N₂ flow (vitiation), `RAD` = uncalibrated radiometer.
  - **The OSD date is 1 day ahead** (leap-year bug); the time is usable for alignment.
  - The clock gives absolute time (GMT/ISS time) → allows alignment with flow changes from the experimental table.
  - **Must be masked** before segmenting (it is bright white text) and can be **read by template OCR** (`src/bass2/osd.py`) to obtain telemetry series.
- Flame in B1 (PMMA 100 µm, opposed flow): appears **saturated magenta/pink** (camera saturates red+blue), two flame sheets (upper and lower sides of the film) advancing **to the left** (against the flow). Almost black background (mean RGB ≈ 5–8), max V = 255 → the flame core is saturated.
- B1: 1343 frames (44.8 s).

## `*_Still_Sequence.mp4`

- It is a **recording of the Nikon D300S camera review screen** (thumbnail + histogram + EXIF: `M 1/10 F2 ISO1000 35mm`, `4288x2848 RAW`, counter `192/208`).
- **Not usable for measurement** (tiny thumbnail), but useful to know shot timing and exposure parameters.

## Zips `GMT2014_###_BASS_S###M_TP##.zip`

- Contain **Nikon RAW `.NEF` images** (`iss040e071087.NEF`, ISS catalog names `issNNNeNNNNNN`), 4288×2848.
- Decodable with `rawpy` (installed in `.venv`); `postprocess(half_size=True)` → 2160×1434 RGB.
- Exposure 1/10 s, f/2, ISO 1000 → very noisy images (visible sensor noise); the flame appears as greenish/bluish bands.
- Useful as **frames with high spatial resolution but low temporal frequency** (≈ 1 image every ~1–2 s) → shape validation/spatial calibration, not for fast series.
- `original videos.zip`: original versions of the videos (pending inspection).
- `*_ProofSheet.pdf`: contact sheet of the NEF images.

## Implications for the pipeline

1. Main input: the main `.mp4` (+ `_2ND_VIEW` if it exists, for 3D/stereo).
2. Mandatory steps: correct SAR, mask OSD, convert to approximate linear luminance (inverse gamma 2.2) if intensity is integrated.
3. Core saturation makes the **luminous area** depend on the threshold → report threshold sensitivity.
4. OSD telemetry = covariates for the predictive model (FAN changes precede spread-rate changes).
