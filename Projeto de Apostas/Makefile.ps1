# VBQ-UNIFIED — Windows PowerShell Makefile equivalent
# Usage: .\Makefile.ps1 <command>
# Or:    powershell -File .\Makefile.ps1 <command>

param(
    [Parameter(Position=0)]
    [ValidateSet("setup","test","train","clv","backtest","live","daily","doctor","clean")]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "VBQ-UNIFIED Commands:" -ForegroundColor Cyan
    Write-Host "  setup    - Install dependencies (uv/pip)"
    Write-Host "  test     - Run full test suite"
    Write-Host "  train    - Train football model (mock)"
    Write-Host "  clv      - Generate CLV report"
    Write-Host "  backtest - Run walk-forward backtest"
    Write-Host "  live     - Run live pipeline (paper)"
    Write-Host "  daily    - Run daily report"
    Write-Host "  doctor   - System health check"
    Write-Host "  clean    - Clean caches and temp files"
}

function Invoke-Setup {
    Write-Host "[setup] Checking Python..." -ForegroundColor Green
    python --version
    Write-Host "[setup] Installing uv..." -ForegroundColor Green
    pip install uv -q
    Write-Host "[setup] Installing dependencies..." -ForegroundColor Green
    uv pip install -e . || pip install -e .
    Write-Host "[setup] Done." -ForegroundColor Green
}

function Invoke-Test {
    Write-Host "[test] Running pytest..." -ForegroundColor Green
    python -m pytest tests/ -q --tb=short
}

function Invoke-Train {
    Write-Host "[train] Training football model..." -ForegroundColor Green
    python scripts/train_bot.py football --source mock --walk-forward
}

function Invoke-Clv {
    Write-Host "[clv] Generating CLV report..." -ForegroundColor Green
    python scripts/run_clv_report.py
}

function Invoke-Backtest {
    Write-Host "[backtest] Running walk-forward backtest..." -ForegroundColor Green
    python scripts/backtest_season.py --sport football --season 2024 --check-leakage --compare-tier-b
}

function Invoke-Live {
    Write-Host "[live] Running live pipeline (paper mode)..." -ForegroundColor Green
    python scripts/run_pipeline.py --sport football --mode live
}

function Invoke-Daily {
    Write-Host "[daily] Generating daily report..." -ForegroundColor Green
    python scripts/daily_report.py
}

function Invoke-Doctor {
    Write-Host "[doctor] Running health check..." -ForegroundColor Green
    python scripts/vbq_doctor.py --verbose
}

function Invoke-Clean {
    Write-Host "[clean] Removing caches..." -ForegroundColor Green
    Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
    Write-Host "[clean] Done." -ForegroundColor Green
}

switch ($Command) {
    "setup"    { Invoke-Setup }
    "test"     { Invoke-Test }
    "train"    { Invoke-Train }
    "clv"      { Invoke-Clv }
    "backtest" { Invoke-Backtest }
    "live"     { Invoke-Live }
    "daily"    { Invoke-Daily }
    "doctor"   { Invoke-Doctor }
    "clean"    { Invoke-Clean }
    default    { Show-Help }
}
