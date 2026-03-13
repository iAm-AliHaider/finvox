# Load .env and start agent
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}
$env:PYTHONIOENCODING = "utf-8"
Set-Location $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\python.exe" agent.py start
