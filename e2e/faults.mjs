// Fault injection against a real server + real browser (P5.3). Exit 0 = every check passed.
//   node faults.mjs   (env: RTVIS_TEST_FACES, RTVIS_PY = path to the venv python, RTVIS_ROOT = repo root)
import { chromium } from 'playwright-core'
import { spawn } from 'node:child_process'
import { existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

const faces = process.env.RTVIS_TEST_FACES, py = process.env.RTVIS_PY, root = process.env.RTVIS_ROOT
const PORT = 8012, CAM = 8091, base = `http://127.0.0.1:${PORT}`
const data = mkdtempSync(path.join(tmpdir(), 'rtvis-faults-'))
const exe = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const results = []
const check = (name, ok, d = '') => { results.push(ok); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${d ? '  ' + d : ''}`) }

const kill = (p) => new Promise((r) => { if (!p || p.exitCode !== null) return r(); p.once('exit', r); spawn('taskkill', ['/PID', p.pid, '/T', '/F']) })
const camera = () => spawn(py, [path.join(root, 'e2e/mjpeg_camera.py'), path.join(faces, 'positive.mp4'), String(CAM)], { stdio: 'ignore' })
const server = () => spawn(py, [path.join(root, 'server/run.py')], {
  stdio: 'ignore',
  env: { ...process.env, RTVIS_DATA_DIR: data, RTVIS_PORT: String(PORT), RTVIS_CAMERA_ID: 'FAULTCAM', PYTHONPATH: `${root}/server;${root}/ai_vision`,
         RTVIS_CAMERA_SOURCE: `http://127.0.0.1:${CAM}/video`, SUPABASE_URL: 'http://127.0.0.1:9', SUPABASE_KEY: 'unreachable', RTVIS_SYNC_INTERVAL: '5' },
})
const up = async () => { for (let i = 0; i < 60; i++) { try { if ((await fetch(base + '/health')).ok) return true } catch {} await sleep(1000) } return false }
const waitFor = async (fn, seconds) => { const end = Date.now() + seconds * 1000; while (Date.now() < end) { try { if (await fn()) return true } catch {} await sleep(500) } return false }

let cam = camera(), srv = server()
const browser = await chromium.launch({ executablePath: exe, headless: true })
try {
  check('server up', await up())
  await fetch(base + '/api/auth/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'Op', email: 'op@example.com', password: 'password123' }) })
  const page = await browser.newPage()
  const errors = []
  page.on('pageerror', (e) => errors.push(String(e)))
  await page.goto(base)
  await page.fill('#email', 'op@example.com'); await page.fill('#password', 'password123'); await page.click('button[type=submit]')
  await page.waitForSelector('.stats-grid')
  const badge = () => page.locator('.stat-status-badge').innerText()
  const link = () => page.locator('.dashboard-conn-status').innerText()
  const streamOk = () => page.evaluate(() => document.querySelector('.stream-media-wrapper img')?.naturalWidth > 0)
  check('baseline: Active + stream + Live', await waitFor(async () => (await badge()).includes('Active') && await streamOk() && (await link()).includes('Live'), 40))

  // 1. Supabase unreachable from the start: server keeps serving and reports it
  const token = (await (await fetch(base + '/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: 'op@example.com', password: 'password123' }) })).json()).token
  const status = await (await fetch(base + '/api/system/status', { headers: { Authorization: `Bearer ${token}` } })).json()
  check('Supabase down: server up, status reports personSync not ok, no key/url leaked',
    status.personSync?.ok === false && !JSON.stringify(status).includes('unreachable') && !JSON.stringify(status).includes('127.0.0.1:9'), JSON.stringify(status.personSync))

  // 2. Camera drops
  await kill(cam)
  check('camera drop: dashboard shows Idle, server stays healthy', await waitFor(async () => (await badge()).includes('Idle') && (await fetch(base + '/health')).ok, 60))
  cam = camera()
  check('camera back: Active again without page reload', await waitFor(async () => (await badge()).includes('Active'), 60))
  check('camera back: stream image recovers', await waitFor(streamOk, 30))

  // 3. Server (WebSocket) drops and returns
  await kill(srv)
  check('server down: realtime link shows Reconnecting', await waitFor(async () => (await link()).includes('Reconnecting'), 20))
  srv = server()
  check('server back: realtime link Live again, no reload', await waitFor(async () => (await link()).includes('Live'), 90))
  check('server back: Active again', await waitFor(async () => (await badge()).includes('Active'), 60))
  check('no uncaught page errors', errors.length === 0, errors.slice(0, 2).join(' | '))
} finally {
  await browser.close(); await kill(cam); await kill(srv)
}
process.exit(results.every(Boolean) ? 0 : 1)
