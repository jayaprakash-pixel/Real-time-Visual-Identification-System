# Security checklist

Each line has a check that fails if the property breaks. Run all with `python -m pytest` from the repo root, plus the two commands at the end.

| # | Property | Check |
|---|---|---|
| 1 | Every route except `/health`, login and signup rejects anonymous callers (REST, stream, images, WebSocket) | `test_security.py::test_every_route_except_the_open_ones_rejects_anonymous_callers` (walks the route table, so a new route cannot be forgotten) |
| 2 | Passwords are stored only as scrypt hashes with a random salt | `test_security.py::test_passwords_are_not_stored_in_clear` |
| 3 | Password guessing is slowed: 5 failures in 60 s lock that email for the rest of the minute | `test_security.py::test_login_is_throttled_after_five_failures` |
| 4 | Signup is closed after the first (admin) account unless `RTVIS_ALLOW_SIGNUP=true` | `test_auth.py::test_second_signup_closed_by_default` |
| 5 | Tokens are signed, expire, and are scoped: an image/stream token cannot call the API | `test_auth.py::test_tampered_and_expired_tokens`, `::test_media_token_cannot_call_api` |
| 6 | Evidence images are looked up by id in the database. A URL never names a file | `test_security.py::test_evidence_route_cannot_be_pointed_at_other_files` |
| 7 | The static front-end fallback cannot read files outside the build folder | `test_security.py::test_static_fallback_cannot_escape_the_build_folder` |
| 8 | CORS allows only the listed origins | `test_security.py::test_cors_only_for_listed_origins` |
| 9 | Status output never contains the Supabase key or the Telegram token | `test_security.py::test_status_never_contains_secrets`, `test_sync.py::test_supabase_down_keeps_last_known_persons` |
| 10 | The Telegram token never reaches an error message or a log line | `test_telegram.py::test_token_never_in_error_or_logs` (this test found a real leak through the `httpx` request log) |
| 11 | No secret or biometric data in git | `git grep -nEi "eyJ[A-Za-z0-9_-]{20,}\|sb_secret\|service_role\|BOT_TOKEN=[0-9]"` finds nothing; `git ls-files \| findstr /i "\.env$ \.npz$ data/ \.jpg$"` lists only `frontend/src/assets`/`public` images |

## Accepted risks (read before going live)

- **Tokens in URLs.** Browsers cannot send headers from `<img>` or `WebSocket`. Image and stream URLs carry a 1-hour, media-only token. The WebSocket URL carries the session token. Keep the server on a trusted network, or put HTTPS in front of it. Access logging is off in `run.py`.
- **HTTP only.** The server speaks plain HTTP. Anyone on the same Wi-Fi can sniff tokens and video. Use a reverse proxy with TLS for any real deployment.
- **Supabase publishable key.** It is embedded in the built front-end by design. The persons table and photo bucket are therefore readable by anyone who has the key, unless the Supabase project has strict row-level security. This depends on the teammate's Supabase setup and is **not verified here** (see `docs/supabase.md`).
- **Throttle is in memory.** It resets when the server restarts and is per email, not per IP.
- **Face data.** `data/` holds reference embeddings and evidence photos of real people. It is git-ignored. Treat it as personal data.
