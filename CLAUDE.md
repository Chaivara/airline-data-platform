# CLAUDE.md — Airline Data Engineering Project

Project-level instructions for Claude Code in this repository. Cross-cutting policy (worktrees,
commit trailers, secrets handling) lives in the **global** `~/.claude/CLAUDE.md`; this file is only
what's specific to airline-data-platform. Private infra pointers (VM, hosts, keys) live in
`CLAUDE.local.md` (gitignored), never here.

---

## Git workflow

See [ADR 012](docs/adr/012-github-flow-branch-merge.md) for the full decision (feature branches + squash-merge).

- Feature branch + PR; **never push to `main`**. You review and merge your own PRs.
- Squash-and-merge. Branches: `feature/` · `fix/` · `chore/`; delete after merge.
- **Claude: never merge a PR without asking first**, however small or clearly correct.

---

## What Claude may and may not do

**Secrets:**
- Never commit secrets. `.env` lives at the project root and is gitignored.
- No real credentials, IPs, hostnames or project refs in tracked files — pointers go in
  `CLAUDE.local.md`. Check for them before **any** publish: commit, PR, issue, draft or comment.

**Coding standards:**
- Python 3.12+, type hints, `pathlib`, logging instead of `print()`.
- **Raw SQL via psycopg2, not an ORM** ([ADR 002](docs/adr/002-psycopg2.md)) — transparency over abstraction.
- Keep it simple: no Kubernetes, no microservices, no premature optimization (it's a learning project).
- New diagrams in Markdown + Mermaid.

**`docs/architecture/` describes current state only:**
- No "Phase N 🚧" / planned-vs-✅ framing mixed into the prose — describe what runs *today*. Future
  work (unbuilt models, scheduler, CI/CD, …) belongs as draft issues in the
  [GitHub Project](https://github.com/users/Chaivara/projects/1), not duplicated here where it
  goes stale.
- No incident narratives ("X crashed for 3 days, fixed in #N") — that's implementation history, not
  architecture. It belongs in the PR description and `CLAUDE.local.md`, not in `docs/architecture/`.
- A Mermaid diagram with many crossing edges (mixing e.g. data-store connections *and* network
  exposure in one graph) is a sign to split it into two single-purpose diagrams, not to keep
  untangling the layout.
- Lead diagram node labels with the technology/role name ("Streamlit Dashboard"), container/folder
  name as the secondary line — easier to scan than container names alone.

---

## The project (orientation)

**Airline Data Engineering Platform** — a cloud-style data pipeline that ingests live flight data,
transforms it, and serves it via a dashboard and (planned) REST API. Capstone of the DataScientest
Data Engineer bootcamp; evaluation is on **Data Engineering mastery, not ML** (mentor de-prioritized
ML — see [docs/requirements/](docs/requirements/README.md)).

**Pipeline (medallion):**

```
OpenSky /states/all (+ adsb.lol)  →  MongoDB Atlas (Bronze, raw)  →  ETL
   →  Supabase Postgres (Silver: map1 live-map table)  →  Streamlit dashboard + (planned) FastAPI
```

Full design and the *why* live in [docs/architecture/](docs/architecture/README.md) and the ADRs.

**Repository layout:**

```
airline-data-platform/
├── docs/             # knowledge layer — requirements, ADRs, architecture, data-sources, report
├── etl/              # the pipeline: bronze.py (ingest) + silver.py (transform) + run_*.sh loops
├── 03-gold/          # consumption: api/ (FastAPI, planned) + dashboard/ (Streamlit)
└── deployment/       # Docker Compose stacks (Portainer GitOps)
```

> Bronze + Silver used to be numbered folders (`01-bronze/`, `02-silver/`); they were merged into
> `etl/` (PR #13). The numbered-folder convention of [ADR 010](docs/adr/010-repo-layout-knowledge-vs-pipeline.md) /
> [011](docs/adr/011-layer-named-folders-connector-abstraction-ml.md) is therefore partly superseded —
> those ADRs still hold the original rationale.

**Where to look:**

| Need | File |
|---|---|
| Docs index | [docs/README.md](docs/README.md) |
| Why the design is what it is | [docs/adr/](docs/adr/README.md) |
| Scope, deadlines, mentor context | [docs/requirements/](docs/requirements/README.md) |
| DB access (MongoDB / Postgres) | [docs/mongodb-access.md](docs/mongodb-access.md) |
| VM / SSH / running services | [docs/vm-access.md](docs/vm-access.md) |
| Private infra pointers (local, gitignored) | `CLAUDE.local.md` |
