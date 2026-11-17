# ADR 020 — 24-Hour TTL on Bronze Collections, Created Manually in Atlas

**Status:** Accepted
**Date:** 2026-11-17

---

## Context

Bronze lands raw API snapshots in MongoDB Atlas on the free tier (M0, 512 MB). Each bronze run
inserts one document per source, and `adsb_raw` snapshots are large (roughly 100–180 KB each).
Run in a loop, `adsb_raw` grows by hundreds of MB per day and fills the cluster; once full, Atlas
blocks writes and the whole pipeline stops (issue #28 in the original repository).

Bronze is a short-lived landing zone: Silver only reads the **latest** snapshot per source, so
older snapshots have no consumer.

MongoDB's TTL index deletes documents automatically once a date field is older than a set age.
It only works on a real BSON date: pointed at a string it is created without complaint and then
never deletes anything. `bronze.py` stores `fetched_at` as a BSON date for exactly this reason.

## Decision

Create a **TTL index on `fetched_at` with `expireAfterSeconds = 86400` (24 hours)** on both
Bronze collections, `adsb_raw` and `states_all` in the `airlines` database. The indexes are
**created manually in Atlas** (console or `mongosh`), not by application code. The steps and the
verification check are in [mongodb-access.md](../mongodb-access.md#retention-ttl-index).

## Rationale

- **Bounded storage.** With a 24-hour window the collections hold at most a day of snapshots,
  which fits the free tier even with the ETL looping.
- **No consumer loses data.** Silver reads only the newest snapshot, so a 24-hour window loses
  nothing the pipeline uses. The window is also long enough to inspect recent raw data when
  debugging.
- **Why not in `bronze.py`.** `create_index` run at startup would execute against whichever
  cluster `MONGO_URL` points to. If an index on `fetched_at` already exists there with a
  different expiry, MongoDB raises an index-options conflict and bronze would crash at startup.
  That failure would first appear in a deployed environment, after merge. A one-time manual
  step per cluster avoids a code path that can only fail in production.

## Consequences

- **Manual step per cluster.** Every new Atlas cluster needs the two indexes created once; this
  is recorded in `mongodb-access.md` so it is not forgotten.
- **Not instant.** Atlas removes expired documents in a background pass roughly once a minute, so
  a document can outlive its 24 hours briefly.
- **Raw history is not kept.** Anything older than 24 hours is gone from Bronze. If a longer
  history is ever needed (for example for ML), retention has to be reconsidered; the age is a
  single index option and can be changed without touching the code.
- **String dates never expire.** Documents written with `fetched_at` as an ISO string (older
  bronze versions) are ignored by the index and must be migrated or removed by hand.
- **Revisit trigger:** if the Atlas cluster becomes infrastructure-as-code (issue #1), the index
  creation should move there or into a versioned script.
