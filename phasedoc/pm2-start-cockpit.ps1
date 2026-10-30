# Starts this arc's cockpit under the PM2 service and proves it survives a service restart. Run elevated.
$ErrorActionPreference = 'Continue'
$log = "$PSScriptRoot\pm2-start-cockpit.log"
Start-Transcript -Path $log -Force | Out-Null
$env:PM2_HOME = 'C:\ProgramData\pm2\home'
$pm2 = "$env:APPDATA\npm\pm2.cmd"
& $pm2 delete phasedoc-rtvis *> $null
& $pm2 start "$PSScriptRoot\ecosystem.cockpit.config.js"
& $pm2 save
Start-Sleep 3
Write-Host "Before restart: $((Invoke-WebRequest http://127.0.0.1:6801/health -UseBasicParsing -TimeoutSec 5).Content)"
Restart-Service PM2
Start-Sleep 10
try { $c = (Invoke-WebRequest http://127.0.0.1:6801/health -UseBasicParsing -TimeoutSec 5).Content; Write-Host "After service restart: $c"; Write-Host 'RESULT PASS' }
catch { Write-Host "After service restart: FAILED $_"; Write-Host 'RESULT FAIL' }
& $pm2 ls
Stop-Transcript | Out-Null
