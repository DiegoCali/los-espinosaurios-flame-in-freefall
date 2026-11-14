# Auditoría final reservada — ACME PSI-10 / Tad-v1

Este documento describe **una única evaluación independiente** del modelo seleccionado después de los 12 intentos de AutoResearch de `pilot-01`. La salida predice `Tad` termodinámica calculada (K), **no** hollín, extinción, temperatura real ni estabilidad de la llama.

## Estado congelado

- Rama: `feature/psi-10-acme-autoresearch`.
- Commit del modelo seleccionado: `6d4dbe72c660dff475bfee09804ac275382300b6`.
- Modelo: `ridge_composition_quadratic_alpha_0_001`.
- Entrenamiento fijo: **134** filas de etileno; validación usada para elegir el modelo: **52** filas; evaluación final: **50** filas de **4 jornadas**.
- Evaluación de validación informada por Antigravity: RMSE cercano a **116.172 K** (confirmado en `runs/pilot-01/results.tsv` durante preflight).
- El `holdout` permanece intacto hasta invocar deliberadamente `--final`.

El evaluador final **no** altera `prepare.py`, `evaluate.py`, `train.py` ni las particiones. El candidato se reentrena sobre las **134 observaciones originales**, sin añadir las 52 de validación para evitar modificar la estrategia después de haber seleccionado el modelo.

## 1. Resguardar el historial local

Desde la raíz del repositorio:

```bash
mkdir -p ~/acme-psi10-backup
cp -a investigations/ACME/runs/pilot-01 ~/acme-psi10-backup/
git switch feature/psi-10-acme-autoresearch
git pull --ff-only origin feature/psi-10-acme-autoresearch
git status --short
```

No borres `runs/pilot-01`: Git lo ignora. Si tienes un `stash`, revísalo por separado antes de comenzar.

## 2. Añadir y revisar el nuevo código **sin ejecutar holdout**

Los archivos nuevos son `evaluate_holdout.py`, `tests/test_holdout_contract.py` y `HOLDOUT_FINAL.md`.

```bash
cd investigations/ACME
uv sync
uv run python -m unittest discover -s tests -v
cd ../..
git add investigations/ACME/evaluate_holdout.py investigations/ACME/tests/test_holdout_contract.py investigations/ACME/HOLDOUT_FINAL.md
git diff --cached --stat
git diff --cached --check
git commit -m "test(acme): add frozen one-time holdout audit"
git push origin feature/psi-10-acme-autoresearch
```

Este commit **debe** incluir únicamente los tres archivos nuevos. No modificar `train.py`, el protocolo ni el evaluador original. No abrir `data/processed/acme_tad_holdout.csv` durante esta preparación.

## 3. Verificación previa sin mirar holdout

Desde `investigations/ACME/`:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
uv run python evaluate_holdout.py --check
```

El chequeo verifica rama, estado limpio de Git, integridad del modelo frente al commit congelado, hashes de los CSV originales, contrato de entradas, grupos de entrenamiento y los doce registros del historial local. **No lee ni carga el conjunto holdout**.

Si `--check` falla, **NO** invoques `--final`. Corrige únicamente un problema de entorno o de archivos faltantes sin tocar el modelo, los datos ni el protocolo.

## 4. Evaluación única (solo después de aprobar `--check`)

```bash
uv run python evaluate_holdout.py --final
```

Esta instrucción consume la evaluación reservada. Antes de abrir `holdout`, crea `runs/holdout-final-v1/execution_receipt.json` mediante creación exclusiva. Una segunda ejecución será bloqueada, incluso si la primera falla, hasta que se investigue y documente la causa. **No borres manualmente el recibo para repetir la prueba**.

Genera `runs/holdout-final-v1/final_holdout_metrics.json`, con:

- RMSE, MAE y error absoluto máximo globales, en K.
- Las tres métricas por tipo de llama (`Normal`, `Inverse`).
- Las tres métricas por jornada experimental (`group_id`).
- Hash SHA-256 del modelo congelado, del historial, de los originales y del CSV holdout.
- Identificadores de modelo/commit, número de filas, versiones Python/NumPy, tiempo y limitaciones científicas.

Se comprueba que las 50 filas coinciden **exactamente** con una reconstrucción determinista desde los dos CSV originales NASA. Dicha lectura y comprobación se realiza únicamente durante el cierre final, después de crear el recibo.

## 5. Conservar y documentar resultados

```bash
cp -a runs/holdout-final-v1 ~/acme-psi10-backup/
cat runs/holdout-final-v1/final_holdout_metrics.json
```

No uses el resultado de holdout para elegir otro modelo, retocar `alpha` ni añadir nuevos experimentos. Si el RMSE es peor que en validación, debe reportarse sin cambios al modelo.

Este piloto solo evalúa la aproximación de **temperatura adiabática calculada** y no permite afirmar cumplimiento de los objetivos A/B/C (hollín, estructura, extinción) de la investigación NASA.
