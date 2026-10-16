$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "NIYAM virtual-environment Python was not found at $python"
}

$reportDir = Join-Path $PSScriptRoot 'test-reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir 'latest-test-report.txt'

function Invoke-PythonCaptured {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    $token = [guid]::NewGuid().ToString('N')
    $stdoutPath = Join-Path $env:TEMP "niyam-$token.stdout.txt"
    $stderrPath = Join-Path $env:TEMP "niyam-$token.stderr.txt"

    try {
        $process = Start-Process `
            -FilePath $python `
            -ArgumentList $Arguments `
            -WorkingDirectory $PSScriptRoot `
            -NoNewWindow `
            -Wait `
            -PassThru `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath

        $stdout = if (Test-Path -LiteralPath $stdoutPath) {
            [System.IO.File]::ReadAllText($stdoutPath)
        } else { '' }
        $stderr = if (Test-Path -LiteralPath $stderrPath) {
            [System.IO.File]::ReadAllText($stderrPath)
        } else { '' }

        return [pscustomobject]@{
            ExitCode = [int] $process.ExitCode
            StdOut = [string] $stdout
            StdErr = [string] $stderr
        }
    }
    finally {
        Remove-Item -LiteralPath $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
    }
}

@(
    'NIYAM Reliability Test Report'
    "Run time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
    "Python: $(& $python --version 2>&1)"
    'Project: NIYAM local AI assistant'
    ''
    'Compilation checks: main.py, tools.py, memory_store.py'
) | Set-Content -LiteralPath $reportPath -Encoding utf8

$compile = Invoke-PythonCaptured -Arguments @('-m', 'py_compile', 'main.py', 'tools.py', 'memory_store.py')
if ($compile.StdOut) { Add-Content -LiteralPath $reportPath -Value $compile.StdOut }
if ($compile.StdErr) { Add-Content -LiteralPath $reportPath -Value $compile.StdErr }
if ($compile.ExitCode -ne 0) {
    Add-Content -LiteralPath $reportPath -Value "Compilation: FAIL (exit $($compile.ExitCode))"
    throw "Compilation failed. See $reportPath"
}
Add-Content -LiteralPath $reportPath -Value 'Compilation: PASS'
Add-Content -LiteralPath $reportPath -Value ''
Add-Content -LiteralPath $reportPath -Value 'Automated unit tests:'

# Capture stdout and stderr to files instead of PowerShell error records;
# unittest writes verbose results to stderr on some Python/Windows combinations.
$tests = Invoke-PythonCaptured -Arguments @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v')
if ($tests.StdOut) {
    Add-Content -LiteralPath $reportPath -Value '--- stdout ---'
    Add-Content -LiteralPath $reportPath -Value $tests.StdOut
    Write-Host $tests.StdOut
}
if ($tests.StdErr) {
    Add-Content -LiteralPath $reportPath -Value '--- unittest output ---'
    Add-Content -LiteralPath $reportPath -Value $tests.StdErr
    Write-Host $tests.StdErr
}

if ($tests.ExitCode -ne 0) {
    Add-Content -LiteralPath $reportPath -Value ''
    Add-Content -LiteralPath $reportPath -Value "Result: FAIL (exit $($tests.ExitCode))"
    throw "Unit tests failed. See $reportPath"
}

Add-Content -LiteralPath $reportPath -Value ''
Add-Content -LiteralPath $reportPath -Value 'Result: PASS'
Write-Host "All compilation checks and unit tests passed. Report: $reportPath" -ForegroundColor Green
