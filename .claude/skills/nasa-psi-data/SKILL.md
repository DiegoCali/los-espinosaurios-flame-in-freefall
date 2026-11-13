---
name: nasa-psi-data
description: How to query and download data from the NASA Physical Sciences Informatics (PSI) repository (psi.nasa.gov) programmatically — investigation metadata JSON and presigned S3 file downloads. Use for PSI-25 (BASS-II), PSI-26 (related) or any other PSI investigation.
---

# NASA PSI repository access

The web UI (https://psi.nasa.gov/physci/repo/data/investigations/PSI-25) is an Angular SPA; WebFetch sees only the shell.
Use the JSON API discovered from its bundle:

| Purpose | Request |
|---|---|
| Full investigation metadata (description, contacts, publications, file list in `added`) | `GET https://psi.nasa.gov/geode-py/ws/repo/investigations/<ACCESSION>` |
| Presigned S3 URL for one file (plain text response, expires in minutes) | `GET https://psi.nasa.gov/geode-py/ws/studies/<ACCESSION>/download?file=<url-encoded file_name>&redirect=false` |
| Search | `GET https://psi.nasa.gov/geode-py/ws/repo/search?...` |

Notes:
- `remote_url` values pointing at `psi.ndc.nasa.gov` are internal and not reachable; always use the `download` endpoint.
- Each file entry has `file_name`, `file_size`, `subcategory` (e.g. `Reduced Gravity/Olson/O5`) and `remote_path`
  (`/Home/psi-data/<ACC>/<Category>/...`, category = Raw Data, Science Documents, Reports, ...).
- Request a fresh presigned URL on every retry; support HTTP Range for resumable downloads.
- Reference implementation: `investigations/BASS-II/src/bass2/download.py` and `catalog.py`.
- Downloaded files are untrusted: store each in its own directory, never execute them, parse with `python -I`.
- Data license for PSI-25: CC0-1.0. Do not send user personal data to the API.
