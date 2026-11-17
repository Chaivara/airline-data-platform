# Architecture Decision Records (ADRs)

Each ADR documents one significant decision: the context, the choice, the alternatives we considered, and the consequences. They are the single source of truth for **why** the architecture looks the way it does.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [001](001-postgres-first.md) | PostgreSQL First, MongoDB in Phase 2 | Accepted | 2026-05-12 |
| [002](002-psycopg2.md) | psycopg2 as PostgreSQL Driver | Accepted | 2026-05-12 |
| [003](003-dual-stream.md) | Dual-Stream ADS-B Strategy (OpenSky + adsb.lol) | Accepted | 2026-05-13 |
| [004](004-mongo-as-multisource-hub.md) | MongoDB as Multi-Source Landing Zone Hub | Accepted | 2026-05-18 |
| [005](005-opensky-mongo-migration.md) | OpenSky Pipeline Migration: PostgreSQL → MongoDB | Accepted | 2026-05-18 |
| [006](006-mongo-atlas-migration.md) | MongoDB Migration: Self-hosted on VM → MongoDB Atlas | Accepted | 2026-05-27 |
| [007](007-decouple-from-liora-vm.md) | Decouple from Liora VM; Dedicated Cloud Compute + Neon Postgres | Accepted | 2026-05-27 |
| [008](008-airline-attribution-star-schema.md) | Airline Attribution: Star (resolved `airline_icao`) over Snowflake | Accepted | 2026-06-02 |
| [009](009-states-api-silver-model.md) | Silver Model: OpenSky States as central fact; adsb.lol Bronze-only | Accepted | 2026-06-02 |
| [010](010-repo-layout-knowledge-vs-pipeline.md) | Repo Layout: `docs/` knowledge layer + numbered pipeline phases | Accepted | 2026-06-02 |
| [011](011-layer-named-folders-connector-abstraction-ml.md) | Layer-named folders, data-connector abstraction, ML placement | Accepted | 2026-06-10 |
| [012](012-github-flow-branch-merge.md) | GitHub Flow — branching & merge (feature branches + squash-merge) | Accepted | 2026-06-23 |
| [014](014-adsb-lol-silver-fallback.md) | adsb.lol Promoted to Silver as an Operational Fallback (OpenSky VM egress block) | Accepted | 2026-06-30 |
| [015](015-etl-scheduling-docker-loop.md) | ETL Scheduling Stays a Docker Loop, Not systemd | Accepted | 2026-07-01 |
| [018](018-mono-repo.md) | Mono-Repo: Application Code, Deployment Config, and Infrastructure in One Repository | Accepted | 2026-07-05 |
| [019](019-cloudflare-tunnel-ingress.md) | Cloudflare Tunnel as the Only Ingress; No Reverse Proxy, No Inbound Web Ports | Accepted | 2026-07-05 |
| [020](020-bronze-ttl-index-manual-atlas.md) | 24-Hour TTL on Bronze Collections, Created Manually in Atlas | Accepted | 2026-11-17 |

> Numbering gaps (013, 016, 017) are ADRs still in local draft state (`*.draft.md`, gitignored) —
> a draft reserves its number when writing starts and appears here once promoted via its own PR.

## Format

Each ADR follows this structure:

- **Context** — what situation required a decision
- **Decision** — what we chose
- **Rationale** — why, including rejected alternatives
- **Consequences** — what changes because of this decision

## When to write a new ADR

Write one when:
- A choice is hard to reverse (technology, architecture pattern, vendor)
- Multiple reasonable alternatives existed
- A future team member would ask "why did they do it that way?"

Do **not** write ADRs for:
- Reversible coding decisions (variable names, function signatures)
- Routine library upgrades
- Implementation details that are obvious from the code
