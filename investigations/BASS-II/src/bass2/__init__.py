"""bass2 — flame-spread analysis of NASA BASS-II (PSI-25) ISS videos.

Modules:
    config        load configs/*.yaml and project paths
    catalog       NASA metadata, file inventory, cleaned experimental table
    download      resumable downloads through presigned URLs of the PSI API
    video         frame reading, pixel-aspect correction, OSD/ROI masks
    osd           template OCR of the burned-in telemetry (FUEL/AIR/FAN/RAD/clock)
    segmentation  segmentation of the luminous flame region
    metrics       per-frame geometric and photometric metrics
    spread        flame edges, spread rate and uncertainty
    forecast      forecasting models and rolling-origin evaluation
    evaluation    metrics (Dice/IoU, MASE, CRPS, coverage) and the scalar objective
    viz           standard scientific figures with captions
    pipeline      per-test orchestration (video -> series -> figures)
    cli           `bass2` command-line interface
"""

__version__ = "0.1.0"
