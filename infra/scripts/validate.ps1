[CmdletBinding()]
param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [switch]$SkipMigration
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$ApiRoot = Join-Path $RepositoryRoot "services/api"
$Python = Join-Path $RepositoryRoot ".venv/Scripts/python.exe"
$Results = [System.Collections.Generic.List[object]]::new()

function Invoke-ValidationCheck([string]$Name, [scriptblock]$Action) {
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) {
            throw "command exited with code $LASTEXITCODE"
        }
        $Results.Add([pscustomobject]@{ Name = $Name; Status = "PASS" })
        Write-Host "[PASS] $Name" -ForegroundColor Green
    }
    catch {
        $Results.Add([pscustomobject]@{ Name = $Name; Status = "FAIL" })
        Write-Host "[FAIL] $Name - $($_.Exception.Message)" -ForegroundColor Red
    }
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Project Python environment not found: $Python"
}
if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    $DatabaseUrl = "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot"
}
$env:DATABASE_URL = $DatabaseUrl
$env:TEST_DATABASE_URL = $DatabaseUrl

Invoke-ValidationCheck "Python environment" { & $Python --version }
Invoke-ValidationCheck "PostgreSQL connectivity" {
    & $Python -c "import os; from sqlalchemy import create_engine, text; e=create_engine(os.environ['DATABASE_URL']); c=e.connect(); c.execute(text('SELECT 1')); c.close()"
}

if (-not $SkipMigration) {
    Invoke-ValidationCheck "Alembic upgrade head" {
        Push-Location $ApiRoot
        try { & $Python -m alembic upgrade head } finally { Pop-Location }
    }
}

Invoke-ValidationCheck "Alembic current matches dynamic head" {
    Push-Location $ApiRoot
    try {
        $headsOutput = (& $Python -m alembic heads)
        $currentOutput = (& $Python -m alembic current)
        $heads = @($headsOutput | ForEach-Object { if ($_ -match '^\s*(\S+)\s+\(head\)') { $Matches[1] } })
        $current = @($currentOutput | ForEach-Object { if ($_ -match '^\s*(\S+)\s+\(head\)') { $Matches[1] } })
        if ($heads.Count -ne 1 -or $current.Count -ne 1 -or $current[0] -ne $heads[0]) {
            throw "current=$($current -join ','); head=$($heads -join ',')"
        }
    } finally { Pop-Location }
}

Invoke-ValidationCheck "Phase 3.4-005 market-data boundary" {
    & $Python -c "import os; from sqlalchemy import create_engine, inspect; t=set(inspect(create_engine(os.environ['DATABASE_URL'])).get_table_names(schema='topicpilot')); assert {'market_data_sources','raw_market_observations'} <= t, t; assert not ({'normalized_market_observations','market_snapshots'} & t), t"
}

Invoke-ValidationCheck "Pytest migration, foundation, and domain discovery" {
    Push-Location $ApiRoot
    try {
        $env:PYTHONPATH = $RepositoryRoot
        $testFiles = @(
            Get-ChildItem (Join-Path $ApiRoot "tests") -File |
                Where-Object { $_.Name -eq "test_database_foundation.py" -or $_.Name -eq "test_market_data_models.py" -or $_.Name -eq "test_canonical_observation_postgres.py" -or $_.Name -match "^test_.+_(migration|domain|relationships)\.py$" } |
                Sort-Object Name |
                Select-Object -ExpandProperty FullName
        )
        if ($testFiles.Count -eq 0) { throw "No migration, foundation, domain, or relationship tests discovered" }
        & $Python -m pytest $testFiles -q
    } finally { Pop-Location }
}

Write-Host "`nTopicPilot validation summary" -ForegroundColor Cyan
$Results | Format-Table -AutoSize
$failed = @($Results | Where-Object Status -eq "FAIL").Count
if ($failed -gt 0) {
    Write-Host "NOT READY ($failed check(s) failed)" -ForegroundColor Red
    exit 1
}
Write-Host "READY" -ForegroundColor Green
exit 0
