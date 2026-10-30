# Starts the RTVIS server under the PM2 service and proves it survives a service restart. Run elevated.
$ErrorActionPreference = 'Continue'
$log = "$PSScriptRoot\pm2-start-server.log"
Start-Transcript -Path $log -Force | Out-Null
$env:PM2_HOME = 'C:\ProgramData\pm2\home'
$pm2 = "$env:APPDATA\npm\pm2.cmd"
New-Item -ItemType Directory -Force "$PSScriptRoot\data" | Out-Null
& $pm2 delete rtvis-server *> $null
& $pm2 start "$PSScriptRoot\ecosystem.config.js"
& $pm2 save
Start-Sleep 15
Write-Host "Before restart: $((Invoke-WebRequest http://127.0.0.1:8010/health -UseBasicParsing -TimeoutSec 10).Content)"
Restart-Service PM2
Start-Sleep 25
try { $c = (Invoke-WebRequest http://127.0.0.1:8010/health -UseBasicParsing -TimeoutSec 10).Content; Write-Host "After service restart: $c"; Write-Host 'RESULT PASS' }
catch { Write-Host "After service restart: FAILED $_"; Write-Host 'RESULT FAIL' }
& $pm2 ls
Stop-Transcript | Out-Null
