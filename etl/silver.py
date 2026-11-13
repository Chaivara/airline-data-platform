import logging
from pymongo import MongoClient
import pandas as pd
from pprint import pprint
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# Target Postgres table for the Silver refresh. Env-injected so the same image
# serves prod (map1) and the Q stage environment (q_map1) — set MAP_TABLE per
# Portainer stack. Restricted to a strict allowlist: the value is interpolated
# as a SQL identifier (table names can't be psycopg2 %s params), so the allowlist
# is what keeps it from ever becoming an injection vector.
MAP_TABLE = os.environ.get("MAP_TABLE", "map1")
if MAP_TABLE not in {"map1", "q_map1"}:
    raise ValueError(f"MAP_TABLE must be 'map1' or 'q_map1', got {MAP_TABLE!r}")

col_names = ["icao24", "callsign", "time_position", "longitude", "latitude", "on_ground", "true_track", "vertical_rate"]
cols = [0, 1, 3, 5, 6, 8, 10, 11]


def map_opensky_doc(doc):
    """OpenSky /states/all snapshot → map1 rows (positional state-vector columns)."""
    return [[state[i] for i in cols] for state in doc["states"]]


def map_adsb_doc(doc):
    """adsb.lol snapshot → map1 rows. Fallback source for when OpenSky is unreachable
    (e.g. the AWS VM's egress IP is blocked by OpenSky)."""
    now_ms = doc.get("now")
    rows = []
    for ac in doc.get("ac", []):
        lat, lon = ac.get("lat"), ac.get("lon")
        if lat is None or lon is None:
            continue  # no position fix yet — nothing to map

        alt_baro = ac.get("alt_baro")
        seen_pos = ac.get("seen_pos")
        time_position = int(now_ms / 1000 - seen_pos) if now_ms is not None and seen_pos is not None else None

        rows.append([
            ac.get("hex"),                                   # icao24
            (ac.get("flight") or "").strip() or None,         # callsign
            time_position,
            lon,                                              # longitude
            lat,                                              # latitude
            alt_baro == "ground",                              # on_ground
            ac.get("track"),                                  # true_track
            ac.get("baro_rate", ac.get("geom_rate")),          # vertical_rate
        ])
    return rows


def fetched_at(doc):
    """Read a document's fetched_at as an aware datetime, accepting either type.

    bronze.py used to store this as an ISO string and now stores a real BSON date (a TTL
    index only expires real dates — see issue #28). Both forms therefore coexist until the
    historical documents are migrated, and the two collections migrate at different times.
    Comparing them raw would raise TypeError ("can't compare str to datetime") and take the
    whole silver loop — and with it map1's freshness — down mid-migration.
    """
    value = doc["fetched_at"]
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


try:
    client = MongoClient(os.environ["MONGO_URL"])
    db = client["airlines"]
    opensky_doc = db["states_all"].find_one({}, sort=[("fetched_at", -1)])
    adsb_doc = db["adsb_raw"].find_one({}, sort=[("fetched_at", -1)])

    # Freshest snapshot wins — on the VM, OpenSky calls fail silently (egress
    # blocked) so its snapshot goes stale while adsb_raw keeps updating.
    use_adsb = adsb_doc is not None and (
        opensky_doc is None or fetched_at(adsb_doc) > fetched_at(opensky_doc)
    )

    if use_adsb:
        log.info(f"Using adsb.lol fallback (fetched_at={adsb_doc['fetched_at']}) — fresher than OpenSky snapshot.")
        rows = map_adsb_doc(adsb_doc)
    else:
        log.info(f"Using OpenSky snapshot (fetched_at={opensky_doc['fetched_at']}).")
        rows = map_opensky_doc(opensky_doc)

    log.info(f"Fetched {len(rows)} rows from MongoDB.")
except KeyError as e:
    log.error(f"Missing environment variable: {e}")
    raise
except Exception as e:
    log.error(f"Failed to fetch data from MongoDB: {e}")
    raise

try:
    conn = psycopg2.connect(
        host=os.environ["SUPABASE_DB_URL"],
        port=5432,
        database="postgres",
        # Direct connection uses "postgres"; the Supavisor pooler needs "postgres.<project-ref>".
        # Defaults to "postgres" so the existing deployed stacks keep working unchanged.
        user=os.environ.get("SUPABASE_DB_USER", "postgres"),
        password=os.environ["SUPABASE_DB_PASSWORD"]
    )
    cur = conn.cursor()
    # MAP_TABLE is allowlist-validated above, so this f-string interpolation is injection-safe.
    cur.execute(f"DELETE FROM {MAP_TABLE}")
    snapshot_fetched_at = fetched_at(adsb_doc if use_adsb else opensky_doc)
    execute_values(cur,
        f"INSERT INTO {MAP_TABLE} (icao24, callsign, time_position, longitude, latitude, on_ground, true_track, vertical_rate, created_at, updated_at) VALUES %s",
        [[*row, datetime.now(timezone.utc), snapshot_fetched_at] for row in rows]
    )
    conn.commit()
    cur.close()
    conn.close()
    log.info(f"Written {len(rows)} rows to PostgreSQL.")
except KeyError as e:
    log.error(f"Missing environment variable: {e}")
    raise
except Exception as e:
    log.error(f"Failed to write to PostgreSQL: {e}")
    raise

