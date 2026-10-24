$ErrorActionPreference = 'Stop'
$projectRoot = (Split-Path -Parent $PSScriptRoot).TrimEnd('\')
$processes = Get-CimInstance Win32_Process
$owned = @($processes | Where-Object {
    $line = $_.CommandLine
    if (!$line -or !$line.Contains($projectRoot)) { return $false }
    $ownNext = $line.Contains((Join-Path $projectRoot 'node_modules\next\dist\bin\next')) -or $line.Contains((Join-Path $projectRoot 'node_modules\next\dist\server\lib\start-server.js'))
    $ownAPI = $line.Contains('--app-dir') -and ($line.Contains('backend.main:app') -or $line.Contains('backend.portal:app')) -and $line.Contains('uvicorn')
    return $ownNext -or $ownAPI
})
foreach ($target in $owned) {
    # Verify again in case the PID has been reused since the snapshot.
    $current = Get-CimInstance Win32_Process -Filter "ProcessId=$($target.ProcessId)" -ErrorAction SilentlyContinue
    if ($current -and $current.CommandLine -eq $target.CommandLine) {
        Stop-Process -Id $target.ProcessId -ErrorAction SilentlyContinue
        Write-Output "Stopped AccessPath process $($target.ProcessId)."
    }
}
if ($owned.Count -eq 0) { Write-Output 'No verified AccessPath service processes were found. Other sessions were left running.' }
