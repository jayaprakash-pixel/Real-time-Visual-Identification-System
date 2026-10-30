# Real-time Visual Identification System — plan of record

Arc tracker: `phasedoc/plan.cmd tree`. A leaf is ticked only after its acceptance test has run.
This arc started on 2026-10-30, after Module 2 (AI vision) and most of the frontend already existed. It is not a retrospective seeding: every leaf starts open.

**Goal.** A phone is the CCTV. A laptop is the control room. An operator registers a missing person once. The AI watches the live video and confirms the person over several frames. The system then saves evidence, stores the event and alerts the operator at once. Today three parts exist side by side and are not connected. This arc builds the third part (Module 3, alerts) and connects all three.

**What exists on day one.**
- Module 2 (AI vision): done and working. It detects, tracks, recognises and verifies faces, and calls `on_match` with a result.
- Module 1 (frontend): React console with login, registration, persons list and detection history. Persons use Supabase. Everything else runs on fake data (`USE_MOCK = true`).
- Module 3 (alerts): a 100-line demo that prints and beeps. It uses a 90% threshold that does not match the AI's scoring.

## P0 — Foundation
We set up this tracking window and give it a permanent port (6801). We reserve the port for the server (8010). We create one Python environment for the AI and the server. We need the Supabase address and key from the teammate who owns the Supabase project, so that the server can read the registered persons. Until then the persons sync cannot be tested.

## P1 — Alert engine
This is the heart of Module 3. It decides whether a result from the AI is a real alert, stores it, and tells every channel. A verification gate rejects weak or repeated results (the same person is not announced twice within the cooldown). A store keeps every accepted detection in a small database (SQLite). A dispatcher sends each alert to all channels, and a broken channel never blocks the others. A Telegram message channel exists but is off until the user decides to use it.

An honest note on sound: PM2 runs services as the SYSTEM account, which has no access to the operator's speakers. So the alarm sound and the popup are played by the browser dashboard (P4.3), not by the server.

## P2 — Backend server
One small web server (FastAPI) gives the frontend everything it already asks for: login, system status, the detection list and count, the person list, the live video as a stream of JPEG pictures (MJPEG), and a live alert channel (WebSocket). Every route except the health check needs a login token. The URLs and field names follow what the frontend code expects, so the frontend needs few changes.

## P3 — AI integration
The AI pipeline runs inside the server, in its own thread, without its own window. Each confirmed match goes through the gate, the store and the dispatcher. A background job copies the registered persons from Supabase into the AI's reference store: it downloads each photo, turns it into face numbers (embeddings), and removes persons that were deleted. All settings (camera address, thresholds, cooldown) come from environment variables.

## P4 — Frontend wiring
We turn mock mode off with one environment variable and connect the real server. The dashboard shows the live video and the real system status. A live match opens a popup, plays an alarm and can raise a browser notification. The server also serves the built frontend, so the whole product runs from one address.

## P5 — End-to-end proof and hardening
We prove the whole chain with a test video: a registered person must produce exactly one alert, one history row and one evidence image. An unregistered person must produce none. We inject faults (camera drop, Supabase down, dropped connection) and check recovery. We review security: no secrets in the repository, login on every route, protected evidence images. The server then runs under PM2 and survives a reboot-style service restart.

## P6 — Documentation and release
The README and the landing page status tables are changed to match what was verified, nothing more. The work is pushed to GitHub. A summary note goes into the vault.

## Open questions
- Supabase address and key (owner: teammate). Blocks P0.4 and P3.3.
- Do we want phone alerts (Telegram or SMS)? P1.4 builds the Telegram channel but leaves it off.
