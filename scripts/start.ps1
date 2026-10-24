$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$logRoot = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$ports = @(3103, 9313, 9314)
foreach ($port in $ports) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is in use. No process was stopped. Check logs/accesspath-processes.json before starting another instance."
    }
    $probe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
    try { $probe.Start() } catch { throw "Port $port cannot be bound (it may be reserved by Windows). No services were started." } finally { $probe.Stop() }
}
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$nodePath = (Get-Command node -ErrorAction Stop).Source
$nextPath = Join-Path $projectRoot 'node_modules\next\dist\bin\next'
if (!(Test-Path -LiteralPath $pythonPath) -or !(Test-Path -LiteralPath $nextPath)) {
    throw 'Install local dependencies first. See README.md.'
}
$portal = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','backend.portal:app','--app-dir',('"' + $projectRoot + '"'),'--host','127.0.0.1','--port','9314','--no-access-log') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'portal.out.log') -RedirectStandardError (Join-Path $logRoot 'portal.err.log') -PassThru
$api = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','backend.main:app','--app-dir',('"' + $projectRoot + '"'),'--host','127.0.0.1','--port','9313','--no-access-log') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'api.out.log') -RedirectStandardError (Join-Path $logRoot 'api.err.log') -PassThru
$web = Start-Process -FilePath $nodePath -ArgumentList @(('"' + $nextPath + '"'),'dev','--hostname','127.0.0.1','--port','3103') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'web.out.log') -RedirectStandardError (Join-Path $logRoot 'web.err.log') -PassThru
@{ project=$projectRoot; portal=$portal.Id; api=$api.Id; web=$web.Id; url='http://127.0.0.1:3103' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'accesspath-processes.json')
Write-Output 'AccessPath starting at http://127.0.0.1:3103. API: 9313. Fictional portal: 9314. Other sessions were left running.'
