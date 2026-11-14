# Procedencia y reutilización de datos — NASA PSI-10 / Flame Design

## Fuente primaria y atribución

Los archivos de `raw/` proceden de **NASA Physical Sciences Informatics, PSI-10, versión 1**. Deben citarse así:

> Axelbaum RL, Sunderland PB, Urban DL, Stocker DP, Frolov SM. "Advanced Combustion via Microgravity Experiments / Flame Design (ACME/Flame Design)", NASA PSI Data Repository, Version 1, http://doi.org/10.60555/w4zy-bt45.

- DOI: https://doi.org/10.60555/w4zy-bt45
- Investigación NASA PSI: https://psi.nasa.gov/physci/repo/data/investigations/PSI-10
- Guía NASA para licencias y reutilización: https://science.data.nasa.gov/about/license

NASA describe sus datos científicos como abiertos con criterios de uso que dependen de la licencia o aviso específico de cada colección. Los archivos originales incluidos aquí **no se re-licencian como obra del repositorio**. Para cualquier reutilización, respetar los metadatos y avisos que acompañen el conjunto NASA.

## Archivos originales incluidos, sin modificación

| Archivo | Filas | SHA-256 |
| --- | ---: | --- |
| `raw/PSI-10_Experimental table_Flame Design_Normal Flame.csv` | 207 | `4a663292bd3f65201943cc71bd661a70383639276a9176f64105b285bf0b6deb` |
| `raw/PSI-10_Experimental table_Flame Design_Inverse Flame.csv` | 120 | `97933ee9ae0b9ebc6b948a67485a0fe2f8218f753253a4f2be93c40d374c44e4` |

Los dos hashes se registraron antes de los experimentos en `metadata/acme_inventory.json` y fueron verificados contra los archivos adjuntos en el material de trabajo. No modificar encabezados, orden, codificación ni los valores de los CSV originales.

## Archivos generados

`prepare.py` procesa ambos archivos y genera `processed/acme_all.csv`, `processed/acme_tad_pilot.csv`, `processed/acme_tad_train.csv`, `processed/acme_tad_validation.csv` y `processed/acme_tad_holdout.csv`, además de verificar el inventario. Las salidas procesadas son **derivadas regenerables**; las originales y los hashes son la referencia de integridad. La partición se fija por configuración de llama y jornada, con semilla `20261113`.

Las 327 filas originales incluyen 236 ensayos elegibles para el piloto de etileno de flujo constante: 134 entrenamiento, 52 validación y 50 holdout. El objetivo es `Tad (K)` **calculada**, no temperatura real medida.

## Reproducir la preparación, sin repetir la evaluación final

Desde `investigations/ACME/`:

```bash
sha256sum data/raw/*.csv
uv sync
uv run python prepare.py --check
uv run python -m unittest discover -s tests -v
```

**No ejecutar otra vez `evaluate_holdout.py --final`: la evaluación reservada ya fue consumida.** Los resultados definitivos corresponden al informe `analysis/FINAL_TAD_PILOT.md` y a los registros archivados.

## Política de publicación de resultados

Publicar solo los dos originales de NASA que se utilizaron, los hashes y la documentación de procedencia. No añadir videos, grandes archivos suplementarios o materiales con licencia distinta sin revisar sus avisos. Publicar por separado, de forma inalterada, `runs/pilot-01/results.tsv`, `runs/holdout-final-v1/execution_receipt.json` y `runs/holdout-final-v1/final_holdout_metrics.json` para respaldar el reporte científico. Los registros derivan de la ejecución local y no son archivos de NASA.
