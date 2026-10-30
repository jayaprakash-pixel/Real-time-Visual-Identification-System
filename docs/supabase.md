# Supabase contract

Module 1 (the frontend) registers persons straight into Supabase. The server (`server/bridge.py`, `PersonSync`) reads them back every `RTVIS_SYNC_INTERVAL` seconds and teaches the AI.

> **Status: inferred, not verified.** The names below come from `frontend/src/services/personsApi.js`. The Supabase project belongs to a teammate and no key has been tested yet. Run `python server/tools/supabase_check.py` once `.env` has the URL and key (leaf P0.4), then correct this file.

| Item | Value used | Where it comes from |
|---|---|---|
| Table | `missing_persons` | `personsApi.js` |
| Columns read by the server | `id`, `name`, `photo_path` | same |
| Columns written by the frontend | `name, age, gender, missing_date, missing_location, description, photo_path` (+ `id`, `created_at` by default) | same |
| Storage bucket | `person-photos`, files at `registrations/<uuid>.jpg\|png` | same |
| Key | publishable (anon) key, in `.env` as `SUPABASE_KEY` | never the service-role key |

## What the server needs from Supabase

1. `select id,name,photo_path` on the table must work with the publishable key (the frontend lists persons the same way, so it should).
2. Photo download through `/storage/v1/object/authenticated/person-photos/<path>`, falling back to the public route if the bucket is public.

## Things to ask the teammate

- Is row-level security on? With the publishable key in every browser bundle, an open table lets anyone read, insert or delete missing-person records (the frontend `Persons` page deletes rows with the same key). The check script prints whether an anonymous insert is refused.
- Is `photo_path` always set, and are photos always a clear frontal face? A photo without a detectable face is skipped (logged, not retried).
- Is there one row per person? The server uses the row `id` (a UUID) as the person id.
