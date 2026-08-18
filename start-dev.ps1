<#
  Khoi dong moi truong phat trien: Database + Backend (Docker) va Frontend (Vite dev server),
  sau do tu dong mo trinh duyet toi trang frontend.

  Cach dung:
    powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
  hoac don gian hon, double-click file start-dev.bat di kem.
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$backendUrl = "http://localhost:8000/docs"

function Wait-ForUrl {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 90
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) { return $true }
        } catch {
            # chua san sang, thu lai
        }
        Start-Sleep -Seconds 2
    }
    return $false
}

Write-Host "==> Khoi dong Database + Backend qua Docker Compose..." -ForegroundColor Cyan
Push-Location $root
try {
    docker compose up -d --build db backend
} finally {
    Pop-Location
}

Write-Host "==> Cho backend san sang tai $backendUrl ..." -ForegroundColor Cyan
if (-not (Wait-ForUrl -Url $backendUrl -TimeoutSeconds 90)) {
    Write-Warning "Backend chua phan hoi sau 90s. Kiem tra log bang: docker compose logs -f backend"
} else {
    Write-Host "==> Backend da san sang." -ForegroundColor Green
}

# Vite co the doi sang port khac (vd 5174) neu 5173 dang ban, nen ta doc log
# de lay dung URL thay vi doan cung port.
$frontendDir = Join-Path $root "frontend_react"
$logFile = Join-Path $env:TEMP "cataloging-frontend-dev.log"
if (Test-Path $logFile) { Remove-Item $logFile -Force }

Write-Host "==> Khoi dong Frontend (Vite dev server) trong cua so moi..." -ForegroundColor Cyan
# NO_COLOR de tat ma mau ANSI, giup doc log chinh xac dia chi may chu.
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location `"$frontendDir`"; `$env:NO_COLOR = '1'; npm run dev 2>&1 | Tee-Object -FilePath `"$logFile`""
)

Write-Host "==> Cho Vite khoi dong va xac dinh dia chi thuc te..." -ForegroundColor Cyan
$frontendUrl = $null
$deadline = (Get-Date).AddSeconds(60)
$ansiPattern = [char]27 + '\[[0-9;]*m'
while ((Get-Date) -lt $deadline -and -not $frontendUrl) {
    if (Test-Path $logFile) {
        $content = (Get-Content -Path $logFile -Raw -ErrorAction SilentlyContinue) -replace $ansiPattern, ''
        if ($content) {
            $matches2 = [regex]::Matches($content, "Local:\s+(http://localhost:\d+/?)")
            if ($matches2.Count -gt 0) {
                $frontendUrl = $matches2[$matches2.Count - 1].Groups[1].Value
            }
        }
    }
    if (-not $frontendUrl) { Start-Sleep -Seconds 1 }
}

if (-not $frontendUrl) {
    Write-Warning "Khong doc duoc URL cua Vite sau 60s, dung mac dinh http://localhost:5173/"
    Write-Warning "Kiem tra cua so PowerShell vua mo de xem log chi tiet."
    $frontendUrl = "http://localhost:5173/"
}

Write-Host "==> Mo trinh duyet toi $frontendUrl" -ForegroundColor Cyan
Start-Process $frontendUrl

Write-Host ""
Write-Host "Hoan tat. Backend: $backendUrl | Frontend: $frontendUrl" -ForegroundColor Green
Write-Host "Dung backend + database bang: docker compose down" -ForegroundColor DarkGray
