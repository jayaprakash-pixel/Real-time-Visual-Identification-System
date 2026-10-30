"""P0.4: checks the Supabase settings in .env without printing any secret.
   python server/tools/supabase_check.py"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import Settings  # noqa: E402

s = Settings.from_env()
if not (s.supabase_url and s.supabase_key):
    sys.exit("SUPABASE_URL and SUPABASE_KEY are not set in .env")

h = {"apikey": s.supabase_key, "Authorization": f"Bearer {s.supabase_key}"}
r = httpx.get(f"{s.supabase_url}/rest/v1/{s.supabase_table}", params={"select": "id,name,photo_path", "limit": 3}, headers=h, timeout=10)
print(f"select {s.supabase_table}: HTTP {r.status_code}")
rows = r.json() if r.status_code == 200 else []
print(f"  rows returned: {len(rows)}; columns: {sorted(rows[0]) if rows else 'n/a (table empty)'}")

b = httpx.post(f"{s.supabase_url}/storage/v1/object/list/{s.supabase_bucket}", headers=h, json={"prefix": "registrations", "limit": 3}, timeout=10)
print(f"list bucket {s.supabase_bucket}: HTTP {b.status_code}")

if rows and rows[0].get("photo_path"):
    p = httpx.get(f"{s.supabase_url}/storage/v1/object/authenticated/{s.supabase_bucket}/{rows[0]['photo_path']}", headers=h, timeout=15)
    print(f"download first photo: HTTP {p.status_code}, {len(p.content)} bytes")

# Read-only on purpose: this project is shared. Whether the key can also WRITE is a question for the
# project owner (row-level security), not something to test against live data.
ok = r.status_code == 200 and b.status_code == 200
sys.exit(0 if ok else 1)
