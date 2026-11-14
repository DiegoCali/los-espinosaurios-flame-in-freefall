# AutoResearch — NASA PSI-10 / ACME Flame Design

## 1. Misión

Actúa como un agente de investigación experimental siguiendo la metodología de AutoResearch.

Tu objetivo es mejorar progresivamente un modelo de aprendizaje automático que predice la **temperatura adiabática calculada (`Tad`)** de llamas esféricas de difusión en microgravedad, utilizando los datos experimentales de NASA PSI-10 / ACME Flame Design.

Debes investigar, proponer modificaciones, ejecutar experimentos, evaluar resultados y conservar únicamente los modelos que mejoren la métrica principal sin comprometer la validez científica del procedimiento.

La investigación debe ejecutarse en CPU, con recursos computacionales limitados y experimentos reproducibles.

**Importante:** este modelo es un piloto computacional. No predice directamente la formación de hollín, la temperatura real de extinción ni la existencia de llamas estacionarias.

## 2. Contexto científico

**Investigación:** NASA PSI-10 — Advanced Combustion via Microgravity Experiments (ACME).

**Título:** Flame Design: A Novel Approach to Clean Efficient Diffusion Flames.

**Plataforma:** International Space Station (ISS).

**Centro:** NASA Glenn Research Center.

**DOI:** https://doi.org/10.60555/w4zy-bt45

### 2.1 Objetivos científicos de NASA

**Objetivo A — Formación de hollín**

Determinar los límites de aparición de hollín en llamas esféricas normales e inversas, considerando flujo másico, fracción de mezcla estequiométrica (`Zst`), dilución de reactivos y presión.

**Objetivo B — Características de la llama**

Investigar los efectos de las condiciones experimentales sobre la temperatura, el tamaño, el color, la fracción volumétrica de hollín y la posibilidad de alcanzar condiciones estacionarias.

**Objetivo C — Extinción**

Determinar los límites de extinción y distinguir mecanismos radiativos y cinéticos, considerando la composición de reactivos, la presión y las condiciones del flujo.

### 2.2 Hipótesis científicas

1. La formación de hollín requiere condiciones críticas de relación local C/O, temperatura y tasa de deformación del flujo.
2. Bajo las condiciones estudiadas de llamas esféricas de etileno, la extinción radiativa se relaciona con una temperatura máxima real cercana a 1130 K.
3. Pueden existir llamas esféricas de difusión estacionarias incluso con pérdidas de energía por radiación.

Estas hipótesis constituyen el contexto científico del proyecto, pero **no deben considerarse demostradas por el piloto de `Tad`**.

## 3. Alcance del piloto AutoResearch

El modelo utilizará las condiciones iniciales de ensayos de etileno (`C2H4`) con flujos constantes para predecir la temperatura adiabática calculada.

El conjunto de datos se obtuvo de las tablas experimentales de NASA:

- `PSI-10_Experimental table_Flame Design_Normal Flame.csv`
- `PSI-10_Experimental table_Flame Design_Inverse Flame.csv`

Los datos contienen:

| Conjunto | Registros |
|---|---:|
| Registros originales | 327 |
| Registros con `Tad` numérica | 256 |
| Registros elegibles de etileno | 236 |
| Entrenamiento | 134 |
| Validación | 52 |
| Prueba final reservada | 50 |

Se excluyen del piloto las condiciones `RAMP`, `RAMPED`, `LOW O2` y los ensayos con propano. Estos registros se conservan en el conjunto de auditoría.

Las particiones se encuentran fijadas por jornada experimental.

**No está permitido modificar las particiones, la variable objetivo ni las métricas durante los experimentos.**

## 4. Arquitectura del proyecto

El trabajo se realiza exclusivamente dentro de:

`investigations/ACME/`

Los archivos principales son:

| Archivo | Responsabilidad |
|---|---|
| `README.md` | Descripción general y alcance científico |
| `protocol.md` | Protocolo experimental y restricciones |
| `program.md` | Instrucciones del agente AutoResearch |
| `knowledge/ACME_DATASET.md` | Documentación y auditoría del conjunto |
| `prepare.py` | Preparación y particiones invariables |
| `evaluate.py` | Evaluación y métricas invariables |
| `train.py` | Implementación experimental editable |
| `pyproject.toml` | Configuración de dependencias con uv |
| `uv.lock` | Versiones resueltas de dependencias |
| `tests/` | Pruebas automatizadas |
| `runs/` | Historial de experimentos |

### 4.1 Archivo editable

Durante la experimentación, el agente puede modificar **únicamente**:

`investigations/ACME/train.py`

El agente no puede modificar:

- `prepare.py` ni `evaluate.py`.
- `README.md`, `protocol.md` o `program.md`.
- `knowledge/`, `tests/` o `analysis/`.
- `data/raw/`, `data/processed/` o `data/metadata/`.
- `pyproject.toml`, `uv.lock` o `requirements.txt`.
- Archivos `.gitignore`.
- Archivos pertenecientes a otras investigaciones.

El directorio `runs/` puede recibir exclusivamente los archivos que genere automáticamente `evaluate.py`. No se deben alterar manualmente los registros TSV.

## 5. Entorno de ejecución

### 5.1 Rama de trabajo

Todos los experimentos se realizan directamente en:

`feature/psi-10-acme-autoresearch`

**No crear otras ramas.**

No cambiar a `main`, no realizar merges y no modificar el trabajo de las demás investigaciones.

Los experimentos deben realizarse mediante commits normales y reversibles.

Está prohibido utilizar `git reset --hard`, reescribir el historial o realizar `git push --force`.

### 5.2 Gestor de dependencias

Utilizar exclusivamente **uv**.

No utilizar `pip` ni crear entornos virtuales manualmente.

Desde `investigations/ACME/`:

```bash
uv sync
```

Para reducir la variabilidad del consumo de CPU:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

Para verificar el entorno:

```bash
uv run python prepare.py --check

uv run python -m unittest discover -s tests -v
```

El resultado esperado es de diez pruebas automatizadas aprobadas.

No instalar dependencias nuevas durante la ejecución de AutoResearch.

## 6. Contrato del modelo

El archivo `train.py` debe mantener esta interfaz:

```python
MODEL_NAME: str

def fit_predict(
    X_train,
    y_train,
    X_eval,
    seed,
):
    ...
```

La función debe devolver un arreglo NumPy unidimensional que contenga una predicción finita por observación de evaluación.

### 6.1 Datos recibidos

- `X_train`: matriz de 134 filas y 7 características.
- `y_train`: 134 temperaturas adiabáticas calculadas, en kelvin.
- `X_eval`: matriz de 52 filas y 7 características.
- `seed`: semilla fija `20261113`.

La función no recibe las etiquetas de validación ni las de prueba final.

### 6.2 Orden de características

Las columnas son:

| Índice | Característica |
|---|---|
| 0 | `flame_type_inverse` |
| 1 | `burner_reactant_mole_fraction` |
| 2 | `ambient_reactant_fraction_initial` |
| 3 | `burner_reactant_flow_mg_s` |
| 4 | `nitrogen_flow_mg_s` |
| 5 | `total_flow_mg_s` |
| 6 | `pressure_initial_atm` |

Las características representan el papel físico de cada reactivo.

En una llama normal, el quemador suministra combustible; en una llama inversa, suministra oxidante.

No interpretar ambas configuraciones como si inyectaran la misma especie química.

### 6.3 Restricciones de entrenamiento

- Ajustar todos los parámetros utilizando exclusivamente entrenamiento.
- Calcular estadísticas de normalización solo con `X_train`.
- Mantener el comportamiento determinista cuando se utilice la semilla fija.
- No utilizar características posteriores al ensayo.
- No leer datos adicionales desde `train.py`.
- No abrir `data/processed/acme_tad_holdout.csv`.
- No utilizar etiquetas de validación para ajustar el modelo.
- No memorizar identificadores ni observaciones particulares.
- No inventar mediciones ni etiquetas científicas.
- No utilizar la variable calculada `Zst` como entrada del modelo.
- No cambiar las unidades de salida: las predicciones deben estar en kelvin.

## 7. Métrica de optimización

La métrica principal es:

**`val_rmse_k` — Root Mean Squared Error en kelvin.**

El objetivo es minimizarla.

Las métricas secundarias son:

- `val_mae_k`: error absoluto medio.
- `val_max_abs_error_k`: error absoluto máximo.
- `elapsed_seconds`: tiempo de ejecución.
- `peak_memory_mb`: consumo máximo de memoria registrado.

El cálculo de estas métricas está definido exclusivamente en `evaluate.py`.

El agente no puede modificar el evaluador ni utilizar funciones alternativas de puntuación para decidir qué cambios conservar.

### 7.1 Criterio de aceptación

Un candidato se conserva cuando:

1. Se ejecuta sin errores.
2. Produce predicciones finitas y con dimensiones correctas.
3. Reduce el RMSE respecto al mejor candidato aceptado en al menos 0.001 K.
4. Respeta las restricciones científicas y técnicas.
5. No introduce complejidad injustificada.

Estados de evaluación:

- `baseline`: referencia inicial.
- `keep`: candidato con mejora válida.
- `discard`: candidato sin mejora suficiente.
- `crash`: candidato que no pudo evaluarse correctamente.

El estado `keep` automático no sustituye la revisión del código y de sus restricciones.

## 8. Presupuesto experimental

La ejecución inicial utiliza:

```text
RUN_ID: pilot-01
SEED: 20261113
MAX_ATTEMPTS: 12
MAX_CANDIDATE_SECONDS: 120
HARDWARE: CPU
```

Los doce intentos incluyen la línea base.

Cada experimento debe finalizar dentro del presupuesto de ejecución definido en `evaluate.py`.

No utilizar GPU, simulaciones CFD extensivas ni modelos cuyo entrenamiento exceda los recursos disponibles.

## 9. Estado actual de pilot-01

**La ejecución ya comenzó y no debe reiniciarse.**

Los siguientes experimentos están registrados:

| Intento | Modelo | RMSE (K) | Estado |
|---|---|---:|---|
| 1 | Media del entrenamiento | 286.978761 | `baseline` |
| 2 | Ridge, alpha=10 | 178.891824 | `keep` |

Mejor RMSE registrado: **178.891824 K**.

Intentos completados: **2 de 12**.

Intentos restantes: **10**.

El siguiente candidato debe registrarse como **intento 3**.

No volver a ejecutar `--baseline` ni repetir Ridge alpha=10 dentro de `pilot-01`.

Antes de continuar, comprobar que existe:

```text
runs/pilot-01/results.tsv
```

Si el archivo no existe o su contenido no corresponde a los dos intentos anteriores, detener la experimentación y solicitar recuperar el registro original. No recrear artificialmente resultados previos.

## 10. Inicio de la sesión

Desde la raíz del repositorio:

```bash
git switch feature/psi-10-acme-autoresearch

cd investigations/ACME

export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

uv sync

uv run python -m unittest discover -s tests -v

cat runs/pilot-01/results.tsv
```

Comprobar también:

```bash
git status --short

git log -5 --oneline
```

Los archivos protegidos deben estar libres de cambios inesperados.

No modificar archivos ajenos a `train.py` durante los experimentos.

## 11. Ciclo AutoResearch

El agente debe ejecutar el siguiente procedimiento para cada intento restante.

### Paso 1. Analizar resultados

Consultar `runs/pilot-01/results.tsv` e identificar:

- Mejor RMSE alcanzado.
- Mejor versión de `train.py`.
- Último intento ejecutado.
- Experimentos aceptados y descartados.
- Recursos computacionales utilizados.

Utilizar esta información para proponer una hipótesis concreta de mejora.

### Paso 2. Formular una hipótesis

Cada intento debe modificar una idea específica y verificable.

Ejemplos:

- Reducir o aumentar la regularización Ridge.
- Incorporar interacciones entre fracciones molares.
- Comparar un modelo conjunto frente a un modelo que distingue configuraciones normales e inversas.
- Introducir transformaciones polinómicas limitadas.
- Eliminar características redundantes.
- Mejorar el escalado numérico.

Evitar cambios extensos sin justificación.

### Paso 3. Modificar train.py

Editar exclusivamente:

`train.py`

Mantener la interfaz definida en la sección 6.

No modificar los archivos de evaluación, preparación, configuración ni documentación.

### Paso 4. Ejecutar las pruebas

```bash
uv run python -m unittest discover -s tests -v
```

Revisar errores y corregir únicamente `train.py` cuando corresponda.

Si las pruebas no pasan, no presentar el candidato como válido. Documentar el incidente; no alterar manualmente `results.tsv` para simular una evaluación.

### Paso 5. Crear el commit

Antes de evaluar, crear un commit del candidato:

```bash
git add train.py

git commit -m "experiment(acme): DESCRIPCION_DEL_CAMBIO"
```

No incluir archivos adicionales.

### Paso 6. Ejecutar la evaluación

```bash
uv run python evaluate.py --candidate \
  --run-id pilot-01 \
  --description "DESCRIPCION_DEL_CAMBIO"
```

El evaluador añadirá un nuevo registro a:

`runs/pilot-01/results.tsv`

### Paso 7. Interpretar la evaluación

**Si el estado es `keep`:**

- Conservar el nuevo `train.py`.
- Registrar el commit como mejor versión, siempre que supere también la revisión metodológica.
- Continuar el siguiente intento desde ese modelo.

**Si el estado es `discard`:**

- Registrar el resultado.
- Restaurar exclusivamente `train.py` desde el commit del mejor modelo válido anterior.
- Crear un commit de restauración si la versión descartada ya estaba confirmada.

Ejemplo:

```bash
git restore --source=COMMIT_MEJOR_MODELO -- train.py

git add train.py

git commit -m "revert(acme): restore best model"
```

Sustituir `COMMIT_MEJOR_MODELO` por un identificador real previamente verificado.

No utilizar `git reset --hard` ni borrar el registro de experimentos.

**Si el estado es `crash`:**

- Consultar el mensaje de error.
- Registrar el intento como fallido.
- Restaurar o corregir el candidato respetando el presupuesto.
- No modificar `evaluate.py` para evitar el fallo.

### Paso 8. Repetir

Continuar hasta completar el intento 12 o alcanzar un bloqueo que impida continuar de forma metodológicamente válida.

No reiniciar el presupuesto con otro `RUN_ID` para obtener intentos adicionales dentro de esta misma ejecución.

## 12. Primer experimento sugerido

El próximo intento debe evaluar si una regularización Ridge más baja mejora el comportamiento del modelo.

En `train.py`, probar:

```python
MODEL_NAME = "ridge_alpha_1"
RIDGE_ALPHA = 1.0
```

Mantener el resto de la implementación sin cambios.

Ejecutar las pruebas, crear el commit y evaluar:

```bash
uv run python evaluate.py --candidate \
  --run-id pilot-01 \
  --description "Ridge alpha=1"
```

Comparar el RMSE con el mejor valor actual:

**178.891824 K**.

Conservar el cambio únicamente si cumple los criterios establecidos.

Los siguientes experimentos deben decidirse a partir de resultados reales, no de valores esperados o inventados.

## 13. Posibles líneas de investigación computacional

Una vez evaluadas distintas regularizaciones Ridge, considerar las siguientes alternativas.

### 13.1 Modelos por configuración

Examinar si las relaciones entre concentración, flujo y temperatura difieren suficientemente entre llamas normales e inversas como para justificar un modelo con interacciones o coeficientes específicos.

### 13.2 Características polinómicas

Probar términos cuadráticos y productos entre variables de composición, manteniendo un número limitado de parámetros.

Toda transformación debe ajustarse exclusivamente con datos de entrenamiento.

### 13.3 Escalado y regularización

Comparar diferentes estrategias de normalización y regularización, evitando matrices mal condicionadas.

### 13.4 Selección de características

Examinar si existe información redundante, especialmente entre los flujos individuales y el flujo total.

### 13.5 Modelos ligeros no lineales

Si las mejoras lineales se agotan, considerar una formulación no lineal pequeña implementable con las dependencias disponibles y dentro del presupuesto de CPU.

No instalar bibliotecas adicionales durante `pilot-01`.

## 14. Integridad experimental

Las siguientes acciones están estrictamente prohibidas:

- Modificar `prepare.py` o `evaluate.py`.
- Cambiar la semilla fija o la separación por jornada.
- Utilizar las etiquetas del conjunto `holdout`.
- Utilizar `y_validation` para entrenamiento.
- Acceder desde `train.py` a archivos CSV o JSON de evaluación.
- Sustituir predicciones por valores copiados de las tablas.
- Alterar métricas para obtener una mejora artificial.
- Modificar manualmente `results.tsv`.
- Borrar intentos fallidos.
- Reescribir commits o forzar publicaciones.
- Afirmar que `Tad` representa temperatura experimental medida.
- Construir etiquetas de hollín utilizando umbrales arbitrarios sobre `Tad` o `Zst`.

Los resultados deben ser reproducibles, interpretables y estar asociados a una versión concreta del código.

Las restricciones del agente constituyen un protocolo de investigación; no reemplazan el aislamiento del entorno ni la revisión humana de integridad.

## 15. Registro y reproducibilidad

Cada intento debe conservar, como mínimo:

- Número de intento.
- Identificador de ejecución.
- Commit de Git.
- SHA-256 de `train.py`.
- Semilla.
- Nombre del modelo.
- RMSE.
- MAE.
- Error absoluto máximo.
- Tiempo.
- Memoria máxima registrada.
- Estado.
- Descripción de la hipótesis.

El registro debe mantenerse en:

`runs/pilot-01/results.tsv`

No eliminarlo durante las restauraciones del modelo.

Dado que `runs/` se encuentra excluido de Git durante la búsqueda, conservar el directorio local hasta finalizar la investigación y preparar su archivo de evidencias.

## 16. Finalización de la investigación

Al completar los doce intentos, el agente debe:

1. Identificar el mejor modelo válido por RMSE de validación.
2. Restaurar esa versión de `train.py`, si el último candidato no es el mejor.
3. Ejecutar nuevamente las pruebas automatizadas.
4. Verificar que los archivos protegidos no hayan sido modificados.
5. Resumir todos los experimentos realizados.
6. Informar la mejora respecto a la línea base.
7. Documentar el tiempo y la memoria utilizados.
8. Identificar las principales limitaciones del modelo.

El informe debe incluir:

| Indicador | Resultado |
|---|---|
| RMSE de línea base | 286.978761 K |
| RMSE Ridge inicial | 178.891824 K |
| Mejor RMSE final | Según ejecución |
| Mejor MAE final | Según ejecución |
| Intentos totales | Según registro, máximo 12 |
| Cambios aceptados | Según registro |
| Cambios descartados | Según registro |
| Fallos | Según registro |
| Mejor commit | Según historial |

No inventar valores que aún no se hayan obtenido.

### Evaluación final reservada

Los 50 registros `holdout` deben permanecer sin consultar durante todo el ciclo AutoResearch.

La evaluación final se realizará posteriormente, una sola vez, mediante un procedimiento independiente, después de congelar el modelo seleccionado.

No agregar una opción de evaluación `holdout` a `evaluate.py` durante la búsqueda.

## 17. Interpretación científica

Una reducción de RMSE demuestra una mejor aproximación computacional de la temperatura adiabática calculada dentro del protocolo utilizado.

**No demuestra por sí misma:**

- Que el modelo identifique la aparición de hollín.
- Que reproduzca temperaturas máximas medidas.
- Que confirme la extinción radiativa a 1130 K.
- Que determine cuándo una llama alcanza estado estacionario.
- Que generalice a metano, propano u otras configuraciones no incluidas en el piloto.

Los objetivos A, B y C requerirán posteriormente un nuevo conjunto de variables objetivo obtenidas de observaciones experimentales verificables.

## 18. Referencias

- NASA, *Flame Design: A Novel Approach to Clean Efficient Diffusion Flames*, investigación PSI-10.
- NASA, *ACME/Flame Design Final Report*, 2023.
- NASA, *Science Requirements Document for Flame Design*, versión 1.3, 2010.
- NASA, *ACME Science Operations Requirements*, revisión A, 2011.
- Andrej Karpathy, [AutoResearch](https://github.com/karpathy/autoresearch).
- [AutoResearch Pendulum Study](https://github.com/PoncheDeFrutas/autoresearch-pendulum-study).

---

**Instrucción final para el agente:** continúa la ejecución existente `pilot-01` desde el intento 3, trabaja únicamente en la rama `feature/psi-10-acme-autoresearch`, utiliza `uv`, modifica solo `train.py`, respeta el límite de doce intentos y conserva la integridad científica de los resultados.