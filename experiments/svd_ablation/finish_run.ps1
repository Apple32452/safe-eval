param(
    [Parameter(Mandatory=$true)][int]$RunnerId,
    [Parameter(Mandatory=$true)][string]$PythonExe
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $repoRoot
$repoSafe = $repoRoot.Replace('\','/')
$outputDir = Join-Path $PSScriptRoot 'results_pruned_final'
$logDir = Join-Path $repoRoot 'results/svd_ablation_background'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$statusPath = Join-Path $logDir 'status.json'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'

function Save-Status([string]$State, [string]$Detail) {
    @{status=$State; detail=$Detail; utc=[DateTime]::UtcNow.ToString('o')} |
        ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
}

Start-Transcript -LiteralPath (Join-Path $logDir 'finish.log') -Append | Out-Null
try {
    Save-Status 'waiting_for_experiment' "Watching runner $RunnerId"
    while ($true) {
        $metadata = $null
        try {
            $metadata = Get-Content -LiteralPath (Join-Path $outputDir 'run_metadata.json') -Raw |
                ConvertFrom-Json
        } catch {
            # The runner updates this file after each completed case.
        }
        if ($metadata -and $metadata.status -eq 'complete') { break }
        if ($metadata -and $metadata.status -in @('failed','interrupted')) {
            throw "Experiment ended with status $($metadata.status): $($metadata.error)"
        }
        if (-not (Get-Process -Id $RunnerId -ErrorAction SilentlyContinue)) {
            throw 'Runner exited without complete metadata; preserve outputs for inspection.'
        }
        if ($metadata) {
            Save-Status 'running' "$($metadata.completed_cases)/117 cases complete"
        }
        Start-Sleep -Seconds 5
    }

    Save-Status 'auditing' 'Generating findings and verifying dense/pruned parity'
    & $PythonExe experiments/svd_ablation/report.py --input experiments/svd_ablation/results_pruned_final --output experiments/svd_ablation/results_pruned_final/FINDINGS.md
    if ($LASTEXITCODE -ne 0) { throw 'Independent report audit failed' }

    $parityCode = @'
import csv, hashlib, json
from pathlib import Path
import numpy as np
root = Path('experiments/svd_ablation')
out = root / 'results_pruned_final'
def read(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))
def key(row):
    return row['case_id'], row['arm'], int(row['repeat'])
old = {key(r): r for r in read(root / 'results_reference/per_trial.csv')}
new = {key(r): r for r in read(out / 'per_trial.csv')}
assert len(old) == len(new) == 23400 and old.keys() == new.keys()
fields = ('mean_queries', 'mse', 'mae', 'residual_mean', 'residual_variance', 'simultaneous_coverage', 'stopped_absolute_error')
maximum = {field: 0.0 for field in fields}
for identity, row in new.items():
    for field in ('scenario', 'language_pair', 'target_system', 'n'):
        assert row[field] == old[identity][field]
    for field in fields:
        a, b = float(row[field]), float(old[identity][field])
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-12)
        maximum[field] = max(maximum[field], abs(a-b))
meta = json.loads((out / 'run_metadata.json').read_text())
assert meta['status'] == 'complete' and meta['completed_cases'] == 117
for relative, expected in meta['source_sha256'].items():
    assert hashlib.sha256((root.parent / relative).read_bytes()).hexdigest() == expected
assert hashlib.sha256((root / 'PROTOCOL.md').read_bytes()).hexdigest() == meta['protocol_sha256']
result = dict(status='passed', records_compared=23400, maximum_absolute_difference=maximum, frozen_sources_verified=True, protocol_verified=True)
(out / 'PARITY_WITH_DENSE.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
'@
    & $PythonExe -c $parityCode
    if ($LASTEXITCODE -ne 0) { throw 'Dense/pruned parity or frozen-source verification failed' }

    $branch = & git -c "safe.directory=$repoSafe" branch --show-current
    if ($LASTEXITCODE -ne 0 -or $branch -ne 'experiment/svd-ablation') {
        throw 'Branch changed; automatic commit cancelled'
    }
    $mainHead = & git -c "safe.directory=$repoSafe" rev-parse main
    if ($LASTEXITCODE -ne 0 -or $mainHead -ne '50a64e42e580ef548bfe92e3596298a2d255605b') {
        throw 'Main differs from the original base; inspect before committing'
    }
    $staged = @(& git -c "safe.directory=$repoSafe" diff --cached --name-only)
    foreach ($path in $staged) {
        if ($path -and -not $path.StartsWith('experiments/svd_ablation/results_pruned_final/') -and
            $path -ne 'experiments/svd_ablation/finish_run.ps1') {
            throw 'Other staged work exists; automatic commit cancelled'
        }
    }
    & git -c "safe.directory=$repoSafe" add -- experiments/svd_ablation/results_pruned_final experiments/svd_ablation/finish_run.ps1
    if ($LASTEXITCODE -ne 0) { throw 'Could not stage verified results' }
    & git -c "safe.directory=$repoSafe" commit -m 'Record verified pruned SVD ablation results and dense-run parity'
    if ($LASTEXITCODE -ne 0) { throw 'Could not commit verified results' }
    $commit = & git -c "safe.directory=$repoSafe" rev-parse HEAD
    Save-Status 'complete' "Verified 117 cases and 23400 records; committed $commit"
} catch {
    Save-Status 'failed' $_.Exception.Message
    Write-Output $_.Exception.ToString()
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
