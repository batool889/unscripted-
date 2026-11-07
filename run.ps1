$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) { throw 'Run setup.ps1 first.' }
if (-not (Test-Path -LiteralPath 'frontend/dist/index.html')) { throw 'Build the website first: cd frontend; npm run build' }
if (-not (Test-Path -LiteralPath 'data/indexes/active.json')) { throw 'Run .\.venv\Scripts\python.exe -m app.ingestion first.' }
Write-Host 'Open http://127.0.0.1:8000 . Press Ctrl+C to stop.'
& ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
