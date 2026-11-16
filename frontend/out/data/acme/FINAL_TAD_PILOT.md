# Informe final — Piloto AutoResearch NASA PSI-10 / ACME Flame Design

**Estado:** ejecución AutoResearch terminada y auditoría holdout realizada una sola vez.  
**Rama de trabajo:** `feature/psi-10-acme-autoresearch`.  
**Modelo seleccionado:** `ridge_composition_quadratic_alpha_0_001`.  
**Commit del modelo:** `6d4dbe72c660dff475bfee09804ac275382300b6`.  
**Momento de la auditoría final (UTC):** 2026-11-14T04:26:26.638564+00:00.  
**Variable predicha:** temperatura adiabática **calculada**, `tad_calculated_k`, en kelvin.

## Resumen

Se utilizó el esquema AutoResearch para desarrollar un modelo sustituto de temperatura adiabática calculada a partir de las tablas de condiciones experimentales de NASA PSI-10 / Flame Design [1]. Se realizaron **12 intentos** de búsqueda sobre un conjunto fijo, seleccionando candidatos mediante RMSE de validación. El RMSE descendió de **286.978761 K** para la referencia constante a **116.171636 K** para el modelo seleccionado, una disminución del **59.5 %** en esa partición. Tras congelar el modelo, la auditoría independiente de una sola ejecución sobre **50** registros reservados obtuvo **RMSE de 62.170083 K**, **MAE de 55.232577 K** y **error absoluto máximo de 131.338958 K**.

**Delimitación científica:** el piloto aprende a aproximar una cantidad termodinámica tabulada; no predice directamente hollín, extinción, temperatura medida ni estado estacionario. El resultado reservado no se utilizó para seleccionar modelos ni ajustar hiperparámetros.

## 1. Fuente de datos y objetivos NASA

El experimento NASA ACME/Flame Design estudia las llamas esféricas de difusión en microgravedad, incluidas configuraciones **normal** e **inversa**. Sus objetivos científicos comprenden: **A**, identificar límites de aparición de hollín; **B**, caracterizar estructura, temperatura, evolución y estabilidad de la llama; y **C**, estudiar los límites y mecanismos de extinción. Las dos tablas de la fase piloto no contienen etiquetas directas para resolver estos objetivos; el modelo abordó únicamente la predicción de `Tad` calculada [1–2].

Los datos utilizados proceden de las tablas CSV originales de la versión 1 de NASA PSI-10. No se modificaron los originales:

| Archivo | Filas | SHA-256 |
| --- | ---: | --- |
| `PSI-10_Experimental table_Flame Design_Normal Flame.csv` | 207 | `4a663292bd3f65201943cc71bd661a70383639276a9176f64105b285bf0b6deb` |
| `PSI-10_Experimental table_Flame Design_Inverse Flame.csv` | 120 | `97933ee9ae0b9ebc6b948a67485a0fe2f8218f753253a4f2be93c40d374c44e4` |

Los archivos se encuentran en `data/raw/`; `data/metadata/acme_inventory.json` documenta hashes, exclusiones y particiones. Las directrices de atribución y el procedimiento de verificación están en `data/README.md`.

## 2. Preparación y separación de observaciones

El inventario contiene **327 registros**. **256** presentan valores numéricos de `Tad`; el subconjunto inicial homogéneo utiliza **236 ensayos de etileno (C2H4)** de flujo constante con entradas completas. Se dejaron fuera de este piloto los ensayos de propano (20), los eventos RAMP/RAMPED (69) y LOW O2 (2), sin borrar dichas filas de la tabla normalizada de auditoría. Estas categorías son descripciones del inventario y no deben sumarse como conjuntos necesariamente disjuntos.

La separación fue determinista, por grupo `flame_type + Day`, con semilla `20261113`:

| Conjunto | Registros | Función |
| --- | ---: | --- |
| Entrenamiento | 134 | Estimación de normalización y coeficientes |
| Validación | 52 | Comparación y elección entre intentos AutoResearch |
| Holdout | 50 | Única evaluación final, después de congelar el modelo |

No se mezclaron observaciones de una misma jornada y configuración entre las particiones. El conjunto holdout abarca cuatro grupos; su tamaño limitado restringe las conclusiones sobre generalización a otras campañas.

## 3. Variables y modelo

Las siete entradas preensayo permitidas son el indicador de llama inversa, fracción molar de reactivo del quemador, fracción inicial de reactivo ambiental, flujo de reactivo del quemador, flujo de nitrógeno, flujo total y presión inicial. No se utilizan como entradas la variable objetivo, `Zst` calculada, identificadores, jornadas, fracciones finales ni presiones finales o medias. En una llama normal el reactivo del quemador es combustible; en una llama inversa, oxígeno, por lo que la misma columna genérica representa **el papel del reactivo**, no necesariamente la misma especie.

El modelo elegido es una regresión **Ridge** con `alpha=0.001`, las seis entradas numéricas lineales, un indicador binario para la configuración y tres términos de segundo grado de composición: fracción del quemador al cuadrado, producto de las fracciones de quemador y ambiente, y fracción ambiental al cuadrado. Incluido el intercepto, se ajustan **11 parámetros**. Las medias y desviaciones se calculan únicamente sobre los 134 ejemplos de entrenamiento; la función de predicción no recibe las etiquetas de validación ni de holdout.

Identificadores congelados:

- Modelo: `ridge_composition_quadratic_alpha_0_001`.
- Commit del modelo: `6d4dbe72c660dff475bfee09804ac275382300b6`.
- SHA-256 de `train.py`: `ab3c90ca73338ef954119343ae0a6f310b50352a39ad668b91729dce77929eb5`.
- Python: `3.13.17`; NumPy: `2.5.4`; ejecutado en CPU.

## 4. Búsqueda experimental AutoResearch

Se fijó un presupuesto de **12 intentos**, incluida la línea base, y la evaluación de cada propuesta se mantuvo bajo `evaluate.py`, sin cambiar el contrato de datos. La función principal de selección fue RMSE de validación; también se conservaron MAE, máximo error absoluto, tiempo, memoria, hash del código y decisiones `keep`/`discard`. Se probaron alternativas de regularización, interacciones, términos cuadráticos y cúbicos, selección de variables y Ridge con kernel gaussiano. Se rechazaron propuestas que no superaron el mejor valor de validación.

| Hito | Modelo | RMSE validación (K) | Estado |
| --- | --- | ---: | --- |
| Intento 1 | Predicción de la media de entrenamiento | 286.978761 | `baseline` |
| Intento 2 | Ridge, `alpha=10` | 178.891824 | `keep` |
| Intentos 3–11 | Variaciones documentadas en el historial original | Consultar TSV | `keep` o `discard` |
| Intento 12 | Ridge cuadrático de composición, `alpha=0.001` | **116.171636** | **`keep`** |

La mejora de validación frente a la línea base fue de **170.807125 K**, aproximadamente **59.5 %**. El listado íntegro de las doce variantes, sus métricas y sus hashes reside en `runs/pilot-01/results.tsv`; **no debe reconstruirse ni editarse manualmente**. El uso iterativo de la misma validación puede inducir sesgo de selección, incluso aunque el ajuste estadístico use solo entrenamiento.

## 5. Auditoría final independiente

Tras seleccionar y congelar el modelo, `evaluate_holdout.py` ejecutó una validación de integridad previa sin abrir holdout, verificando rama, archivos protegidos, hashes NASA, historial y modelo seleccionado. En el entorno de ejecución se aprobaron **15 pruebas automatizadas**. Después, una única ejecución `--final` reservó un recibo antes de acceder a los 50 registros reservados, reconstruyó su partición desde los CSV NASA y calculó métricas agregadas. El ajuste del modelo continuó utilizando solo el entrenamiento original de 134 observaciones.

### 5.1 Resultado global

| Métrica | Resultado holdout |
| --- | ---: |
| RMSE | **62.170083 K** |
| MAE | **55.232577 K** |
| Máximo error absoluto | **131.338958 K** |

### 5.2 Por tipo de llama

| Tipo | n | RMSE (K) | MAE (K) | Error máximo absoluto (K) |
| --- | ---: | ---: | ---: | ---: |
| Inverse | 25 | 72.616640 | 65.182068 | 131.338958 |
| Normal | 25 | 49.568762 | 45.283085 | 99.048352 |
| **Global** | **50** | **62.170083** | **55.232577** | **131.338958** |

### 5.3 Por grupo de jornada

| Grupo | n | RMSE (K) | MAE (K) | Error máximo absoluto (K) |
| --- | ---: | ---: | ---: | ---: |
| `inverse_day_02` | 13 | 64.145782 | 57.404844 | 98.466169 |
| `inverse_day_05` | 12 | 80.797355 | 73.607395 | 131.338958 |
| `normal_day_10` | 12 | 48.824972 | 46.491340 | 72.732452 |
| `normal_day_12` | 13 | 50.245565 | 44.167773 | 99.048352 |

El RMSE de holdout es menor que el de validación, pero son subconjuntos y jornadas diferentes: **no debe presentarse como una segunda mejora experimental ni atribuirse causalmente al modelo**. En las cuatro jornadas reservadas, la predicción fue menos precisa para llamas inversas; el grupo `inverse_day_05` registró el RMSE más alto.

### 5.4 Evidencia criptográfica

- Momento UTC: `2026-11-14T04:26:26.638564+00:00`.
- SHA-256 del historial TSV: `2b6ddaa70ba35be72c1271a2ed237d9cade6f42a337e087ea3df5763f17545ba`.
- SHA-256 del CSV procesado holdout: `fb97e0a56da8a6fb753d86b254cf84644f63d0d88c4a70e2f4e22399ce72cf8b`.
- Informe completo: `runs/holdout-final-v1/final_holdout_metrics.json`.
- Recibo de única ejecución: `runs/holdout-final-v1/execution_receipt.json`.

**El resultado holdout ya fue consumido. No volver a ejecutar `--final` ni borrar el recibo para repetirlo.** No ajustar ningún modelo basándose en esta evaluación.

## 6. Limitaciones y discusión

1. La variable objetivo es una temperatura adiabática **calculada**, no temperatura máxima medida de llama; el error de predicción no indica incertidumbre de termometría real.
2. Las 50 observaciones reservadas proceden de cuatro jornadas agrupadas; la independencia efectiva es menor que la de 50 experimentos aleatorios sin correlación.
3. Los 11 parámetros se ajustaron sobre 134 observaciones, pero esto por sí solo no prueba ausencia de sobreajuste. El sesgo de selección por doce comparaciones merece una interpretación prudente.
4. Los coeficientes del modelo están condicionados por escalado, interacciones y correlación de variables; sus signos no son pruebas causales de mecanismos termodinámicos.
5. El alcance se limita a etileno y condiciones de flujo constante, sin ensayos de propano o rampas.
6. No hay etiquetas tabuladas directas de formación de hollín, extinción o estado estacionario; no se deben inventar valores mediante umbrales de Tad.

## 7. Conclusiones

La ejecución AutoResearch completó doce intentos con un evaluador y particiones fijas y eligió un modelo Ridge cuadrático de composición que redujo el RMSE de validación de 286.978761 a 116.171636 K. La única evaluación reservada del modelo congelado produjo RMSE de 62.170083 K y MAE de 55.232577 K en 50 registros distribuidos en cuatro jornadas. Estos resultados apoyan la utilidad del procedimiento para aproximar **Tad calculada** en este dominio de datos, pero no permiten afirmar resultados sobre hollín, estructura real, radiación o extinción de llamas.

La investigación puede pasar a una siguiente fase, con una pregunta científica distinta y nuevas etiquetas o mediciones verificables, sin reutilizar el holdout anterior para selección de modelos.

## 8. Recomendaciones y reproducibilidad

- Incorporar al repositorio los **dos CSV originales**, junto a `data/README.md` y el inventario con SHA-256; conservar los originales sin transformaciones.
- Preservar el historial `runs/pilot-01/results.tsv` y los dos JSON de `runs/holdout-final-v1/` como evidencia documental, sin editar sus contenidos. Son archivos originalmente excluidos por `.gitignore`; añadirlos selectivamente con `git add -f` una sola vez para publicar el resultado definitivo.
- Mantener congelados `train.py`, las asignaciones y los evaluadores. Publicar resultados finales no autoriza una nueva ejecución de `--final`.
- Para los objetivos científicos NASA A/B/C, obtener selectivamente mediciones o etiquetas auditadas de hollín, temperatura real, radio de llama, estabilidad y mecanismos de extinción a partir de los materiales de NASA PSI-10.

## 9. Referencias

**[1] Axelbaum RL, Sunderland PB, Urban DL, Stocker DP, Frolov SM.** “Advanced Combustion via Microgravity Experiments / Flame Design (ACME/Flame Design)”, **NASA PSI Data Repository, Version 1**. http://doi.org/10.60555/w4zy-bt45. **Fuente primaria de las dos tablas originales usadas.**

**[2] NASA Physical Sciences Informatics.** PSI Data Repository e investigación PSI-10. https://psi.nasa.gov/physci/repo/data/investigations/PSI-10.

**[3] NASA Science Data Portal.** *Science Data Licenses*. https://science.data.nasa.gov/about/license.

**[4] NASA PSI-10.** *ACME/Flame Design Final Report* y documentos científicos, descritos en `knowledge/ACME_DATASET.md`, consultables desde el catálogo de la investigación [1–2].

**[5] Resultados del proyecto actual.** Historial `runs/pilot-01/results.tsv`; recibo y métricas de `runs/holdout-final-v1/`; código congelado en commit `6d4dbe72c660dff475bfee09804ac275382300b6`. Estas son evidencias derivadas del piloto, no documentos originales NASA.
