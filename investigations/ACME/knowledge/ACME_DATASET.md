# NASA PSI-10 — ACME / Flame Design: auditoría inicial del conjunto de datos

## 1. Investigación y alcance

- **Investigación:** Advanced Combustion via Microgravity Experiments (ACME), Flame Design.
- **Identificador NASA PSI:** PSI-10.
- **DOI:** [10.60555/w4zy-bt45](https://doi.org/10.60555/w4zy-bt45), presente en el archivo de metadatos de NASA `PSI-10_metadata_PSI-10-ISA.zip`.
- **Origen:** [NASA Physical Sciences Informatics](https://psi.nasa.gov/physci/repo/data/investigations/PSI-10).
- **Objetivo científico NASA:** estudiar formación de hollín, estructura y extinción de llamas esféricas de difusión en microgravedad; comparar configuraciones de llama normal e inversa.
- **Alcance actual de nuestro software:** preparar las tablas de condiciones experimentales y verificar un piloto de regresión para la **temperatura adiabática calculada**, *no* para hollín.

## 2. Archivos originales usados

| Archivo | Tipo | Uso |
|---|---|---|
| `PSI-10_Experimental table_Flame Design_Normal Flame.csv` | NASA CSV | 207 filas, llama normal |
| `PSI-10_Experimental table_Flame Design_Inverse Flame.csv` | NASA CSV | 120 filas, llama inversa |
| `PSI-10_Reports_FinalRpt_ACMEFlameDesign.pdf` | NASA, informe final 2023 | Contexto físico, restricciones y limitaciones |
| `PSI-10_Science Documents_SRD_ACMEFlameDesign.pdf` | NASA, requisitos científicos | Objetivos y terminología física |
| `PSI-10_Science Documents_ACME_SORD.pdf` | NASA, requisitos operacionales | Definición y control de operaciones |
| `PSI-10_metadata_PSI-10-ISA.zip` | NASA ISA metadata | Identificador, DOI y procedencia |

Los originales se guardan sin modificar en `data/raw/`, excluido del control de versiones. `data/metadata/acme_inventory.json` registra los SHA-256 de los dos CSV utilizados.

## 3. Inventario verificado de los CSV

| Indicador | Llama normal | Llama inversa | Total |
|---|---:|---:|---:|
| Filas | 207 | 120 | 327 |
| `Tad (K)` y `mean Zst` numéricos | 147 | 109 | 256 |
| Condiciones de flujo `RAMP`/`RAMPED` | 60 | 9 | 69 |
| Condiciones marcadas `LOW O2` | 0 | 2 | 2 |
| Registros de propano (`C3H8`) | 20 | 0 | 20 |
| Filas disponibles para el piloto inicial de etileno (`C2H4`) | 127 | 109 | **236** |

- `Test` es único en cada fila y no se repite entre ambas tablas.
- **No equivalen a 327 observaciones independientes desde el punto de vista estadístico:** los ensayos del mismo día comparten condiciones ambientales y equipamiento.
- Las 20 pruebas de propano proceden de la configuración de llama normal de la segunda ronda (2021). Se conservan para auditoría, pero se excluyen del primer piloto para evitar mezclar combustibles con poca representación.
- Las filas `RAMP`/`RAMPED` documentan operaciones de flujo variable: **no son valores faltantes numéricos comunes ni equivalen a flujo cero**.
- Los dos valores `LOW O2` se mantienen como marca operativa. No se inventan fracciones de oxígeno.
- Un registro (`22042M1`) tiene un prefijo distinto de otros registros del día inverso 6 y se conserva tal cual. La agrupación por `Flame Type` + `Day` no asume que el prefijo del ID siempre indica la jornada.

## 4. Semántica física y columnas normalizadas

En una **llama normal**, el combustible sale del quemador hacia una atmósfera oxidante. En una **llama inversa**, el oxígeno sale del quemador hacia una atmósfera que contiene combustible. No deben fusionarse directamente `Xfuel` (normal) y `XO2` (inversa) bajo un nombre que suponga la misma especie química.

El script `prepare.py` crea columnas comunes que preservan el papel físico de cada variable:

| Columna procesada | Llama normal | Llama inversa |
|---|---|---|
| `burner_reactant` | `fuel` | `oxygen` |
| `ambient_reactant` | `oxygen` | `fuel` |
| `burner_reactant_mole_fraction` | `Xfuel` | `XO2` |
| `ambient_reactant_fraction_initial` | `XO2 (init)` | `XC2H4 initial` |
| `burner_reactant_flow_mg_s` | `mfuel (mg/s)` | `mO2 (mg/s)` |
| `nitrogen_flow_mg_s` | `mN2 (mg/s)` | `mN2 (mg/s)` |
| `total_flow_mg_s` | `mtot (mg/s)` | `mtot (mg/s)` |
| `pressure_initial_atm` | `pinit (atm)` | `pinit (atm)` |
| `tad_calculated_k` | `Tad (K)` | `Tad (K)` |
| `zst_calculated` | `mean Zst` | `mean Zst` |

Las columnas `ambient_reactant_fraction_final`, `pressure_final_atm` y `pressure_mean_atm` se conservan **solo para auditoría**. No se autorizan como entradas del piloto predictivo porque reflejan información posterior al inicio del ensayo o agregaciones de todo el ensayo.

### Diferencia crucial: temperatura adiabática y extinción

`Tad (K)` en los CSV representa **temperatura adiabática calculada**, no la temperatura real medida por pirómetro o termopar. En su informe final, NASA describe una temperatura crítica de **1130 K** asociada a la extinción radiativa en condiciones estudiadas de etileno a 1 bar. Estos son conceptos distintos; el piloto jamás debe presentar un error pequeño de `Tad` como confirmación de la temperatura crítica de extinción.

### Hallazgo sobre el hollín

Los dos CSV **no contienen etiquetas por prueba de “hollín sí/no”, concentración de hollín, tiempo de extinción ni diámetro de llama medido**. Esos resultados científicos requieren obtener mediciones o etiquetas verificadas a partir de archivos adicionales, publicaciones o imágenes seleccionadas. `prepare.py` no produce etiquetas de hollín artificiales.

## 5. Salidas de la preparación

Al ejecutar `python3 prepare.py` se generan:

- `data/processed/acme_all.csv`: 327 filas normalizadas, con operaciones especiales preservadas como estado y valores numéricos no disponibles en blanco.
- `data/processed/acme_tad_pilot.csv`: 236 filas elegibles de etileno; incluye la partición asignada.
- `data/processed/acme_tad_train.csv`: filas de entrenamiento.
- `data/processed/acme_tad_validation.csv`: filas para experimentación y selección de modelo.
- `data/processed/acme_tad_holdout.csv`: filas reservadas para evaluación final. **No usar en `train.py` ni en las pruebas repetidas de AutoResearch.**
- `data/metadata/acme_inventory.json`: conteos, hashes, grupos asignados, variables permitidas y restricciones.

## 6. Validación preliminar de bajo cómputo

- **Problema piloto:** regresión de `tad_calculated_k` en ensayos de etileno con condiciones de flujo constantes.
- **Características autorizadas:** `flame_type`, `burner_reactant_mole_fraction`, `ambient_reactant_fraction_initial`, `burner_reactant_flow_mg_s`, `nitrogen_flow_mg_s`, `total_flow_mg_s`, `pressure_initial_atm`.
- **No utilizar como características:** `zst_calculated`, `tad_calculated_k`, mediciones finales, `day`, `test_id`, `group_id`, `source_file`, ni `split`.
- **Unidad de partición:** grupo compuesto por configuración de llama (`Normal`/`Inverse`) y `Day` original. Todos los ensayos de un mismo grupo quedan en la misma partición.
- **Método:** asignación determinista por semilla fija y por configuración, aproximadamente 60 % de grupos para entrenamiento, 20 % validación y 20 % evaluación final. Las proporciones de filas pueden diferir.
- **Métricas previstas:** RMSE y MAE expresadas en kelvin; aún no se ha entrenado ni validado ningún modelo.
- **Restricción:** la métrica de validación sirve para seleccionar experimentos; las filas `holdout` solo deben evaluarse una vez después de seleccionar y congelar el mejor modelo.

### Límites de interpretación

Las tablas contienen **valores termodinámicos calculados a partir de condiciones experimentales**, por lo que el piloto evalúa una aproximación computacional a cálculos existentes, no una medición física independiente. Los valores originales del experimento incluyen incertidumbres y concentraciones que pueden haber sido estimadas. La validación entre jornadas reduce, pero no elimina, el riesgo de fuga o extrapolación deficiente.

## 7. Referencias NASA

1. NASA, *ACME/Flame Design Final Report (2023)*, en especial pp. 3–8 (objetivos), 24 (cronología), 25–27 (resultados físicos) y 93 (tipos de archivos archivados).
2. NASA, *Science Requirements Document for Flame Design*, Version 1.3, 1 April 2010, pp. 2–3, 8–15 (hollín, extinción, `Zst`, `Tad`).
3. NASA, *ACME Science Operations Requirements*, Revision A, 18 October 2011, pp. 4–6 y 13–16 (operación y controles de flujo).
4. NASA PSI, Study PSI-10, [catálogo y procedencia](https://psi.nasa.gov/physci/repo/data/investigations/PSI-10), DOI: 10.60555/w4zy-bt45.
