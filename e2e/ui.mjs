// Browser walk against a running server.
//   node ui.mjs <baseUrl> <email> <password> <expect: alert|none> [personName] [waitSeconds]
// Exit code 0 = every check passed. Prints one line per check.
import { chromium } from 'playwright-core'
import { existsSync } from 'node:fs'

const [base, email, password, expect = 'alert', person = 'Test Person', wait = '60'] = process.argv.slice(2)
const exe = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
             'C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync)
const results = []
const check = (name, ok, detail = '') => { results.push(ok); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`) }

const browser = await chromium.launch({ executablePath: exe, headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
const errors = []
page.on('console', (m) => m.type() === 'error' && errors.push(m.text()))
page.on('response', (r) => r.status() >= 400 && errors.push(`HTTP ${r.status()} ${r.url().replace(/token=[^&]+/, 'token=...')}`))
page.on('pageerror', (e) => errors.push(String(e)))
let alertLatencyMs = null
page.on('websocket', (ws) => ws.on('framereceived', (f) => {
  try { const a = JSON.parse(f.payload); if (a.detectedAt && alertLatencyMs === null) alertLatencyMs = Date.now() - new Date(a.detectedAt).getTime() } catch {}
}))
await page.addInitScript(() => {            // count alarm playbacks
  window.__plays = 0
  const play = HTMLMediaElement.prototype.play
  HTMLMediaElement.prototype.play = function () { window.__plays++; return play.call(this) }
})

await page.goto(base)
await page.fill('#email', email)
await page.fill('#password', password)
await page.click('button[type=submit]')
await page.waitForSelector('.stats-grid', { timeout: 15000 })
check('login reaches dashboard', true)

const img = page.locator('.stream-media-wrapper img')
await img.waitFor({ timeout: 15000 })
await page.waitForFunction(() => document.querySelector('.stream-media-wrapper img')?.naturalWidth > 0, null, { timeout: 15000 })
check('live stream image loaded', true, `naturalWidth=${await img.evaluate((e) => e.naturalWidth)}`)
check('monitoring badge Active', (await page.locator('.stat-status-badge').innerText()).includes('Active'))
check('realtime link Live', (await page.locator('.dashboard-conn-status').innerText()).includes('Live'))

const deadline = Date.now() + Number(wait) * 1000
let popup = false
while (Date.now() < deadline && !popup) popup = await page.locator('.alert-card').count() > 0 || (await page.waitForTimeout(500), false)

if (expect === 'alert') {
  check('alert popup appeared', popup)
  if (popup) {
    check('popup shows person name', (await page.locator('.alert-card').first().innerText()).includes(person))
    // detectedAt is truncated to whole seconds, so this overstates the true latency by under 1 s
    check('alert reached the browser within 2 s of detection', alertLatencyMs !== null && alertLatencyMs <= 2000, `latency<=${alertLatencyMs} ms`)
    check('alarm played exactly once', (await page.evaluate(() => window.__plays)) === 1, `plays=${await page.evaluate(() => window.__plays)}`)
    await page.screenshot({ path: 'popup.png' })
    const src = await page.locator('.alert-card img').first().getAttribute('src')
    const r = await page.request.get(src)
    check('alert image loads', r.ok() && (r.headers()['content-type'] || '').includes('image/jpeg'))
  }
  await page.goto(base + '/history')
  await page.waitForSelector('.history-table tbody tr:not(.skeleton-row)', { timeout: 15000 })
  const rows = await page.locator('.history-table tbody tr:not(.skeleton-row)').count()
  check('history lists the detection', rows === 1 && (await page.locator('.table-person-name').first().innerText()) === person, `rows=${rows}`)
} else {
  check('no alert popup for unregistered person', !popup)
  await page.goto(base + '/history')
  await page.waitForTimeout(3000)
  const rows = await page.locator('.history-table tbody tr:not(.skeleton-row) .table-person-name').count()
  check('history empty', rows === 0, `rows=${rows}`)
}
check('0 console errors', errors.length === 0, errors.slice(0, 3).join(' | '))
await browser.close()
process.exit(results.every(Boolean) ? 0 : 1)
