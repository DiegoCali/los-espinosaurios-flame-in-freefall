# Protocolo experimental — NASA PSI-10 / ACME, piloto Tad-v1

**Estado:** protocolo preliminar que debe congelarse mediante commit antes de la búsqueda automática. Cambiarlo durante una ejecución invalida la comparación con intentos anteriores. **No es el protocolo final del estudio de hollín.**

## 1. Preguntas y correspondencia con NASA

| Pregunta NASA | Hipótesis relacionada | ¿Se contrasta ahora? | Evidencia requerida después |
|---|---|---|---|
| A: límites de formación de hollín respecto a flujo, Zst, diluyente y presión | H1: C/O, T y strain críticos | No | Etiquetas y/o medidas de hollín, temperatura local y condiciones hidrodinámicas |
| B: estructura, temperatura, tamaño, color, fracción de hollín y estado estable | H3: existencia de llamas estacionarias | No | Series de tiempo de radio, temperatura y radiación de pruebas seleccionadas |
| C: extinción radiativa/cinética y límites | H2: extinción cerca de 1130 K | No | Temperatura máxima medida, tiempo y mecanismo de extinción; selección acorde a presión |
| **Piloto metodológico**: ¿puede AutoResearch reducir el error de predicción de `Tad` calculada? | Ninguna hipótesis de hollín/extinción | **Sí** | CSV de condiciones y `Tad`, disponibles |

Las metas A/B/C corresponden al proyecto NASA completo; no debe afirmarse que nuestro piloto las haya cumplido. El hallazgo de 1130 K corresponde a estudios de **llamas esféricas de etileno a aproximadamente 1 bar**, y se refiere a temperatura de extinción real, no `Tad` calculada.

## 2. Datos congelados

- Fuente: NASA PSI-10, DOI `10.60555/w4zy-bt45`.
- Dos archivos CSV originales en `data/raw/`. Sus hashes SHA-256 constan en `data/metadata/acme_inventory.json`.
- Normal: 207 filas; inversa: 120; total: 327.
- Condiciones no constantes: 69 marcadas `RAMP`/`RAMPED`; 2 `LOW O2`. Se conservan para auditoría, se excluyen del piloto.
- Se excluyen 20 filas de propano para mantener el piloto homogéneo en combustible etileno.
- **Unidad objetivo:** `tad_calculated_k` (kelvin), parámetro termodinámico calculado y no temperatura medida.
- **Conjunto piloto:** 236 filas de etileno con flujo constante y entradas completas.

`prepare.py`, sus transformaciones, los CSV originales, la lista de variables autorizadas y las asignaciones de grupo **no se modifican** durante un run.

## 3. Variables y riesgo de fuga

**Entradas permitidas en fase 1:** `flame_type`, `burner_reactant_mole_fraction`, `ambient_reactant_fraction_initial`, `burner_reactant_flow_mg_s`, `nitrogen_flow_mg_s`, `total_flow_mg_s`, `pressure_initial_atm`.

En el evaluador, `flame_type` se codifica como `flame_type_inverse` (0 normal, 1 inversa), seguido por las seis variables numéricas en el orden indicado por `evaluate.FEATURE_ORDER`.

**Prohibidos como características:** `tad_calculated_k`, `zst_calculated`, `day`, `test_id`, `group_id`, `source_file`, `split`, `flow_status`, `ambient_reactant_fraction_final`, `pressure_final_atm` y `pressure_mean_atm`. `total_flow` es potencialmente redundante con sus componentes; se permite solo como condición inicial y puede descartarse del modelo si mejora la generalización.

Las columnas genéricas de flujo se interpretan por su **papel físico**, no como la misma especie química en normal e inversa: el gas inyectado es combustible en la configuración normal y oxígeno en la inversa.

## 4. Particiones invariables por jornada

La unidad de separación es `flame_type + Day`; nunca se separan filas de la misma jornada entre train, validation y holdout.

| Partición | Filas | Uso |
|---|---:|---|
| Entrenamiento (`train`) | 134 | Ajustar transformaciones, parámetros y modelo |
| Validación (`validation`) | 52 | Medir el resultado de cada intento y elegir entre candidatos |
| Prueba final (`holdout`) | 50 | Reservada para una **única** auditoría después de congelar el mejor modelo |

Semilla de partición y modelo: `20261113`. Grupos concretos en `data/metadata/acme_inventory.json`.

Las cuatro jornadas de validación y las cuatro de holdout pueden representar condiciones diferentes; no se afirma independencia perfecta ni capacidad generalizada a otras campañas. Seleccionar doce veces con la misma validación genera sesgo de selección. Los resultados se reportarán como piloto.

## 5. Métricas

El evaluador `evaluate.py` calcula, usando exclusivamente etiquetas reales de validación:

- **Principal:** RMSE en kelvin (`val_rmse_k`); menor es mejor.
- **Secundarias:** MAE (`val_mae_k`) y máximo error absoluto, también en kelvin.
- **Operativas:** tiempo transcurrido y máximo de memoria del proceso en MB.

`train.py` recibe `X_train`, `y_train` y `X_validation`, pero **no recibe `y_validation` ni datos holdout**. Cualquier normalizador, selección de variables, ajuste de hiperparámetros o entrenamiento debe usar únicamente los 134 datos de entrenamiento. No codificar valores particulares de los CSV.

## 6. Línea base y modelos

- Intento 1: media de `Tad` de entrenamiento, utilizada para todas las predicciones de validación.
- Primer candidato: Ridge con regularización L2 y escalado definido en `train.py`, ajustado solo con datos train.
- Exploración futura: combinaciones polinómicas limitadas, regresión robusta, modelos no lineales pequeños y relaciones físicas comprobables. No usar arquitecturas profundas ni CFD para este piloto.

Un modelo no es "mejor" si supera la validación utilizando la variable calculada `Zst` como entrada, identificadores, información futura, etiquetas ocultas o manipulaciones de la métrica.

## 7. Presupuesto y decisión

- **12 intentos máximos por `run-id`**, línea base incluida (máximo 11 candidatos).
- **Tiempo objetivo máximo por candidato:** 120 s en CPU; un experimento que lo exceda es un intento fallido, documentado. No usar GPU.
- Cada intento registra código/commit, hash SHA-256 de `train.py`, hipótesis, seed, RMSE, MAE, error máximo, tiempo, memoria y `status`.
- `keep` automático: el RMSE baja al menos 0.001 K respecto del mejor aceptado. Se exige además revisión humana de complejidad, integridad de los archivos protegidos y ausencia de fuga.
- `discard`: métrica válida sin mejora suficiente, o complejidad injustificada.
- `crash`: excepción de ejecución, salida inválida o incumplimiento de presupuesto.
- La comparación entre condiciones manual y AutoResearch, si se realiza, debe partir de la **misma línea base**, con el mismo número de intentos y métricas. No afirmar superioridad general a partir de una sola ejecución.

## 8. Archivos protegidos

Durante la búsqueda el agente **solo puede editar `train.py`**. Protegidos: `README.md`, `protocol.md`, `program.md`, `prepare.py`, `evaluate.py`, `tests/`, `requirements.txt`, `knowledge/`, `data/`, `analysis/` y `.gitignore`.

`evaluate.py` genera `runs/<run-id>/results.tsv` y `latest_validation.json` automáticamente. Estos resultados de búsqueda se preservan fuera del seguimiento de Git para evitar que restablecer código los borre. El registro `crash` se genera para errores de modelo; un corte del proceso por el sistema operativo puede requerir documentación manual aparte.

**Alcance del control:** la separación es un contrato de software y de procedimiento, no un sandbox de seguridad que impida toda lectura al código con acceso total al disco. Se deben inspeccionar los diffs y no dar al agente permisos innecesarios.

## 9. Cierre científico de la fase 1

Solo después de completar y congelar la búsqueda:

1. Elegir el mejor modelo exclusivamente por validación.
2. Congelar su código y sus dependencias.
3. Definir un **evaluador final separado** para la única prueba holdout, documentando su uso. No agregar `holdout` a `evaluate.py`.
4. Reportar incertidumbre, diferencias por tipo de llama y jornadas, y posible sesgo de selección.
5. Publicar conclusiones limitadas a la aproximación de una temperatura **calculada**.

Para las hipótesis NASA, abrir un nuevo protocolo A/B/C tras conseguir observaciones etiquetadas: no deducir hollín desde umbrales arbitrarios de `Tad`, ni declarar extinción por comparar `Tad` con 1130 K, ni estacionariedad sin series temporales.

## 10. Referencias

- NASA, *ACME / Flame Design Final Report* (2023), pp. 3–8, 24–27 y 93.
- NASA, *Science Requirements Document for Flame Design* (2010), hipótesis sobre `Zst`, C/O, temperatura y límites.
- NASA PSI-10, DOI 10.60555/w4zy-bt45.
- A. Karpathy, `autoresearch`; `autoresearch-pendulum-study`, adaptación de bajo cómputo.
