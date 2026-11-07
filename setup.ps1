$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw 'Setup command failed. Resolve the error above and run setup again.' } }
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) { py -3.11 -m venv .venv; Check-Exit }
& ./.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
Check-Exit
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
& ./.venv/Scripts/python.exe -m app.ingestion
Check-Exit
Push-Location frontend
try { npm ci --no-audit --no-fund; Check-Exit; npm run build; Check-Exit } finally { Pop-Location }
Write-Host 'Setup complete. Add your NEW Gemini API key to .env, then run: .\run.ps1'
