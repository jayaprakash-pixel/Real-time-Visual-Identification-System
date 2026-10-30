# End-to-end results

Runner: `e2e/run.ps1` (fresh data dir, one registered person, real server, headless Edge via playwright-core).
Test media: `RTVIS_TEST_FACES` folder. The faces are public press photos kept **outside the repository**. The registered reference photo and the video frames are two different photos of the same person (cosine 0.69). The negative video shows a different person (cosine 0.02).

## P5.1 Positive: registered person
`e2e\run.ps1 -Video mixed.mp4 -Expect alert` (30 s of the unregistered face, then 20 s of the registered face), 2026-10-31:

| Check | Result |
|---|---|
| Login through the UI reaches the dashboard | PASS |
| Live stream image loaded (naturalWidth 800) | PASS |
| Monitoring badge Active, realtime link Live | PASS |
| Alert popup appeared with the person's name | PASS |
| Alert reached the browser within 2 s of detection | PASS (at most 481 ms; detection time is truncated to whole seconds) |
| Alarm played exactly once | PASS |
| Alert evidence image loads (image/jpeg) | PASS |
| History lists exactly 1 detection | PASS |
| 0 console errors and 0 HTTP errors | PASS |
| Evidence on disk | 1 scene image |

## P5.2 Negative: unregistered person
`e2e\run.ps1 -Video negative.mp4 -Expect none -Wait 30`: no popup, history empty (0 rows), 0 scene images on disk, 0 console errors. PASS.

## Defects found by these runs (and fixed)
1. The status poll ran before login and received HTTP 401 (it also triggers a logout in the API client). Polling now starts only after login.
2. `httpx` logged the Telegram bot token inside the request URL (found by `test_telegram.py`). The `httpx` and `httpcore` loggers are now WARNING level.

## Not covered here
Phone camera over Wi-Fi (a video file stands in for the stream), real Supabase (a fake Supabase server stands in; see P0.4 and P3.3), several simultaneous cameras.

## P5.3 Fault injection
`node e2e/faults.mjs` (fake phone camera = MJPEG server on :8091; real server; headless Edge), 2026-10-31. All PASS:

| Fault | Observed |
|---|---|
| Supabase unreachable from the start | Server up; `personSync.ok=false` (error class only, no URL or key in the status JSON) |
| Camera stream killed | Dashboard badge changes to Idle; `/health` still 200 |
| Camera restarted | Badge returns to Active and the stream image reloads, no page reload |
| Server process killed | Realtime link shows Reconnecting |
| Server restarted (same data dir) | Realtime link Live again, status Active, no page reload, no uncaught page errors |
