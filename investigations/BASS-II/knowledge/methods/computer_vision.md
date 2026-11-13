# Computer vision methods for BASS-II flame videos

> Methods knowledge base — computer vision.
> Scope: from the raw MP4 to calibrated time series (mm, s) of leading-edge position, area, length, width, standoff distance, intensity and spread rate.
> Sibling files: `time_series_forecasting.md`, `evaluation_protocol.md` (the latter includes the **Scientific figures** section).
> Last revised: 2026-11-12.

---

## 0. Physical and visual context of the problem

- **Experiment**: BASS-II (Burning and Suppression of Solids II) in the Microgravity Science Glovebox (MSG) on the ISS. A small wind tunnel provides forced flow from 0 to 40 cm/s, variable O2 (e.g. 15–22 % by volume, per `data/docs/Experimental table_BASS-II.csv`) and these samples: PMMA films (0.1–0.4 mm, 1–2 cm wide), PMMA slabs and rods, cotton-fiberglass fabric (SIBAL), Nomex and candles.
- **Typical appearance** in microgravity:
  - The flame is **dim and blue**: CH* (~431 nm) and C2* (Swan bands, ~516 nm) chemiluminescence falls mostly in the camera's B and G channels.
  - It has **yellow-orange soot zones**: gray-body radiation, strong in R and G and much brighter than the blue part.
  - The background is dark, there are reflections on the tunnel walls, and the glow of the **hot-wire igniter** is visible at the start of the test.
- **Flow configuration**:
  - **Opposed flow**: the flame advances against the flow. The leading edge is the blue base, the dimmest part.
  - **Concurrent flow**: the flame advances with the flow. Its tip is longer and more yellow.
  - The "leading edge" must be defined **according to the propagation direction**, not along a fixed image direction.
- **Cameras**: color HD camcorders (MP4, H.264, probably 29.97 fps and possibly interlaced) plus still sequences. Some tests have a front view and a side view ("2ND_VIEW"). The side view allows measuring the standoff distance (flame–surface separation).
- **Methodological consequence**: a single luminance threshold is not appropriate. The blue part has a signal-to-noise ratio of 2 to 10 times the background noise, while soot saturates the sensor. Separate channels and thresholds are needed for the two components, together with an explicit operational definition of the edge.

BASS context references:
- NASA NTRS, BASS-II presentation: https://ntrs.nasa.gov/api/citations/20160000593/downloads/20160000593.pdf
- NASA NTRS, BASS (2014): https://ntrs.nasa.gov/api/citations/20140011099/downloads/20140011099.pdf
- Flammability limits BASS-II vs 1g (TTU ICES): https://ttu-ir.tdl.org/items/1922ad9f-ef4c-4f52-96a4-980c23debe5e
- Boundary-layer effect on opposed-flow flame spread in microgravity (Bhattacharjee/Carmignani): https://ttu-ir.tdl.org/items/41223c66-e96b-4a7e-b390-464e5241e88e
- Effect of gravity on flame spread over PMMA cylinders (Sci. Rep. 2018): https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5760683/
- Local documents: `data/docs/Reports_BASS-II Summary Report.pdf`, `Science Documents_BASS-II_SRD.pdf`, `Science Documents_BASS-II_Test.Matrices.xlsx`.

---

## 1. Video ingestion and decoding

### 1.1 Reading with real timestamps
- Use **PyAV** (`av`) to read frames with their `pts` and `time_base`. The time of each frame is then `t = pts * time_base` rather than `i / fps`. This matters because camcorder MP4s may have VFR, duplicated frames or dropped frames.
- `cv2.VideoCapture` is fine for prototypes, but its `CAP_PROP_POS_MSEC` is unreliable under VFR.
- **Duplicated frames** must be detected; they are typical of pulldown or cadence conversion: when `mean(|f_i − f_{i−1}|)` is below ε, mark `dup=True` and exclude the frame from the derivative.
- Store a `video_meta.json` per video with codec, resolution, nominal fps, `field_order`, number of frames, duration and SHA-256 hash of the file.
- PyAV docs: https://pyav.basswood-io.com/docs/stable/ — FFmpeg ffprobe: https://ffmpeg.org/ffprobe.html

### 1.2 Interlacing
- **Detection**: `ffmpeg -i in.mp4 -vf idet -frames:v 500 -an -f null -` reports how many frames are TFF, BFF or progressive. A custom metric also works: the energy of the difference between even and odd rows at the edges of the moving flame ("combing").
- **Correction**:
  - If the video is interlaced, apply `bwdif` or `yadif` in `send_field` mode (`yadif=1`). This **doubles the temporal resolution** (59.94 fields/s) at the cost of half the vertical resolution (interpolated).
  - Alternatively, split the fields manually (`frame[0::2]`, `frame[1::2]`) and rescale vertically. The ½-line offset between fields must be corrected, otherwise a 0.5 px vertical jitter is introduced.
- idet filter: https://ffmpeg.org/ffmpeg-filters.html#idet — bwdif/yadif: https://ffmpeg.org/ffmpeg-filters.html#bwdif

### 1.3 Gamma, range and compression
- Consumer H.264 normally uses **limited range (TV range, Y∈[16,235])**, the **BT.709** matrix and a gamma transfer curve (~2.2 or 2.4, plus the camcorder "knee").
  - First convert to float RGB with the correct matrix and range: PyAV provides `frame.to_ndarray(format="rgb24")` and does this correctly if the metadata are correct; verify with `ffprobe -show_streams`, fields `color_range` and `color_space`.
  - To measure intensity, **linearize approximately**: `I_lin ≈ ((V/255))^γ`, with γ≈2.2. Only then does the integrated intensity area have a relative physical meaning.
  - The real camcorder curve is unknown, so intensity is reported in **relative units**, not as radiance.
- **Compression artifacts**:
  - 8×8 or 16×16 blocks in dark areas and background "banding".
  - Chroma is **4:2:0 subsampled**: Cb and Cr have half the resolution in x and y. Color-based edges are therefore 2 px blurrier than luminance edges.
  - **Rule**: locate edges on luminance or on the full-resolution B channel, and use chroma only to *classify* the pixel type (blue or soot).
- **Noise**: the dark background suffers from quantization and sensor noise amplified by gain. A light spatio-temporal denoise is recommended before thresholding: bilateral, or a 3-frame temporal average on the static background (not on the flame).

### 1.4 Overexposure and blooming
- Soot and the igniter saturate the sensor (R or G channel = 255). This causes:
  - The **saturated area to overestimate** the real extent: blooming and optical halo.
  - The integrated intensity to be truncated.
- **Detection**: mask `sat = max(R,G,B) ≥ 250`. Report `frac_saturated` per frame. If `sat_area / flame_area` exceeds 0.2, flag the frame as "intensity unreliable".
- **Mitigation**:
  - Do not use the area of the saturated yellow component as "flame size" without a warning.
  - For the opposed-flow **leading edge**, use the blue component, which rarely saturates.
  - The blooming halo can be modeled as a wide PSF. A high luminance threshold (hysteresis-high) trims the halo.

### 1.5 Auto-exposure, auto-gain and auto-white-balance
Consumer camcorders adjust exposure, gain and WB automatically. When the flame grows or soot appears, the camera **darkens** the whole scene, and the blue flame may "disappear" below threshold even though it is physically still there.

**How to detect it**:
1. **Static reference ROIs**: regions that do not change physically, such as the sample holder, a tunnel plate or label, or the far background. Record per frame their per-channel median `m_ref,c(t)` and their 99th percentile.
2. **Change-point**: apply PELT or a simple CUSUM on `log m_ref(t)` (ruptures does not support Py3.14; see §9). A jump or ramp of `log m_ref` with no physical change in the ROI corresponds to an exposure or gain change.
3. **Noise as a gain cue**: the temporal variance of the dark background (σ² in the ROI) increases when gain goes up even if the median stays constant.
4. **WB**: the ratio `m_ref,B / m_ref,R` changes when the white balance changes.
5. **Metadata**: if the MP4 keeps per-frame camera metadata (rare in NASA exports), use them directly. Otherwise, only inference remains.

**How to compensate**:
- **Relative-gain normalization**: `I'_c(t) = (I_lin,c(t) − b_c(t)) / g_c(t)`, where
  - `g_c(t) = (m_ref,c(t) − b_c(t)) / (m_ref,c(t0) − b_c(t0))` is estimated on an *illuminated* reference ROI;
  - `b_c(t)` is the black level (1st percentile of the background).
  - This is only valid in **linearized** space.
- If there is no stable illuminated ROI, apply **background histogram matching** (`skimage.exposure.match_histograms`) against a reference frame, only on background pixels (outside the dilated flame mask).
- **Per-frame adaptive thresholds** (defined as multiples of the background noise, `k·σ_bg(t)`) instead of absolute thresholds. This is the most robust approach.
- **Flag the segments** with an exposure change (`ae_event=True`) and exclude or down-weight them in intensity metrics. Edge position usually remains valid if the threshold is relative.
- References:
  - ruptures (reference for the PELT algorithm; not installable on 3.14): https://centre-borelli.github.io/ruptures-docs/
  - skimage exposure: https://scikit-image.org/docs/stable/api/skimage.exposure.html

### 1.6 Tunnel-wall reflections and glare
- The tunnel walls (polycarbonate or glass) and metal surfaces produce **specular images of the flame**: shifted, dimmer copies. Igniter reflections also appear.
- **Mitigation**:
  1. **Geometric ROI mask** per test and view: a polygon containing the sample and the physically possible flame region. It is defined once per camera configuration and is the most effective measure.
  2. **Main connected component**: keep the largest connected component that touches, or is within *d* mm of, the sample line.
  3. **Geometric consistency**: a reflection on a wall parallel to the focal plane appears with an almost constant shift. It can be detected by cross-correlating the mask with shifted versions of itself.
  4. If two views are available, cross-view consistency rejects objects that do not exist in 3D.

### 1.7 Hot-wire igniter glow
- The hot wire glows orange or red and saturates before and during ignition, and keeps a residual glow after being switched off.
- **Treatment**:
  - There is a fixed igniter ROI per test. It is excluded from the flame mask **until** the flame separates from the igniter by more than *d_ign* (e.g. 3 mm) or until *t_ign* + Δ.
  - The igniter signal itself (the intensity in its ROI) is used as an **ignition time marker**: the test's `t = 0` is the instant the igniter switches off, or the first frame with a separated flame.
  - Its spectrum (gray body, R ≫ B) allows distinguishing it from the blue flame by chroma.
- The ignition transient does **not** belong to the steady propagation regime: it is excluded from spread-rate fits (see §7).

---

## 2. Frame normalization

Per-frame steps, in this order:
1. Decode to float32 RGB in the range [0,1].
2. Deinterlace if applicable.
3. Linearize with γ.
4. Subtract the **dark background frame** `B(x,y)`: the median of the N pre-ignition frames with the igniter off or, if there are none, the temporal median of the flame-free frames. This step removes the static background, the hot-pixel pattern and pilot lights.
5. Correct the gain (§1.5).
6. Perform **registration and stabilization** if the camera or glovebox vibrates, which is rare on the ISS but possible: phase correlation (`cv2.phaseCorrelate` or `skimage.registration.phase_cross_correlation`) on a static ROI with edges, with subpixel precision (`upsample_factor=20`).
7. **Rectify** with the homography (§6) to a sample coordinate system: `x` along the sample in the flow direction and `y` perpendicular, in mm.
8. Store the derived channels per frame:
   - `L` (linear luminance);
   - `B_lin`;
   - `Soot = R_lin − α·B_lin`, or the soot mask;
   - `Blue = B_lin − β·R_lin` (chemiluminescence enhancement);
   - `Cb`, `Cr`, `H`, `S`, `V`.

---

## 3. Segmentation of the luminous flame region

### 3.1 Channels: blue flame (CH*/C2*) vs soot luminosity
- An RGB camera mixes chemiluminescence and soot:
  - CH* (431 nm) falls mostly in **B**;
  - C2* (473/516 nm) falls in **G** and partly in B;
  - soot (gray body at 1500–2000 K) falls in **R > G > B**.
- They cannot be separated exactly without knowing the spectral sensitivities. A practical 2-component approximation:
  - `blue_index = B_lin / (R_lin + G_lin + B_lin + ε)` (blue chromaticity) together with `B_lin` above noise → **blue zone**;
  - `R_lin > k_s·σ_bg` with `R/B > 1.5` → **soot zone**;
  - **total flame** = union of the two.
- To estimate a linear *unmixing*, solve `[R,G,B] = a·s_soot + b·s_chem` per pixel with non-negative least squares (`scipy.optimize.nnls`). The signatures `s_soot` (from clearly sooty yellow pixels) and `s_chem` (from blue base pixels) are taken from each video. This yields the maps `a(x,y)` (soot) and `b(x,y)` (chemiluminescence).
- References:
  - C2*→G and CH*→B correspondence in color cameras vs an ICCD: https://www.aminer.org/pub/56d8e7b7dabfae2eee3bf05c/analysis-of-chemiluminescence-measurements-by-grey-scale-iccd-and-colour-digital-cameras
  - Natural flame luminosity in color and hyperspectral reconstruction (Sci. Rep. 2023): https://www.nature.com/articles/s41598-023-29673-y
  - Flame measurements with an RGB camera and chemiluminescence (Measurement Science Review 2022): https://www.measurement.sk/2022/msr-2022-0016.pdf

### 3.2 Color-space thresholds
| Space | Recommended use | Note |
|---|---|---|
| **HSV** | Classify hue: blue (H≈200–260°) vs yellow-orange (H≈15–60°) | H is unstable when S and V are low: apply hue rules only if V > V_min and S > 0.15 |
| **YCbCr** | Classic fire rules (Çelik & Demirel 2009): for soot, `Y>Cb`, `Cr>Cb`; for the blue flame they are **inverted**: `Cb > Cr`, `Cb > 128+δ` | They must be adapted: the published rules target yellow 1g fire, not blue microgravity flames |
| **CIE Lab** | `b*` < 0 marks blue and `b*` > 0 yellow; `L*` gives perceptual lightness | Useful for clustering (k-means with k=3 or 4: background, blue, soot and reflection) |
| **Linear RGB** | Relative physical intensity and integrals | It is the basis of §3.1 |

- Çelik & Demirel, *Fire Safety Journal* 44(2), 2009: https://i-rep.emu.edu.tr/items/fb1bf81f-9413-419f-ba08-c9b94a1fe826
- Fuzzy variant (Çelik, Özkaramanlı, Demirel): https://i-rep.emu.edu.tr/items/06555e27-62f9-473e-84de-cbbf024f6148/full
- OpenCV, color conversion: https://docs.opencv.org/4.x/de/d25/imgproc_color_conversions.html

### 3.3 Automatic thresholds
- **Otsu** (`skimage.filters.threshold_otsu`): works if the histogram is bimodal (flame vs background). With a dim flame covering less than 2 % of the image, Otsu on the full image fails because the background dominates. It must be applied **on the ROI** or on pixels with `L > 90th percentile`.
- **Multi-Otsu** (`skimage.filters.threshold_multiotsu`, `classes=3`): naturally separates background, blue flame and soot or saturation. Recommended for initialization.
  - https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_multiotsu.html
- **Triangle / Li / Yen**: usually better than Otsu for small bright objects on a dark background. Triangle works well with long-tailed histograms.
  - https://scikit-image.org/docs/stable/auto_examples/applications/plot_thresholding_guide.html
- **Local adaptive** (`threshold_local` and `cv2.adaptiveThreshold`): **not recommended** as the primary method, because it invents edges in uniform background. It only makes sense under strong background illumination gradients.
- **Noise-based threshold** (the recommended default): `T_low = μ_bg + k_low·σ_bg`, `T_high = μ_bg + k_high·σ_bg`. Here μ and σ are robust (median and 1.4826·MAD) and are computed outside the dilated mask of the previous frame. Typical values are k_low=3 and k_high=8.

### 3.4 Hysteresis thresholding
- `skimage.filters.apply_hysteresis_threshold(img, low, high)`: keeps pixels above `low` that are connected to some pixel above `high`.
  - This is ideal for a dim blue flame connected to a brighter base: it recovers the dim tail without accepting isolated noise.
  - https://scikit-image.org/docs/stable/auto_examples/filters/plot_hysteresis.html
- It can be extended in time (**3D hysteresis**, x-y-t): "low" pixels must connect to a "high" pixel in the current frame or in its neighbors (±1 frame). This reduces mask flicker.

### 3.5 Background subtraction
- **Static**: `D = frame − B_dark` (§2). It is sufficient because the camera is fixed and the background does not change, except through AE.
- **Adaptive**: `cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)` or KNN.
  - **Caution**: these models absorb the flame if it stays still. In slow opposed flow the flame moves very slowly (on the order of mm/s), so it becomes part of the background. To mitigate this, use a very low `learningRate` (1e-4) or freeze the model after ignition.
  - https://docs.opencv.org/4.x/d1/dc5/tutorial_background_subtraction.html
- **The residue** of the burning material (pyrolyzed, darkened or melted sample) changes the background after the flame passes. This is an advantage for measuring burnout or the trailing edge, but a problem for static subtraction. For that, a *local per-column x* background model is used, updated only where the flame has already passed.

### 3.6 Morphology and post-processing
1. `remove_small_objects(min_size = 0.5 mm²)`.
2. `binary_closing` with a 0.3–0.5 mm disk.
3. `remove_small_holes`.
4. Keep the main component anchored to the sample (§1.6).
5. Contour smoothing: `cv2.approxPolyDP`, or a Gaussian filter on the SDF (signed distance function) followed by a threshold at 0. The second option avoids JPEG "teeth".

### 3.7 Watershed
- Used to **separate** blue and soot regions that touch, or the flame from an attached reflection. Apply `skimage.segmentation.watershed` on the gradient or on `−L`, with markers taken from the maxima of each component.
- Also used to **refine the edge** between sure-background (L < T_bg) and sure-flame (L > T_high) markers. This is the "marker-controlled" version.
- https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_watershed.html

### 3.8 Active contours and level sets
- **Chan-Vese** (`skimage.segmentation.chan_vese` and `morphological_chan_vese`): region-based rather than gradient-based, so it is robust to diffuse and dim edges. Very well suited to the blue flame.
- **Morphological geodesic active contour** (`morphological_geodesic_active_contour`): edge-based, preferable when the contour is sharp.
- **Initialization**: the hysteresis-threshold mask. 20–50 iterations are enough. It is expensive (~50–200 ms/frame at 1080p), so it is applied only on the cropped ROI.
- https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_morphsnakes.html
- https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_chan_vese.html

### 3.9 Foundation models: SAM / SAM2 zero-shot
- **SAM2** (Meta, 2024) segments images and **video with temporal memory**: given a prompt (point or box) on one frame, it propagates the mask to the others.
  - Use here: generate *pseudo-labels* and reference masks for the gold set, and compare against the classical pipeline.
- **Limitations**:
  - It is trained on objects with well-defined edges; the dim, semi-transparent blue flame is out of distribution.
  - It tends to follow the contour of the bright soot zone and miss the blue base.
  - Video propagation may "drift" to the reflection.
  - Mitigation: apply SAM2 on the **enhanced** image (Blue channel stretched with γ=0.5 or CLAHE and replicated to 3 channels), use positive prompts on the blue base and negative prompts on reflections, and re-inject prompts every N frames.
- **Installation on Python 3.14**:
  - The PyPI package `sam2` (1.1.0, Dec 2024) is published only as an **sdist** and compiles a CUDA extension, so it is fragile on Windows.
  - **Using SAM2 via `transformers` is recommended** (`Sam2Model` and `Sam2Processor` for images, `Sam2VideoModel` with `propagate_in_video_iterator` for video), which is pure-Python on top of `torch`.
  - Docs: https://huggingface.co/docs/transformers/model_doc/sam2 , https://huggingface.co/docs/transformers/model_doc/sam2_video
  - Weights: https://huggingface.co/facebook/sam2-hiera-large (also `-small` and `-tiny`; on a consumer GPU, small or base-plus work well).
  - **SAM3 Tracker** and **EdgeTAM** are available in transformers as more recent or lighter alternatives: https://huggingface.co/docs/transformers/model_doc/sam3_tracker_video

### 3.10 U-Net fine-tuning with weak labels
- **Motivation**: the classical pipeline fails systematically in certain cases (reflections, blue-soot transition). A small U-Net learns the operational definition of "flame" from a few labels.
- **Data**:
  - **Weak labels** = high-confidence classical-pipeline masks (hysteresis with large k_high and frames without `ae_event`), together with SAM2 masks that agree with the classical ones (IoU > 0.8).
  - They are combined with the **gold set** (`evaluation_protocol.md` §2): ~300 hand-labeled frames.
  - Uncertain pixels (disagreement between sources) are marked with `ignore_index` so they do not count in the loss.
- **Model**: `segmentation-models-pytorch` with a lightweight encoder (`resnet18`/`efficientnet-b0` ImageNet-pretrained) and Unet, at a 512×512 input cropped to the rectified ROI.
  - Input: 3 or 4 channels (L, Blue, Soot, optionally the difference with the previous frame).
- **Loss**: Dice + BCE (or Focal, since classes are imbalanced). Optionally, a **boundary loss** or a higher weight for pixels within 1 mm of the leading edge.
- **Augmentations**:
  - Photometric ones that simulate AE: gain scale ×[0.5, 2], gamma [0.8, 1.25], Gaussian and Poisson noise, and JPEG/H.264 re-encode.
  - Horizontal flips only if the flow direction is relabeled.
  - Small rotations (±3°).
- **Split scheme**: **by test** (leave-tests-out), never by frame (see `evaluation_protocol.md`).
- **Size**: 30–50 epochs, batch 8, AdamW lr=3e-4 with cosine. Takes under 20 minutes on a consumer GPU.
- Iterative *self-training* refinement: prediction, confidence filtering, re-training (1–2 rounds at most, to avoid amplifying biases).
- smp: https://github.com/qubvel-org/segmentation_models.pytorch — Original U-Net: https://arxiv.org/abs/1505.04597 — Weak supervision in segmentation: https://arxiv.org/abs/1502.02734 (BoxSup/weakly-sup., Dai et al.).

### 3.11 Temporal smoothing and tracking
- **Mask smoothing**: per-pixel majority voting over a 3–5 frame window, or 3D hysteresis (§3.4). Long windows must be avoided, because they introduce lag at the edge.
- **Smoothing of scalar signals**:
  - The series `x_LE(t)`, `A(t)` and similar are **not** smoothed before estimating the rate: the slope estimator (§7) already smooths.
  - For visualization, use a moving median (outliers) followed by Savitzky-Golay.
- **Tracking**:
  - For the main flame, association by mask overlap (IoU between consecutive frames) plus the constraint that it is anchored to the sample is enough.
  - For several flames or fragments (e.g. on SIBAL fabric, or with local extinction and reignition), Hungarian association (`scipy.optimize.linear_sum_assignment`) on centroids and IoU works.
- **Constant-velocity Kalman** on `x_LE(t)`: detects outliers (innovation above 4σ) and fills gaps of frames without detection. See `time_series_forecasting.md` §4.
- **Optical flow** (`cv2.calcOpticalFlowFarneback` or RAFT): does **not** measure propagation well, because the flame is not a material object being translated. It is useful only for stabilization or for estimating the apparent velocity of soot structures (gas flow).

---

## 4. Per-frame geometric measurements

All are computed in rectified coordinates (mm). `x` is the position along the sample, positive in the forced-flow direction; `y` is the direction perpendicular to the surface (side view) or transverse across the width (front view).

| Quantity | Operational definition | Implementation |
|---|---|---|
| Area `A` | Number of mask pixels × (mm/px)² | `regionprops.area` |
| Blue area / soot area | Areas of the §3.1 submasks | |
| Centroid `(x_c, y_c)` | Weighted mean (geometric or intensity-weighted) | `regionprops.centroid` / `centroid_weighted` |
| **Leading edge `x_LE`** | Most advanced position in the propagation direction: in opposed flow it is the minimum `x` (upstream); in concurrent, the maximum | Profile §5 |
| Trailing edge `x_TE` | Opposite end of the flame (burnout or tail) | Profile §5 |
| Length `L_f` | `|x_LE − x_TE|` | |
| Width `W_f` | y-extent of the mask (percentiles 2–98 to avoid the influence of stray pixels) | |
| Standoff `δ` | In the side view, distance between the sample surface (calibrated line) and the blue-flame isoline at `x_LE + Δx` (e.g. 2 mm), or the minimum distance | Profile in y |
| Shape | Eccentricity, solidity, aspect ratio, perimeter²/(4πA), Hu moments, orientation | `regionprops` |
| Intensity | Sum of `L_lin` in the mask, mean intensity, p95, saturated fraction | relative (see §1.3) |
| Quality | `qc_flags`: `sat`, `ae_event`, `dup`, `igniter`, `n_components`, `edge_snr` | |

- regionprops: https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.regionprops

---

## 5. Subpixel leading-edge extraction

1. **Profile along the flow axis**:
   - Take a band of height `h` (e.g. the central 50 % of the sample width, or the band adjacent to the surface in the side view).
   - Reduce it to a 1D profile `p(x) = percentile_{y∈band}(I(x,y), 90)` or the mean. The 90th percentile is robust to flames that are non-uniform in y.
   - Use the **Blue** or **L** channel depending on the flame type.
2. **Threshold crossing**:
   - The threshold is defined as `T = μ_bg + k·σ_bg`, with k=4 by default, or as a **fraction of the peak**: `T = μ_bg + f·(p_max − μ_bg)`, with f=0.2.
   - The noise-relative threshold **is recommended** as the primary metric, with the peak fraction as an alternative. The sensitivity of `V_f` to k (k=3, 4, 6) must be reported. If the rate does not depend on k, the measurement is robust.
3. **Subpixel**:
   - Locate the first crossing from the front side (from outside the flame inward) and **interpolate linearly** between the two pixels flanking the crossing: `x* = x_i + (T − p_i)/(p_{i+1} − p_i)`.
   - Before interpolating, smooth the profile with a Gaussian σ=1 px to reduce quantization noise.
   - Alternatively, fit a sigmoid or erf `p(x) = a + b·Φ((x−x0)/s)` around the crossing (`scipy.optimize.curve_fit`). This yields `x0` with its uncertainty σ_x0 from the covariance, plus `s` (edge width) as a focus and blooming diagnostic.
4. **Validation**:
   - If `edge_snr = (p(x*+3px) − μ_bg)/σ_bg` is below 3, the edge is flagged as unreliable.
   - Jumps larger than `v_max·Δt + 3σ` are treated as outliers, detected with the Kalman filter (§3.11).
5. The same procedure applies to `x_TE` in the opposite direction and to the standoff in y.

Expected precision: between 0.1 and 0.3 px of noise in `x*` for an edge SNR of 10 or more. At ~0.05–0.1 mm/px, this is ~0.01–0.03 mm.

- Subpixel edge (Devernay 1995): https://inria.hal.science/inria-00074221/document

---

## 6. Pixel→mm calibration and perspective correction

- **Available fiducials**:
  - the **known sample width** (1 or 2 cm for PMMA films, per the experimental table);
  - the rod diameter;
  - the sample holder length and ruler marks, if present on the holder;
  - the spacing of the frame screws.
  - Verify them in `Engineering Documents_BASS-II_Engineering Requirements.pptx` and in the representative images.
- **Simple calibration (isotropic scale)**:
  - Measure the sample edges on a pre-ignition frame with a transverse profile and subpixel edges. Then `s = W_mm / W_px`.
  - Measure at several x positions. If `s` varies by more than 2 % along x, there is perspective and a homography is needed.
- **Homography**:
  - Mark ≥4 coplanar points on the sample plane (frame or holder corners) with known coordinates in mm, and use `cv2.findHomography(src, dst, cv2.RANSAC)` followed by `cv2.warpPerspective`.
  - This corrects the camera tilt relative to the sample plane.
  - **Limitation**: the homography is exact only *on the sample plane*. The flame has thickness (standoff of several mm), so out of plane a parallax error occurs. In the front view this error is small for `x_LE` (the base is attached to the surface).
- **Lens distortion**: zoom camcorders have barrel distortion. If there is no calibration pattern (checkerboard), estimate a single-parameter `k1` model from known straight lines (frame edges), using `cv2.undistort` with k1 tuned to minimize the curvature of those lines. If `|Δ| < 0.5 px` in the ROI, ignore it.
- **Per configuration**: the calibration is stored per (test, view) in `calib/<test>_<view>.json`: homography H, scale, k1, ROI, igniter ROI, flow direction and date. If the camera did not move, it is reused across consecutive tests, verified by phase correlation of the background.
- **Scale uncertainty**: `σ_s/s = sqrt((σ_Wpx/W_px)² + (σ_Wmm/W_mm)²)`. With W_px ~ 200 px and σ_Wpx ~ 0.5 px, it is ~0.3 %, negligible compared with the rate uncertainty.
- **Synchronizing the two views** (front and 2ND_VIEW): done with the ignition event or igniter switch-off, and refined by cross-correlation of `A(t)` between views.
- OpenCV, calibration and homography: https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html , https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html

---

## 7. Spread-rate estimation `V_f = |dx_LE/dt|`

### 7.1 Regime window
- Exclude the ignition transient (`t < t_ign + τ_ign`, typically 2–5 s or until the flame separates from the igniter by more than 3–5 mm) and the final phase (arrival at the end of the sample or extinction).
- The steady window is detected with change-point (PELT on the local slope) or with the criterion that the local slope remains stable (CV < 15 %) for 5 s or more.

### 7.2 Estimators
| Method | Use | Details |
|---|---|---|
| **Global OLS** over the steady window | Per-test summary value `V_f`, comparable with the literature | `scipy.stats.linregress`. Report slope ± SE, R² and residuals |
| **Sliding-window linear regression** | Time series `V_f(t)` | window `w` = 2–5 s (or ≥ 20 points), step of 1 frame; local SE of the slope |
| **Savitzky-Golay derivative** | Smooth `V_f(t)` | `scipy.signal.savgol_filter(x, window_length=w, polyorder=2, deriv=1, delta=Δt)`. Odd `w`, equivalent to 1–3 s. Requires uniform sampling: resample to a regular grid if frames are missing |
| **Robust: Theil-Sen** | With segmentation outliers | `scipy.stats.theilslopes` (gives a 95 % CI); `sklearn.linear_model.TheilSenRegressor` |
| **Robust: Huber / RANSAC** | With jump outliers | `sklearn.linear_model.HuberRegressor`, `RANSACRegressor` |
| **Kalman / RTS smoother** (constant velocity or constant acceleration) | `V_f(t)` with uncertainty, handles gaps | see `time_series_forecasting.md` §4 |
| **Parametric fit** | Deceleration or acceleration | `x(t) = x0 + V t + ½ a t²` or the models in `time_series_forecasting.md` §5 |

- **Resampling**: the raw series runs at ~30 or 60 Hz. For the rate, work at full resolution with long windows, or downsample by averaging to 5 Hz. The noise of `x_LE` is correlated across frames (H.264, AE), so the OLS SE **underestimates** the uncertainty (see §7.3).
- **Sign**: in opposed flow, `x_LE` decreases with time (the flame moves upstream), so `V_f = −dx_LE/dt > 0` is reported.

### 7.3 Uncertainty propagation
- **Components**:
  1. the random edge-position error, σ_x (subpixel, §5);
  2. the autocorrelation of the residuals;
  3. the scale error σ_s;
  4. the bias due to the choice of threshold k;
  5. the timing error (timestamps, nominal vs real fps);
  6. the choice of window.
- **Recommendation**:
  - Slope with **HAC/Newey-West** standard errors (`statsmodels` OLS with `cov_type="HAC", cov_kwds={"maxlags": m}`, with m ≈ 0.5 s in frames), or with a **block bootstrap** of the residuals (blocks of ~1 s, 1000 replicates).
  - Combine in quadrature: `σ_V² = σ_slope,HAC² + (V·σ_s/s)² + σ_k²`, where `σ_k` is half the range of V between k=3 and k=6, and `σ_window` comes from varying the window limits by ±20 %.
  - Report `V_f ± σ_V` (1σ) and the uncertainty breakdown.
- Docs: https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html , https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html , https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html

### 7.4 Validation against published values
- Compare the estimated `V_f` with the rates reported by the BASS-II Summary Report and the team's papers (NTRS and TTU ICES, see §0) for the same test (PI, Test #). The `spread-rate error` metric is defined in `evaluation_protocol.md`.
- Across all tests, check physical trends:
  - `V_f` increases with O2;
  - in thin films, `V_f ∝ 1/thickness` approximately (de Ris, thin fuel);
  - with opposed flow, `V_f` shows a maximum at low velocity (radiative vs kinetic regime). Reported by the BASS/rods studies: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5760683/
- A systematic violation of these trends indicates a pipeline error (calibration, sign, window).

---

## 8. Recommended default pipeline (concrete)

```
for each (test, view):
  0. meta  = ffprobe(video); detect interlace (idet). If interlaced → bwdif send_field.
  1. decode PyAV → RGB float32 [0,1], t = pts*time_base; flag duplicates (mean|Δ|<1e-4).
  2. linear = rgb**2.2 ; dark = median of pre-ignition frames (≥30) ; I = clip(linear-dark, 0)
  3. ROIs (from calib json): roi_flame, roi_ref (illuminated holder), roi_bg (dark background), roi_igniter.
     g(t) = median(I[roi_ref])/median(I[roi_ref] @ t0)  → I /= g(t)   (if roi_ref exists)
     ae_event = custom_PELT(log g(t), pen=BIC) ; σ_bg(t) = 1.4826*MAD(I[roi_bg])
  4. stabilize: phase_cross_correlation(static_roi, upsample=20); warpPerspective(H) → mm grid
     (rectification resolution: 0.05 mm/px or native, whichever is larger)
  5. channels: L = 0.2126R+0.7152G+0.0722B ; Blue = max(B - 0.5R, 0) ; Soot = max(R - 1.0B, 0)
  6. segmentation (per channel c ∈ {Blue, L}):
        smooth = gaussian(c, sigma=1.0 px)
        low  = μ_bg + 3σ_bg ; high = μ_bg + 8σ_bg
        m = apply_hysteresis_threshold(smooth, low, high)   # optional 3D hysteresis ±1 frame
        m &= roi_flame ; m &= ~igniter_mask(t)
        m = remove_small_objects(m, 0.5 mm²) → closing(disk 0.4 mm) → remove_small_holes(2 mm²)
        m = connected component anchored to the sample (dist ≤ 2 mm)
     flame = m_Blue ∪ m_L ; blue = m_Blue \ (Soot>high) ; soot = Soot>high
     (optional) refine with morphological_chan_vese(30 it) in bbox+5 mm
  7. measurements §4 ; leading edge §5 (band = central 50%, p90, k=4, linear interp + erf fit)
  8. QC flags; CV Kalman for outliers (gate 4σ) ; do NOT fill more than 0.5 s
  9. spread rate: steady window (PELT) → OLS + Theil-Sen + HAC SE ; V_f(t) with SavGol(w=2 s, p=2)
 10. output: parquet per test with t, x_LE, σ_x, x_TE, L_f, W_f, δ, A, A_blue, A_soot, I_sum, flags.
```

Fallbacks and improvements:
- If evaluation on the gold set gives Dice < 0.8 for some material type, train the U-Net (§3.10) with the weak labels and use it as the default segmenter for that material.
- SAM2 via transformers is used to assist gold-set labeling and as a comparator, **not** as the production segmenter, unless it wins under `evaluation_protocol.md`.

---

## 9. Libraries (pinned versions, compatible with Python 3.14 on Windows x64)

Verified on PyPI on 2026-11-12. In the "Wheel" column, `cp314` indicates a binary wheel specific to Python 3.14 on win_amd64; `abi3` and `py3` indicate compatible wheels; `pure` indicates pure-Python.

| Package | Version | Wheel | Use |
|---|---|---|---|
| numpy | 2.5.4 | cp314 | base |
| scipy | 1.18.1 | cp314 | signal (savgol), stats (theilslopes), optimize, ndimage |
| opencv-python (or `opencv-contrib-python`) | 5.0.0.93 | abi3 (cp37-abi3) | color, homography, morphology, MOG2, phaseCorrelate |
| scikit-image | 0.26.0 | cp314 | thresholds (multi-Otsu, hysteresis), regionprops, active contours, watershed, registration |
| av (PyAV) | 19.0.2 | cp314 | decoding with PTS |
| imageio | 2.38.1 | pure | still I/O |
| imageio-ffmpeg | 0.8.1 | py3 win_amd64 | embedded ffmpeg binary (idet, bwdif) |
| tifffile | 2026.11.12 | pure | 16-bit TIFF stills, if any |
| pandas | 3.1.1 | cp314 | per-frame tables |
| pyarrow | 26.0.1 | cp314 | parquet |
| matplotlib | 3.11.2 | cp314 | figures |
| shapely | 2.2.0 | cp314 | ROI and contour geometry |
| ~~ruptures~~ | 1.1.10 | **NO** (`requires_python <3.14`, wheels only up to cp313) | change-points: replaced by a **custom CUSUM/PELT** of ~40 lines with numpy (L2 cost + BIC penalty) or by `statsmodels` (Chow test / `breaks_cusumolsresid`) |
| statsmodels | 0.15.0 | cp314 | OLS with HAC |
| scikit-learn | 1.9.1 | cp314 | Huber, RANSAC, TheilSen |
| torch | 2.15.0 | cp314 | U-Net and SAM2. For CUDA, install from the corresponding `https://download.pytorch.org/whl/cu12x` index and verify that a cp314 wheel exists for that CUDA |
| torchvision | 0.29.2 | py3 | requires `!=3.14.1` (OK with 3.14.7) |
| segmentation-models-pytorch | 0.6.0 | pure | U-Net |
| kornia | 0.9.0 | pure | GPU augmentations (optional) |
| transformers | 5.22.2 | pure | SAM2 / SAM2-Video / SAM3-tracker |

**Not recommended**:
- `sam2` from PyPI (sdist only, compiles CUDA; use transformers).
- `decord` (no wheels since 2021).
- `ultralytics`: it is AGPL-3.0, which implies license obligations.

**Note on `autoresearch/`**: the current `pyproject.toml` pins `torch==2.9.1` and `.python-version` = 3.10, inherited from the nanochat template. For this project they must be updated to Python 3.14 and the versions in this table. (Note: the project code now lives in the package `src/bass2/` and the autonomous loop in `research/`.)

Example `pyproject.toml` (excerpt):
```toml
requires-python = ">=3.14"
dependencies = [
  "numpy==2.5.4", "scipy==1.18.1", "opencv-python==5.0.0.93", "scikit-image==0.26.0",
  "av==19.0.2", "imageio==2.38.1", "imageio-ffmpeg==0.8.1", "pandas==3.1.1", "pyarrow==26.0.1",
  "matplotlib==3.11.2", "shapely==2.2.0", "statsmodels==0.15.0", "scikit-learn==1.9.1",
]
[project.optional-dependencies]
dl = ["torch==2.15.0", "torchvision==0.29.2", "segmentation-models-pytorch==0.6.0",
      "transformers==5.22.2", "kornia==0.9.0"]
```

---

## 10. Risks and quick checks

- [ ] The flow direction and the sign of `x` are defined per test (opposed or concurrent).
- [ ] `t=0` comes from the igniter event, not from the start of the file.
- [ ] Calibration was done with the correct sample width: 1 or 2 cm per the table, and the *film* width is not the *holder* width.
- [ ] The % of frames with `ae_event`, `sat` and `dup` is reported.
- [ ] The sensitivity of `V_f` to the threshold k is smaller than the statistical uncertainty.
- [ ] Visual inspection: overlay and kymograph (see "Scientific figures" in `evaluation_protocol.md`) of each test before accepting its numbers.
