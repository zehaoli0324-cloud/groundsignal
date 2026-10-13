param([string[]]$Companies)
$env:PYTHONIOENCODING = 'utf-8'
if (-not $Companies) {
    $companyName = Read-Host 'Company name'
    if ([string]::IsNullOrWhiteSpace($companyName)) { exit 1 }
    $Companies = @($companyName)
}
& python (Join-Path $PSScriptRoot 'scripts/collect.py') @Companies
exit $LASTEXITCODE
