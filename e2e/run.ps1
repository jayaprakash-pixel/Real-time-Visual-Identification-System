# End-to-end run: fresh data dir, register one person, start the server on a test video, walk the UI.
#   .\e2e\run.ps1 -Video mixed.mp4 -Expect alert
#   .\e2e\run.ps1 -Video negative.mp4 -Expect none
# Needs RTVIS_TEST_FACES (folder with image_01..03.jpg and the .mp4 files): real faces are never committed.
param(
  [Parameter(Mandatory)][string]$Video,
  [ValidateSet('alert', 'none')][string]$Expect = 'alert',
  [int]$Wait = 75,
  [int]$Port = 8011
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
$faces = $env:RTVIS_TEST_FACES
$data = Join-Path $env:TEMP "rtvis\e2e-data"
Remove-Item $data -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory $data | Out-Null
$py = Join-Path $root '.venv\Scripts\python.exe'

Push-Location (Join-Path $root 'ai_vision')
& $py -c "import sys; sys.path[:0]=['us-02','us-05']; from reference_store import ReferenceStore; ReferenceStore(r'$data\references.npz').add('MP001','Test Person',[r'$faces\image_02.jpg'])"
Pop-Location

$env:RTVIS_DATA_DIR = $data; $env:RTVIS_CAMERA_SOURCE = Join-Path $faces $Video
$env:RTVIS_CAMERA_ID = 'TESTCAM'; $env:RTVIS_PORT = "$Port"; $env:PYTHONPATH = "$root\server;$root\ai_vision"
$log = Join-Path $env:TEMP 'rtvis\e2e-server.log'
$srv = Start-Process $py -ArgumentList (Join-Path $root 'server\run.py') -PassThru -WindowStyle Hidden -RedirectStandardError $log -RedirectStandardOutput "$log.out"
try {
  for ($i = 0; $i -lt 40; $i++) { try { Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing | Out-Null; break } catch { Start-Sleep 1 } }
  Invoke-RestMethod "http://127.0.0.1:$Port/api/auth/signup" -Method Post -ContentType application/json `
    -Body '{"name":"Operator","email":"op@example.com","password":"password123"}' | Out-Null
  Push-Location $PSScriptRoot
  if (-not (Test-Path node_modules)) { npm install --no-audit --no-fund | Out-Null }
  node ui.mjs "http://127.0.0.1:$Port" op@example.com password123 $Expect 'Test Person' $Wait
  $code = $LASTEXITCODE
  Pop-Location
  Write-Host "evidence files: $((Get-ChildItem (Join-Path $data 'evidence') -Recurse -Filter *_scene.jpg -ErrorAction SilentlyContinue | Measure-Object).Count) scene image(s)"
  exit $code
} finally {
  Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
}
