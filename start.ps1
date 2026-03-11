# FinVox - Start all services
param([switch]$Agent, [switch]$WA, [switch]$All)

$workspace = "C:\Users\AI\.openclaw\workspace\finvox"

function Stop-Port($port) {
  $p = Get-NetTCPConnection -LocalPort $port -State Listen -EA SilentlyContinue | Select-Object -First 1
  if ($p) { Stop-Process -Id $p.OwningProcess -Force -EA SilentlyContinue; Start-Sleep 1 }
}

function Start-Agent {
  Write-Host "[FinVox] Starting voice agent on port 8086..."
  Stop-Port 8086
  Start-Process powershell -ArgumentList "-Command", @"
    cd $workspace\agent
    Get-Content .env | ForEach-Object { if (`$_ -match '^([^#].+?)=(.+)$') { [System.Environment]::SetEnvironmentVariable(`$Matches[1], `$Matches[2]) } }
    `$env:PYTHONIOENCODING='utf-8'
    .\.venv\Scripts\python.exe agent.py start > logs\agent.log 2>&1
"@ -WindowStyle Hidden
  Start-Sleep 3
  $c = Get-NetTCPConnection -LocalPort 8086 -State Listen -EA SilentlyContinue
  if ($c) { Write-Host "[FinVox] Agent UP on port 8086" -ForegroundColor Green }
  else { Write-Host "[FinVox] Agent starting (check logs/agent.log)" -ForegroundColor Yellow }
}

function Start-WA {
  Write-Host "[FinVox] Starting WhatsApp companion on port 8087..."
  Stop-Port 8087
  if (!(Test-Path "$workspace\wa-companion\node_modules")) {
    Write-Host "Installing WA companion dependencies..."
    cd "$workspace\wa-companion"; npm install --silent
  }
  Start-Process powershell -ArgumentList "-Command", @"
    cd $workspace\wa-companion
    node server.mjs > logs\wa.log 2>&1
"@ -WindowStyle Hidden
  Start-Sleep 2
  Write-Host "[FinVox] WA Companion started (check logs/wa.log)" -ForegroundColor Green
}

# Create log dirs
mkdir -Force "$workspace\agent\logs" | Out-Null
mkdir -Force "$workspace\wa-companion\logs" | Out-Null

if ($All -or (!$Agent -and !$WA)) {
  Start-Agent
  Start-WA
} elseif ($Agent) {
  Start-Agent
} elseif ($WA) {
  Start-WA
}

Write-Host ""
Write-Host "FinVox Services:" -ForegroundColor Cyan
Write-Host "  Voice Agent:    http://localhost:8086/health"
Write-Host "  WA Companion:   http://localhost:8087/health"
Write-Host "  Dashboard:      https://finvox-app.vercel.app"
