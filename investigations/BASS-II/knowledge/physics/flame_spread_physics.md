# Physics of flame spread over solids in microgravity (BASS-II context)

> Base reference: **[TM]** = NASA/TM-20210011385, BASS-II Summary Report (2021), https://ntrs.nasa.gov/citations/20210011385. The equations in §2 and §5 are taken from sections 2.2, 2.3 and 6.1 of the TM, which reproduce Bhattacharjee et al., C&F 163 (2016) https://doi.org/10.1016/j.combustflame.2015.10.023, Bhattacharjee et al., FSJ 79 (2016) https://doi.org/10.1016/j.firesaf.2015.11.011, and Olson & Ferkul, C&F 180 (2017) https://doi.org/10.1016/j.combustflame.2017.03.001. Per-test values are in `../literature/publications.md`.
> General statements without a citation are textbook physics (de Ris 1969, Proc. Combust. Inst. 12:241; Fernandez-Pello & Hirano 1983, CST 32:1; T'ien et al. in *Microgravity Combustion: Fire in Free Fall*, 2001). **(inferred)** marks my own derivations or estimates.

---

## 1. Configurations: opposed vs concurrent

| | **Opposed-flow** (flame spreading against the flow) | **Concurrent-flow** (flame spreading with the flow) |
|---|---|---|
| Geometry | The flow $V_g$ reaches the flame from the virgin fuel side. The leading edge faces upstream | The flow pushes the flame over the virgin fuel downstream |
| Mechanism | Heat is transferred forward in a short preheat zone, $L_g\sim\alpha_g/V_g$ (~mm) | The long flame heats a downstream stretch of length ~ $L_f$ |
| Typical behavior | **Fast steady spread** (the flame reaches a fixed size within a few s) | **Growth → limiting length → steady spread** (if the sample is long enough) → decay at the end of the sample |
| BASS-II | B# (films), M# (slabs), P# (rods) | T# (SIBAL), O# (rods with stagnation tip) |
| BASS-I SIBAL values at 10 cm/s (2 cm wide) | 1.21 mm/s | 2.55 mm/s (NTRS 20130012832) |

In μg, at low flow, opposed spread can be faster than concurrent spread. Above a crossover flow, concurrent wins. Saffire at 20 cm/s is already above the crossover: concurrent 1.8 mm/s vs opposed 1.3 mm/s (Jomaas 2017, https://www.pure.ed.ac.uk/ws/files/31828517/The_Saffire_Experiment_2017_US_National_Meeting_Final.pdf).

---

## 2. Opposed-flow: de Ris theory and regimes

### 2.1 Leading-edge scales ([TM §2.3.3])
$$L_g\sim\frac{\alpha_g}{V_g},\qquad t_{g,res}\sim\frac{L_g}{V_g}=\frac{\alpha_g}{V_g^2},\qquad t_{s,res}\sim\frac{L_g}{V_f}=\frac{\alpha_g}{V_gV_f}$$

If $t_{g,res}\gg t_{g,chem}$ ("infinite" kinetics) and $t_{g,res}\ll t_{rad}$ (negligible radiation) hold, the flame is in the **thermal regime**.

### 2.2 Thermal regime: de Ris formulas
Flame coefficient: $F=\dfrac{T_f-T_v}{T_v-T_\infty}$. τ is the **half-thickness** and $\lambda_s$ the solid conductivity.

$$\boxed{V_{f,thin}=\frac{\pi}{4}\,\frac{\lambda_g F}{\rho_s c_s \tau}}\qquad\boxed{V_{f,thick}=\frac{\rho_g c_g\lambda_g}{\rho_s c_s\lambda_s}\,V_g\,F^2}$$

Numerically, for PMMA in 21 % air ([TM] eq. 2.11, SI, τ in m and $V_g$ in m/s):
$$V_{f,thin}=2.34\times10^{-8}\,F/\tau,\qquad V_{f,thick}=9.72\times10^{-5}\,V_g F^2$$

$F_{expt}=4.76$ and $F_{adb}=4.89$. Other values: $F_{deRis,lin}=5.54$ and $F_{eql}=4.41$.

- **Thin:** $V_f$ is **independent of $V_g$** and $\propto 1/\tau$. A larger $V_g$ raises the heat flux (W/m²) but shortens $L_g$, so the total heat (W) is unchanged.
- **Thick:** $V_f\propto V_g$, because the heated solid layer $L_{sy}\sim\sqrt{\alpha_s L_g/V_f}$ depends on the flow.
- Thermal prediction with $F_{adb}$ (inferred): 2.29, 1.14, 0.76 and 0.57 mm/s for 100, 200, 300 and 400 µm. BASS-II measured 1.8–2.1, 1.05–1.13, 0.58–0.80 and 0.46–0.47 mm/s (http://flame.sdsu.edu/bass.html).

### 2.3 Thin/thick criterion ([TM] eq. 2.10 and 2.14)
$$\tau<\tau_{cr}\sim\frac{\lambda_s}{\rho_g c_g V_g F}\quad(\text{thin})$$

- For downward spread in air ($V_{g,eff}=1.9$ cm/s buoyant) this gives **$2\tau_{transition}=5.19$ mm**.
- Since $\tau_{cr}\propto 1/V_g$, at 10 cm/s the transition falls at ~1 mm total thickness and at 3 cm/s at ~3.3 mm (inferred, linear scaling).
- Consequences for BASS-II:
  - The 100–400 µm B# films are thin, confirmed by $V_{f,max}\propto1/\tau$ ([TM §2.1.2]).
  - The 1–5 mm M# slabs at 3–20 cm/s are **intermediate or thick**: they depend on $V_g$ and thickness, and show appreciable regression and consumption.
  - For the P# rods, curvature matters in addition to thickness: $V_f$ increases as diameter decreases (Link 2018).

### 2.4 Radiative regime (μg, low $V_g$) and critical velocity
Leading-edge balance with surface radiative loss ([TM] eq. 2.1):
$$V_f\rho_sc_sL_{sy}W(T_v-T_\infty)\sim\lambda_g\frac{T_f-T_v}{L_{gy}}L_{gx}W-\varepsilon\sigma(T_v^4-T_\infty^4)L_{sx}W$$

Nondimensionalizing with $\eta_f=V_f/V_{f,th}$ and $\eta_g=V_g/V_{f,th}$ ([TM] eq. 2.3–2.5):
$$\eta_f\sim1-\frac{\Psi_0}{\eta_g}\;\Longleftrightarrow\;\boxed{V_{f,rad}\approx V_{f,th}\left(1-\frac{V_{g,cr}}{V_g}\right)},\qquad \boxed{V_{g,cr}\sim\frac{\varepsilon\sigma(T_v^4-T_\infty^4)}{\rho_g c_g(T_f-T_v)}}$$

- **$V_{g,cr}$ does not depend on thickness**, although $V_f$ does. This was confirmed experimentally: ~1 cm/s for 100–300 µm and ~1.5 cm/s for 400 µm at 21 %.
- $V_{g,cr}$ **increases as O2 decreases**:

  | O2 | Exp. | Computation | Theory |
  |---|---|---|---|
  | 21 % | 10 ± 5 mm/s | 15 mm/s | 7.5 mm/s |
  | 16 % | 30 ± 5 mm/s | 35 mm/s | 10 mm/s |

  At 16 %, 2.6 cm/s (100 µm) and ~4 cm/s (200 µm) were measured.
- Visual signature: the flame shrinks, **loses its orange (soot) and turns entirely blue**, the radiometer signal drops, and it extinguishes ~3 s after reaching $V_{g,cr}$. Sequence: t = 27 s at 3 cm/s → t = 30 s no flame ([TM §2.2.5]).

### 2.5 Kinetic regime (high $V_g$ or low O2): Damköhler and blowoff
$$Da=\frac{t_{g,res}}{t_{g,chem}},\qquad t_{g,res}\sim\frac{\alpha_g}{V_r^2}\ (V_r=V_g+V_f),\qquad t_{g,chem}\sim\frac{\rho Y_F}{\dot\omega_F},\quad \dot\omega\propto \rho^2 Y_FY_{O}\,e^{-E/RT_f}$$

- When $V_g\uparrow$ or $Y_{O_2}\downarrow$, Da decreases, $V_f/V_{f,th}=f(Da)$ decreases, and **blowoff** is reached.
- In BASS-II:
  - 100 µm at 21 % approaches blowoff above ~40 cm/s (NTRS 20160000593).
  - B15 and B8 (~20 %) did not blow off at 10 → 55 cm/s.
  - At ~16.4 % O2, B18 and B19 did blow off, at flows of ~30–50 cm/s according to the SDSU notes.
  - The computation at 16 % places the onset of the kinetic effect at $V_g>16$ cm/s.
- For rods and fabric, see Link 2018: $V_f$ **rises and then falls** with $V_g$. This is the competition between the thermal and kinetic regimes, peaking at ~1.7 cm/s for 0.64 cm rods at 17.5–18.2 % (Table S1). For opposed SIBAL the peak is at intermediate flow (BASS-I).

### 2.6 Summary of the opposed-flow map (U-shape)

| $V_g$ range | Regime | Behavior |
|---|---|---|
| $V_g<V_{g,cr}$ (~1 cm/s at 21 %) | Radiative extinction (quenching) | No spread |
| $V_{g,cr}<V_g\lesssim$ 3–5 cm/s | Radiative | $V_f$ increases with $V_g$ |
| ~3 to ~20–40 cm/s | Thermal | $V_f\approx$ constant (thin) or $\propto V_g$ (thick) |
| $V_g\gtrsim$ 20–40 cm/s (depending on O2) | Kinetic | $V_f$ decreases and blowoff follows |

As O2 decreases, the flammable window narrows on both sides.

---

## 3. Concurrent-flow: growth, limiting length and steady state
- **Transient:** after ignition, the flame length $L_f$ and the pyrolysis length grow. In μg, with low forced flow, the flame **reaches a limiting length** (Tseng & T'ien, J. Heat Transfer 132 (2010) 091201). Tip and base then advance at the same velocity: steady spread with constant $L_f$.
  - SIBAL 2.2 cm at 10 cm/s and 21 %: limiting length at ~19 s, steady for ~9 s, ~40 s in total.
  - At 5 cm/s: steady for ~21 s ([TM §7.1.4]).
  - BASS-I 1 cm at 10 cm/s: steady at ~10 s, $x_{tip}=1.71t+2.25$, $x_{base}=1.68t-13.81$, i.e. $L_f\approx16$ mm (NTRS 20130012832).
- **Scaling** (inferred, standard thin physics): $V_f\approx \dfrac{\dot q''_f\,L_h}{\rho_s c_s(2\tau)(T_v-T_\infty)}$, with heated zone $L_h\sim L_f$. Since $L_f$ grows with $U$, **$V_f$ grows almost linearly with $U$**. BASS-I SIBAL: $V_F\approx0.20U+0.56$ mm/s (2 cm) and $0.15U+0.07$ (1 cm), with U in cm/s.
- The sample is short (10 cm), so at high flow **steady state may not be reached** ([TM §7.1.2]).
- **Quenching at low U:** the flame shortens and narrows until it becomes circular, blue, and extinguishes. This occurs at 1–5 cm/s, and the lower the O2, the higher the quench U.
- **Rods with stagnation tip (O#):**
  - At low flow there is no spread along the rod but **tip regression (bulk burning)**: 0.0385 mm/s in the lowest-O2 test.
  - The stretch rate is $a=\tfrac32(U/r)(r/r_0)^{1/2}$.
  - Boundary $X_{O_2}=6e^{-0.5a}+0.0167a+13.4$ (%), minimum at ~13.5 % at $a\approx$ 8–12 s⁻¹.
  - Critical Damköhler (Olson & Ferkul 2017): $Da_{crit}=\dfrac{\beta\rho X_fX_{O_2}e^{-E/RT_{crit}}}{a}=1$, with E = 1.45×10⁵ J/mol.

---

## 4. Flame shape and color in μg: what the video shows
- **Without buoyancy** there is no rising plume. The flame is **thicker, wider and shorter**, with a larger standoff (pure diffusion plus forced flow). It appears **oval, hemispherical or circular** (Link 2018; [TM §6.1.4]).
- **Blue vs yellow/orange:** blue is chemiluminescence (CH*, C2*). Yellow/orange is **incandescent soot**.
  - At low $V_g$ or $U$, the residence time is long, radiative losses increase, $T_f$ drops, less soot forms, and the flame appears **blue**.
  - More flow or O2 makes it luminous and sooty, with a closed tip.
  - Opposed rods: blue, dim and open at the rear below ~2 cm/s; yellow with closed tip from ~2 cm/s ([TM §4.1.2]).
  - Films: sooty with a **blue leading edge** (B1).
- **Open tail:** at very low flow the flame tail opens and pyrolyzate escapes (high CO, $\phi_{global}\approx1.3$) ([TM §1.4]).
- **Pre-extinction:** for quenching, ~1.1 Hz oscillations appear (rods) and the ratio L/W → 0.5. For blowoff, a hole forms in the stagnation region (9–10 mm) that can re-close or end in total blowoff.
- **Solid-phase artifacts:**
  - Bubble layer visible in PMMA, thicker in thick samples.
  - Vapor jetting and sparklers from bursting bubbles.
  - Ejected droplets (candle F4).
  - Smoldering spots behind the base (SIBAL).
  - The igniter wire appears red in the first frames.

### 4.1 Mapping between video observables and physical quantities

| Observable (pixels) | Physical quantity | Notes |
|---|---|---|
| **Leading edge** (first pixel above threshold in the averaged profile, upstream side in opposed) | Flame front ≈ **pyrolysis front + standoff/preheat** | In opposed thin, $\dot x_{LE}=V_f$ at steady state. The slope is the same for the leading edge and for the intensity peak, within ±5 % ([TM §2.2.4]) |
| **Bright edge / intensity peak** | Most intense reaction zone or soot zone | Alternative estimator of $V_f$ |
| **Flame tip** (concurrent, downstream end) | Flame tip, advance of preheating | $L_f = x_{tip}-x_{base}$ |
| **Flame base** (concurrent) | ≈ fuel **burnout** front | Its velocity equals $V_f$ at steady state |
| **Black or charred line behind the flame** (top view) | **Burnout front** | In Fig. 2.7 of [TM] (B03): wire at x = 36 mm and burnout at x = 42 mm |
| **Surface–flame edge distance** | **Standoff** $s$ | Olson measures it to the outer edge of the cyan zone. $s\propto a^{1/3}$ |
| Flame area or integrated intensity | HRR proxy (relative) | Correlates with the radiometer: in rods, $L_f$ and the radiometer signal "track very closely" ([TM §6.1.4.2]) |
| Fraction of blue vs yellow pixels | Proxy for temperature and soot, proximity to extinction | Loss of yellow ⇒ approach to radiative extinction |
| Rod tip position | Regression $V_r$ | Scale 32.95–34 px/mm (Nikon) |
| Overlay text | $V_g$ (cm/s), fan V, N2, radiometer | The anemometer has **~1 min response** and ±0.5 cm/s. Use the fan V → velocity calibration. **There is a lag** between the flow change and the flame response |

---

## 5. Extinction
1. **Radiative or quenching** (low flow): the heat from the flame front no longer compensates the losses (dominant surface radiation and conduction into the solid).
   - Opposed thin: $V_{g,cr}$ from §2.4.
   - Concurrent SIBAL: 1–5 cm/s.
   - Rods: the flame shrinks to a blue hemisphere and oscillates before extinguishing. On the quenching branch, vaporization drops to ~20 % of the received heat and losses exceed 60 % ([TM §6.1.5.5]).
2. **Blowoff** (high flow or low O2): $Da<Da_{crit}$. The blowoff branch is linear in $(X_{O_2},a)$. In rods, downstream stabilization beyond δ ≈ 2 mm prevents the flame from spreading back upstream.
3. **Ignition vs extinction:** the sustained-ignition limit (~14.5 % O2, rods) is **higher** than the extinction limit (13.6 %), due to losses to a cold solid. The solid response time is $t_s=0.7r^2/\alpha_s$, with $\alpha_s=1.2\times10^{-3}$ cm²/s:

   | r (cm) | $t_s$ |
   |---|---|
   | 0.318 | ≈ 59 s |
   | 0.476 | ≈ 132 s (reported) |
   | 0.635 | ≈ 235 s |

   (inferred for 0.318 and 0.635)
4. **Observed extinction time scales:**
   - 100 µm film with flow cut off: <2 s.
   - Radiative ramp: ~3 s from 3 cm/s.
   - Rods: quench >100 s after the last step.
   - Thick slabs: self-extinction after ~10 min at fixed flow (M10 at 8 cm/s).

---

## 6. Physical priors for the forecasting model

### 6.1 Trend models by configuration

| Config. | Prior for front position $x(t)$ / $V_f(t)$ | Parameters and ranges |
|---|---|---|
| **Opposed thin PMMA (B#)** | After an ignition transient of ~a few s: $x(t)=x_0+V_ft$ with **constant $V_f$ per flow step**. On a $V_g$ change, near-immediate jump in $V_f$ (the flame responds in ~1 s; [TM] App. A: "flame response very rapid") | $V_f\approx V_{f,th}(1-V_{g,cr}/V_g)$, $V_{f,th}=2.34\times10^{-8}F/\tau$. At 21 %: **0.46–2.06 mm/s**; noise σ ≈ 5 % |
| **Opposed thick PMMA (M#)** | Piecewise linear with slow initial growth (stable size at ~3 min). $V_f$ increases with $V_g$ | **0.012–0.144 mm/s**. Burns of 8–31 min. Images every 1–8 s |
| **Opposed rods (P#)** | Linear per step, quasi-steady within ≥1 min. Non-monotonic $V_f(V_g)$ (peak at ~1.7 cm/s) | **~0.02–0.10 mm/s** |
| **Concurrent SIBAL (T#)** | **Growth → plateau → decay** in $L_f(t)$. Tip and base: $x_{tip}$ accelerates up to $V_f$. Suggested model (inferred): $L_f(t)=L_\infty(1-e^{-t/t_g})$ or logistic, with $t_g\sim$ 5–10 s, plus a decay phase when $x_{tip}\to$ end of sample | $V_f\approx0.20U+0.56$ mm/s (2 cm, 21 %). $L_\infty\approx16$ mm (1 cm, 10 cm/s), ~40 mm (Saffire at 20 cm/s) |
| **Concurrent/stagnation rods (O#)** | Tip regression $\approx$ constant. **$L_f$ responds to each flow step with first-order relaxation** (time constant ~ $t_s$ = 60–235 s) | $V_r$ ~0.04 mm/s. 1 cm sphere ~0.005 mm/s average |
| **Pre-extinction (all)** | Decay of size and intensity: exponential or logistic toward 0. Loss of yellow color. In rods, ~1.1 Hz oscillation with growing amplitude | Film: window of ~2–3 s. Rods: >100 s |

### 6.2 Recommended (exogenous) covariates
- $V_g$ (overlay OCR plus fan calibration), with a **lag** of a few seconds.
- O2 linearly interpolated between initial and final values (Miller's method).
- Thickness or diameter, width (1 vs 2 cm), one- or two-sided, opposed vs concurrent.
- Flow-change indicators (events): segment the series and fit one model per regime.

### 6.3 Physical constraints (hard and soft)
1. $x_{LE}(t)$ is **monotonic** in the spread direction ($V_f\ge0$). In opposed flow there are small recessions due to oscillations (P17: "leading edge receded slightly").
2. $x_{LE}\le$ sample length (~95 mm for films, 100 mm for SIBAL, 57.15 mm for rods). The flame extinguishes or wraps around when it reaches the end.
3. **Upper bounds** for μg and O2 ≤ 21–22 %:

   | Configuration | Upper bound |
   |---|---|
   | Opposed thin PMMA | ≲ 2.5 mm/s (100 µm) |
   | Opposed slabs | ≲ 0.2 mm/s |
   | Opposed rods | ≲ 0.15 mm/s |
   | Concurrent SIBAL | ≲ ~5 mm/s (up to 20–25 cm/s) |

   Saffire at 20 cm/s gave 1.8 mm/s, which is only a reference. Larger values are likely artifacts (reflections, the glowing wire, exposure changes).
4. **Extinction bounds:** if $V_g<V_{g,cr}$ (~1 cm/s at 21 %, ~2.6–4 cm/s at 16 %), extinction is expected. With O2 < ~14.5 % there is no rod ignition. At 14.1 % there was no film ignition (B14).
5. **Thickness scaling (thin):** $V_f\cdot\tau\approx$ const. The product $V_f\times$total thickness gives **≈0.18–0.24 mm²/s** for the films at ~20.6 % (inferred from SDSU values: B1 0.188, B5 0.225, B4 0.240, B12 0.182, B7 0.189; see table 2.1 of publications.md). It is a cross-check between tests.
6. Expected measurement noise: ±5 % (Flame Analyzer), flow resolution ±0.5 cm/s, and O2 resolution of 0.1 %.

### 6.4 Practical implications for the time series
- The native rate is **~1 Hz (Nikon)** or **30 Hz (video)**. It is advisable to **smooth and differentiate with a window**: SDSU uses a 5-point regression ≈ 5 s.
- Forecast **position** (integrated) and **velocity** (derivative) separately. Position is nearly linear and velocity nearly stepwise.
- For concurrent flow, a 2-state model (tip, base) with the constraint $L_f=x_{tip}-x_{base}\to L_\infty(U)$.
- To detect imminent extinction, useful early signals are decreasing flame area, increasing blue fraction, the onset of oscillations, and a falling radiometer signal (overlay).
