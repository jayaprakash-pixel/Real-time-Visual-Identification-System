"""Settings from environment variables, with the repo-root .env as a fallback (P3.4)."""

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path=ROOT / ".env"):
    """Minimal KEY=VALUE reader. Real environment variables win over the file."""
    if not Path(path).is_file():
        return
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _flag(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    host: str = "127.0.0.1"
    port: int = 8010
    data_dir: Path = ROOT / "data"
    camera_source: str = "0"
    camera_id: str = "CAM01"
    ai_enabled: bool = True
    min_percent: float = 55.0
    cooldown: float = 30.0
    sync_interval: float = 30.0
    allow_signup: bool = False
    token_hours: float = 12.0
    cors_origins: list = field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    frontend_dist: Path = ROOT / "frontend" / "dist"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_table: str = "missing_persons"
    supabase_bucket: str = "person-photos"
    telegram_token: str = ""
    telegram_chat_id: str = ""

    @classmethod
    def from_env(cls):
        load_dotenv()
        e = os.environ.get
        return cls(
            host=e("RTVIS_HOST", "127.0.0.1"),
            port=int(e("RTVIS_PORT", "8010")),
            data_dir=Path(e("RTVIS_DATA_DIR", str(ROOT / "data"))),
            camera_source=e("RTVIS_CAMERA_SOURCE", "0"),
            camera_id=e("RTVIS_CAMERA_ID", "CAM01"),
            ai_enabled=_flag("RTVIS_AI_ENABLED", True),
            min_percent=float(e("RTVIS_MIN_PERCENT", "55")),
            cooldown=float(e("RTVIS_COOLDOWN", "30")),
            sync_interval=float(e("RTVIS_SYNC_INTERVAL", "30")),
            allow_signup=_flag("RTVIS_ALLOW_SIGNUP", False),
            cors_origins=[o for o in e("RTVIS_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o],
            supabase_url=e("SUPABASE_URL", ""),
            supabase_key=e("SUPABASE_KEY", ""),
            supabase_table=e("SUPABASE_TABLE", "missing_persons"),
            supabase_bucket=e("SUPABASE_BUCKET", "person-photos"),
            telegram_token=e("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=e("TELEGRAM_CHAT_ID", ""),
        )

    def public(self):
        """Settings safe to show on the status endpoint (no secrets)."""
        return {"cameraSource": "stream" if self.camera_source.startswith("http") else self.camera_source,
                "cameraId": self.camera_id, "minPercent": self.min_percent, "cooldown": self.cooldown,
                "syncInterval": self.sync_interval, "aiEnabled": self.ai_enabled}
