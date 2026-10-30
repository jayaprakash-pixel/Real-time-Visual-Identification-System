// PM2 process for the RTVIS server (AI pipeline + alerts + API + built frontend), port 8010.
// PM2 runs as SYSTEM and cannot see per-user env vars: camera, Supabase and Telegram settings
// come from the git-ignored .env in this folder (see .env.example).
const root = __dirname.split(require("path").sep).join("/");
module.exports = {
  apps: [{
    name: "rtvis-server",
    script: "server/run.py",
    interpreter: `${root}/.venv/Scripts/python.exe`,
    cwd: root,
    autorestart: true,
    max_restarts: 10,
    out_file: `${root}/data/server.out.log`,
    error_file: `${root}/data/server.err.log`,
    env: {
      PYTHONPATH: `${root}/server;${root}/ai_vision`,
      PYTHONUNBUFFERED: "1",
      RTVIS_HOST: "127.0.0.1",
      RTVIS_PORT: "8010",
    },
  }],
};
