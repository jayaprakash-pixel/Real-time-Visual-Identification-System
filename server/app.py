"""FastAPI app: the interface the frontend already expects (P2.1 to P2.6, P4.4)."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from auth import AuthError, Users
from config import Settings
from dispatch import Dispatcher
from gate import MatchGate
from hub import Hub
from store import Store

MEDIA_TTL = 3600          # media tokens (image/stream URLs) live one hour


class NullEngine:
    """Stands in for the AI pipeline until it is attached (and in tests)."""
    def latest_jpeg(self): return None
    def status(self): return {"monitoring": "offline", "activeCamera": None, "aiService": "down"}


@dataclass
class Services:
    settings: Settings
    store: Store
    users: Users
    gate: MatchGate
    dispatcher: Dispatcher
    hub: Hub
    engine: object = None                         # needs latest_jpeg() and status()
    persons: Callable = lambda: []                # -> [{"id", "name"}]


def to_api(row, media_token):
    """DB row -> the camelCase shape in frontend/src/services/detectionsApi.js."""
    base = f"/api/detections/{row['id']}"
    scene = f"{base}/scene?token={media_token}"
    return {"id": row["id"], "personId": row["person_id"], "personName": row["person_name"],
            "detectedAt": row["detected_at"], "confidence": row["confidence"],
            "cameraSource": row["camera"], "sceneImageUrl": scene,
            "thumbnailUrl": f"{base}/face?token={media_token}" if row.get("face_path") else scene}


def create_app(svc: Services):
    @asynccontextmanager
    async def lifespan(_):
        svc.hub.loop = asyncio.get_running_loop()      # lets the AI thread push alerts into the event loop
        yield

    app = FastAPI(title="RTVIS server", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    svc.engine = svc.engine or NullEngine()
    app.add_middleware(CORSMiddleware, allow_origins=svc.settings.cors_origins,
                       allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])


    @app.exception_handler(AuthError)
    async def _auth_error(_, e):
        return JSONResponse({"message": e.message, "field": e.field}, status_code=e.status)

    # ---- auth plumbing ----
    def operator(request: Request):
        header = request.headers.get("authorization", "")
        return svc.users.verify(header[7:] if header.lower().startswith("bearer ") else "")

    def media_user(request: Request, token: str = Query("")):
        """Browsers cannot set headers on <img>, so media routes also take ?token= (scope 'media')."""
        header = request.headers.get("authorization", "")
        if header.lower().startswith("bearer "):
            return svc.users.verify(header[7:])
        return svc.users.verify(token, scope="media")

    def media_token(email):
        return svc.users.issue(email, ttl=MEDIA_TTL, scope="media")

    # ---- open routes ----
    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/auth/login")
    async def login(request: Request):
        b = await request.json()
        return svc.users.login(b.get("email"), b.get("password"))

    @app.post("/api/auth/signup")
    async def signup(request: Request):
        b = await request.json()
        return svc.users.signup(b.get("name"), b.get("email"), b.get("password"))

    # ---- protected routes ----
    @app.get("/api/system/status")
    def status(email: str = Depends(operator)):
        return {**svc.engine.status(), "streamUrl": f"/video/stream?token={media_token(email)}",
                "settings": svc.settings.public()}

    @app.get("/api/detections")
    def detections(email: str = Depends(operator), person: str = "", camera: str = "", dateFrom: str = "",
                   dateTo: str = "", confidenceMin: float = None, confidenceMax: float = None,
                   sortBy: str = "detectedAt", sortOrder: str = "desc", page: int = None,
                   pageSize: int = 10, limit: int = None):
        mt = media_token(email)
        # The frontend's "recent alerts" call sends ?limit=N and expects a bare array.
        if limit is not None and page is None:
            rows, _ = svc.store.list(sort_by=sortBy, sort_order=sortOrder, page=1, page_size=limit)
            return [to_api(r, mt) for r in rows]
        page = page or 1
        rows, total = svc.store.list(person or None, camera or None, dateFrom or None, dateTo or None,
                                     confidenceMin, confidenceMax, sortBy, sortOrder, page, pageSize)
        return {"items": [to_api(r, mt) for r in rows], "total": total, "page": page, "pageSize": pageSize}

    @app.get("/api/detections/count")
    def count(email: str = Depends(operator)):
        return {"count": svc.store.count()}

    @app.get("/api/detections/{detection_id}/{kind}")
    def evidence(detection_id: str, kind: str, email: str = Depends(media_user)):
        row = svc.store.get(detection_id)
        path = row and (row["face_path"] if kind == "face" else row["scene_path"] if kind == "scene" else None)
        if not path:
            raise HTTPException(404, "Not found")
        return FileResponse(path, media_type="image/jpeg")   # path comes from our DB, never from the URL

    @app.get("/api/persons")
    def persons(fields: str = "id,name", email: str = Depends(operator)):
        keep = [f for f in fields.split(",") if f in ("id", "name")] or ["id", "name"]
        return [{k: p[k] for k in keep} for p in svc.persons()]

    @app.get("/video/stream")
    def stream(email: str = Depends(media_user)):
        async def frames():
            while True:
                jpeg = svc.engine.latest_jpeg()
                if jpeg:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n"
                await asyncio.sleep(0.1)
        return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")

    @app.websocket("/alerts")
    async def alerts(ws: WebSocket, token: str = ""):
        try:
            email = svc.users.verify(token)
        except AuthError:
            await ws.close(code=4401)
            return
        await ws.accept()
        q, mt = svc.hub.subscribe(), media_token(email)
        try:
            while True:
                got = asyncio.ensure_future(q.get())
                gone = asyncio.ensure_future(ws.receive_text())
                done, pending = await asyncio.wait({got, gone}, return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                if gone in done:
                    gone.result()            # raises WebSocketDisconnect when the client leaves
                    continue
                await ws.send_json(to_api(got.result(), mt))
        except WebSocketDisconnect:
            pass
        finally:
            svc.hub.unsubscribe(q)

    # ---- built frontend (P4.4); mounted last so the API routes win ----
    dist = svc.settings.frontend_dist
    if (dist / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            if path.startswith(("api/", "video/")):
                raise HTTPException(404)
            target = (dist / path).resolve()
            ok = target.is_file() and dist.resolve() in target.parents
            return FileResponse(target if ok else dist / "index.html")

    return app
