# Supabase contract

Module 1 (the frontend) registers persons straight into Supabase. The server (`server/bridge.py`, `PersonSync`) reads them back every `RTVIS_SYNC_INTERVAL` seconds and teaches the AI.

> **Status: verified read-only on 2026-10-31** with the publishable key. `python server/tools/supabase_check.py` returned: table `missing_persons` HTTP 200 with columns `id, name, photo_path`; bucket `person-photos` HTTP 200; first photo downloaded (HTTP 200). The real `PersonSync` then embedded that photo and added 1 person to the AI store. The check is read-only on purpose (the project is shared). **Not verified:** whether the key can also write (row-level security), and the add/delete cycle against live data.

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

- Is row-level security on? With the publishable key in every browser bundle, an open table lets anyone read, insert or delete missing-person records (the frontend `Persons` page deletes rows with the same key). We did not test writes against live data.
- Is `photo_path` always set, and are photos always a clear frontal face? A photo without a detectable face is skipped (logged, not retried).
- Is there one row per person? The server uses the row `id` (a UUID) as the person id.
