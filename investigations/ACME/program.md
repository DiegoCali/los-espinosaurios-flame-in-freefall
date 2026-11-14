# AutoResearch: instrucciones del agente para NASA PSI-10 / ACME

## Misión y límites

Mejora la predicción de **temperatura adiabática calculada** `tad_calculated_k` en el piloto CPU de Flame Design, reduciendo `val_rmse_k` sin alterar el protocolo. **No afirmar que se predice hollín, extinción o estado estacionario:** estos son objetivos científicos futuros (A/B/C) que requieren etiquetas/series medidas.

Debes leer completamente, **antes de experimentar**, `README.md`, `protocol.md`, `knowledge/ACME_DATASET.md`, `prepare.py`, `evaluate.py`, `train.py` y los registros existentes de `runs/<RUN_ID>/results.tsv`. No reemplaces las hipótesis NASA por una métrica sin interpretación física.

## Archivo editable

**Solo** `investigations/ACME/train.py`. No modificar `prepare.py`, `evaluate.py`, `README.md`, `protocol.md`, `program.md`, CSV (originales o preparados), metadatos, dependencias, pruebas, `.gitignore`, `analysis` ni `knowledge`. `runs/` solo recibe archivos generados automáticamente por `evaluate.py`; no editar TSV manualmente.

No usar información de `data/processed/acme_tad_holdout.csv`. No leer/usar etiquetas de `validation` como entradas para ajuste, calibración o transformación. No usar `day`, IDs de ensayos, `zst_calculated`, presión final/media, condiciones finales ni ningún dato derivado de `Tad` como característica.

## Contrato de código

Mantener en `train.py`:

```python
MODEL_NAME: str
fit_predict(X_train, y_train, X_eval, seed) -> np.ndarray
```

- `X_train`: `134 × 7`; `y_train`: `134`, temperatura adiabática calculada (K).
- `X_eval`: `52 × 7`, sin etiquetas; devolver un arreglo de 52 predicciones finitas.
- Columnas por orden: indicador de llama inversa, fracción molar de reactivo del quemador, fracción inicial del reactivo ambiente, flujo del reactivo del quemador, flujo N2, flujo total y presión inicial.
- Solo NumPy y Python estándar en la versión inicial; **no instalar dependencias** durante el run.
- Cualquier transformación se ajusta **solo con train** y se aplica después a evaluación.

## Presupuesto

- Fijar `RUN_ID=pilot-01` y la semilla `20261113` para la primera ejecución.
- **Máximo 12 intentos incluyendo baseline.**
- **Máximo objetivo 120 s por candidato** en CPU. Medir tiempo y memoria.
- Métrica principal `val_rmse_k`; auxiliar `val_mae_k`. Menor es mejor.
- No cambiar la partición por jornada ni la métrica.

## Inicio (en una rama separada para experimentos, creada desde la rama feature principal)

```bash
# Desde la raíz del repositorio, solo si no existe la rama experimental:
git switch feature/psi-10-acme-autoresearch
git switch -c feature/psi-10-acme-tad-run01

source .venv/bin/activate
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s investigations/ACME/tests -v
python investigations/ACME/evaluate.py --baseline --run-id pilot-01
```

Si ya existe la rama o el `RUN_ID`, no reiniciarlos ni sobrescribir el registro. Elegir identificadores nuevos solo para una repetición independiente.

**El primer candidato** será el `train.py` inicial, Ridge alpha=10. Después de baseline:

```bash
python investigations/ACME/evaluate.py --candidate --run-id pilot-01 \
  --description "Ridge inicial alpha=10"
```

Antes de nuevos candidatos, registrar en un commit de la rama experimental la versión inicial de `train.py`. Si el primer candidato ya estaba incluido en el commit base, conservar ese SHA como referencia. No crear commits vacíos solo para aparentar un cambio.

## Ciclo de cada intento posterior

1. Leer el último `runs/pilot-01/results.tsv` y elegir una **hipótesis concreta** (ejemplo: reducir regularización, interacción entre configuración de llama y dilución, término cuadrático limitado).
2. Anotar el commit actual del mejor modelo y comprobar que solo cambiará `train.py`.
3. Cambiar exclusivamente `train.py`. Mantener su interfaz y un tiempo de cómputo pequeño.
4. Ejecutar las pruebas automatizadas. Si fallan, anotar el incidente como intento fallido antes de continuar; no modificar el evaluador.
5. Crear un commit específico que describa el cambio experimental.
6. Ejecutar el evaluador con una descripción nueva y consultar `val_rmse_k`, `status`, tiempo y memoria:

```bash
python investigations/ACME/evaluate.py --candidate --run-id pilot-01 \
  --description "HIPOTESIS_EXPERIMENTAL"
```

7. Conservar `train.py` si `status=keep` **y** la mejora es defendible frente a la complejidad añadida. En caso de `discard`, restaurar **solo** `train.py` desde el mejor commit, sin borrar el historial `runs/` ni tocar otros archivos. Si hubo `crash`, investigar el error y descontar el intento.
8. Parar tras el intento 12 o al agotar el presupuesto. No consultar `holdout` para decidir.

## Ideas científicas permitidas

- Ajustar L2/Ridge sin penalizar el intercepto.
- Probar un modelo afín por configuración de llama, con regularización.
- Interacciones físicamente interpretables entre composición de oxidante/combustible y tipo de llama.
- Escalado robusto calculado con entrenamiento, transformaciones suaves y límites numéricos.
- Terminos de segundo grado limitados, combinaciones lineales y reducción de características redundantes.

No construir un clasificador de hollín mediante un umbral arbitrario sobre `Tad` o `Zst`. No codificar predicciones por identificador de ensayo, día o caso de validación. No simular nuevos datos y presentarlos como mediciones de NASA.

## Registro y salida

`evaluate.py` escribirá `runs/<RUN_ID>/results.tsv` con número de intento, hash de `train.py`, commit, semilla, métricas, tiempo, memoria y `baseline` / `keep` / `discard` / `crash` (para excepciones capturadas). Los resultados son **de validación** y no constituyen evaluación final generalizable.

Al terminar, dejar un resumen con el mejor commit/hash, RMSE y MAE iniciales/finales, cambios aceptados, descartados, costo CPU y limitaciones. No anunciar validación independiente hasta que el usuario congele el modelo y se realice la única auditoría con `holdout` mediante un procedimiento separado.
