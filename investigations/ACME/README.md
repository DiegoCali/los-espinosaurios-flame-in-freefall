# NASA PSI-10 — ACME / Flame Design

**Proyecto NASA:** *Flame Design: A Novel Approach to Clean Efficient Diffusion Flames*  
**Tipo:** Microgravity Investigation · **Plataforma:** International Space Station (ISS)  
**Patrocinador:** NASA · **Centro:** Glenn Research Center (GRC)  
**Identificador de investigación:** PSI-10 · **DOI del conjunto:** [10.60555/w4zy-bt45](https://doi.org/10.60555/w4zy-bt45)  
**Fechas del catálogo de la investigación:** 1999-01-14 a 2025-04-30. **Operaciones de vuelo:** abril–julio de 2019 y octubre de 2021–febrero de 2022 (no confundir ambos períodos).

## 1. Propósito científico

El programa Flame Design estudia llamas esféricas de difusión en microgravedad, en configuraciones **normales** (combustible hacia oxidante) e **inversas** (oxidante hacia combustible). Sus objetivos científicos originales son:

- **A. Formación inicial de hollín:** determinar límites de aparición de hollín (*soot inception*) con variaciones en flujo, fracción estequiométrica de mezcla `Zst`, dilución con gases inertes y presión; estudiar temperaturas pertinentes.
- **B. Estructura y evolución de la llama:** estudiar temperatura, dimensiones, color, fracción volumétrica de hollín y posibilidad de regímenes cuasiestacionarios.
- **C. Extinción:** determinar límites de extinción, identificar mecanismos radiativos o cinéticos y evaluar los denominados límites de pseudoinflamabilidad.

**Hipótesis científicas que motivan el proyecto:**

1. La formación inicial de hollín requiere una región con relación atómica local C/O y temperatura suficientemente altas, y una tasa de deformación (*strain rate*) suficientemente baja.
2. En las condiciones estudiadas de llamas esféricas de etileno a **1 bar**, la extinción radiativa ocurre cerca de **1130 K de temperatura máxima real**, no de temperatura adiabática calculada.
3. Es posible obtener llamas esféricas de difusión con comportamiento estacionario pese a pérdidas radiativas, dentro de determinadas condiciones.

Esas hipótesis son **preguntas de investigación**, no etiquetas disponibles en nuestros dos CSV. En particular, la investigación NASA contemplaba CH4 y CO2, pero el informe de vuelo aclara que no se realizaron ensayos ISS con metano como combustible, CO2 como diluyente ni configuración coflow en Flame Design. Los CSV disponibles incluyen etileno y un conjunto pequeño de pruebas con propano.

## 2. Alcance real de la versión actual

**Fase 1: piloto computacional con datos tabulares.** Se construye un *modelo sustituto* (surrogate) para predecir `Tad (K)`, una **temperatura adiabática calculada**, a partir de condiciones iniciales de ensayos de etileno de flujo constante. Sirve para comprobar la metodología AutoResearch en CPU, sin usar imágenes masivas ni un solucionador CFD.

**La fase 1 no predice ni confirma hollín, temperatura máxima medida, tiempo de extinción, tipo de extinción, diámetro de llama ni estado estacionario.** Para evaluar A/B/C y las hipótesis de forma directa necesitaremos etiquetas y/o series temporales medidas, asociadas al identificador `Test`, mediante adquisición selectiva y documentación de incertidumbre.

| Alcance | Datos disponibles | Estado |
|---|---|---|
| Condiciones iniciales y `Tad` calculada | 327 filas originales, 256 con `Tad` numérica | Disponible |
| Piloto etileno, caudales constantes | 236 filas | Disponible |
| Hollín sí/no por prueba | No existe columna en CSV | Pendiente |
| Temperatura máxima real (TFP/termopar) y extinción | No está en tablas resumidas | Pendiente |
| Estabilidad/estado cuasiestacionario | Requiere series de tiempo | Pendiente |

## 3. Estructura

```text
investigations/ACME/
├── README.md                   # contexto, instalación y reproducibilidad
├── protocol.md                 # protocolo congelable y alcance físico
├── program.md                  # instrucciones del agente AutoResearch
├── prepare.py                  # normalización y particiones FIJAS
├── evaluate.py                 # evaluación FIJA: train y validation solamente
├── train.py                    # ÚNICO archivo editable en AutoResearch
├── requirements.txt            # NumPy para el piloto
├── data/
│   ├── raw/                    # NASA original (ignorado en Git)
│   ├── processed/              # CSV regenerables (ignorados en Git)
│   └── metadata/acme_inventory.json
├── knowledge/ACME_DATASET.md   # auditoría y procedencia de datos
├── runs/                       # TSV/JSON de intentos (no versionar en la búsqueda)
├── tests/
│   ├── test_prepare.py
│   └── test_evaluate.py
└── analysis/                   # informes futuros
```

## 4. Preparación en Linux

Desde la raíz del repositorio:

```bash
cd investigations/ACME

uv sync
uv run python prepare.py --check
uv run python -m unittest discover -s tests -v
```

Con los dos CSV originales descargados de NASA en `data/raw/`, la preparación debe indicar: **327** filas, **236** filas para el piloto, con **134 train**, **52 validation** y **50 holdout**. `holdout` permanece sin consultar durante la búsqueda.

Para disminuir variaciones de rendimiento en CPU:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

## 5. Primera medición y primer candidato

```bash
uv run python evaluate.py --baseline --run-id pilot-01

uv run python evaluate.py --candidate \
  --run-id pilot-01 \
  --description "Ridge alpha=10"
```

- Primer comando: predicción constante con la media de `Tad` de **entrenamiento**.
- Segundo comando: regresión Ridge, cuyas medias y escalas se calculan **solo con entrenamiento**.
- Salida: `investigations/ACME/runs/pilot-01/results.tsv` y `latest_validation.json`.
- Métrica principal: `val_rmse_k`, menor es mejor. Complementarias: `val_mae_k`, error máximo absoluto, tiempo y memoria.
- Cada ejecución (`run-id`) acepta hasta **12 intentos incluyendo la línea base**. Use un `run-id` nuevo para una repetición independiente; no reinicie borrando los resultados previos.

Los valores de RMSE corresponden a predicción de cálculos tabulados de `Tad`; **no son errores frente a termometría experimental ni mediciones de hollín**.

## 6. Uso con AutoResearch

1. Lea `knowledge/ACME_DATASET.md`, `protocol.md`, `program.md`, `prepare.py`, `evaluate.py` y `train.py`.
2. Ejecute y registre la línea base en una rama de experimentación que provenga de `feature/psi-10-acme-autoresearch`.
3. Entregue `program.md` al agente con acceso al código local. Durante la búsqueda solo puede modificar `train.py`.
4. Cada intento debe quedar asociado a un hash SHA-256 de `train.py`, commit, métrica y decisión (`keep`, `discard`, `crash`).
5. Las **50 filas holdout** son un conjunto independiente de auditoría final; `evaluate.py` ni siquiera ofrece una opción para abrirlas.

**Advertencia de integridad:** las reglas de `program.md` son restricciones metodológicas, no un entorno de ejecución aislado. Revise el diff de `train.py` antes de aceptar resultados del agente.

## 7. Evolución hacia las hipótesis NASA

- **A / H1 — hollín:** conseguir resultados por ensayo de hollín/color/soot volume fraction, con procedencia verificable. Etiquetas no deben inferirse de `Zst` o `Tad` mediante umbrales arbitrarios.
- **B / H3 — estado estacionario:** conseguir series de radio, temperatura y radiación con marca temporal; definir estadísticamente un tramo cuasiestacionario.
- **C / H2 — extinción:** conseguir temperatura **medida** y evento de extinción para ensayos de etileno, identificando el tipo de extinción. La referencia de 1130 K se limita a las condiciones y métodos de los estudios citados, no a todos los combustibles y presiones.

Para avanzar no hace falta descargar los 1.81 TB; seleccionar pruebas puntuales con metadatos y telemetría alineados por `Test` es una opción inicial más rigurosa.

## 8. Fuentes

- NASA Physical Sciences Informatics, [PSI-10 / Flame Design](https://psi.nasa.gov/physci/repo/data/investigations/PSI-10), DOI: 10.60555/w4zy-bt45.
- NASA, *ACME / Flame Design Final Report* (6 abril 2023), especialmente pp. 3–8, 24–27 y 93.
- NASA, *Science Requirements Document for Flame Design*, versión 1.3 (1 abril 2010).
- A. Karpathy, [autoresearch](https://github.com/karpathy/autoresearch).
- [autoresearch-pendulum-study](https://github.com/PoncheDeFrutas/autoresearch-pendulum-study), referencia de protocolo ligero y registro reproducible.
