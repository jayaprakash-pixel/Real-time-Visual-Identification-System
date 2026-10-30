// PM2 process for this arc's phasedoc cockpit. Shared cockpit code, arc chosen by env: never fork.
const arc = __dirname.split(require("path").sep).join("/");
module.exports = {
  apps: [{
    name: "phasedoc-rtvis",
    script: "C:/whitenoise/phasedoc/cockpit.py",
    interpreter: "C:/Program Files/Python311/python.exe",
    cwd: arc,
    autorestart: true,
    max_restarts: 10,
    env: {
      PHASEDOC_DB: `${arc}/plan.db`,
      PHASEDOC_PLAN: `${arc}/PLAN.md`,
      PHASEDOC_ARCH: `${arc}/ARCHITECTURE.md`,
      PHASEDOC_RESOURCES: `${arc}/resources.json`,
      PHASEDOC_EXPLAINERS: `${arc}/explainers.json`,
      PHASEDOC_PROGRESS: `${arc}/PROGRESS.md`,
      PHASEDOC_PROGRESS_PATTERN: "rtvis|phasedoc|P[0-9]",
      PHASEDOC_TITLE: "Real-time Visual Identification System: phasedoc",
      PHASEDOC_SUBTITLE: "Internal builders' window · ticks follow real acceptance runs",
      PHASEDOC_HOST: "127.0.0.1",
      PHASEDOC_PORT: "6801",
      PYTHONUNBUFFERED: "1",
    },
  }],
};
