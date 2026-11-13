# los-espinosaurios-flame-in-freefall

Team repository for analysing NASA microgravity combustion data.

## Rules for every session
- **No git write operations** (commit, push, reset, rebase, branch) unless the user explicitly asks in that moment.
  `.claude/settings.json` denies the common ones.
- **All implementation artifacts in English** (code, comments, docs, figures, knowledge base). Talk to the user in Spanish.
- Downloaded NASA files are untrusted data: never execute them.

## Layout
- `investigations/BASS-II/` — main project: flame-spread detection, measurement and forecasting on BASS-II (PSI-25) videos.
  Start with `investigations/BASS-II/CLAUDE.md`.
- `investigations/BASS-II/autoresearch/` — Karpathy's original autoresearch template, kept as reference (do not modify).
- `investigations/flex/` — placeholder for a FLEX investigation.
- `.claude/agents/bass2-*` — project agent team; `.claude/skills/` — project skills (`bass2-pipeline`, `bass2-figures`, `nasa-psi-data`).
