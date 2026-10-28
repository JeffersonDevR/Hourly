# Hourly — arranque del pitch. Reemplaza al Makefile (D-015).
#
#   .\demo.ps1          API (:8000) + web (:5173)
#   .\demo.ps1 -Dev     igual, con --reload en la API
#   .\demo.ps1 -Check   arranca, verifica /api/estado y baja todo (autotest)
#
# Requiere `uv` y Node 24+. pnpm no hace falta instalarlo: si no esta en PATH
# se usa `corepack pnpm`, que viene con Node. No instala nada en el sistema.

param([switch]$Dev, [switch]$Check)

$ErrorActionPreference = 'Stop'
$root = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }

$pnpm = if (Get-Command pnpm -ErrorAction SilentlyContinue) { 'pnpm' } else { 'corepack pnpm' }

$apiCmd = 'uv run --directory api uvicorn app.main:app --host 127.0.0.1 --port 8000'
if ($Dev) { $apiCmd += ' --reload' }
$webCmd = "$pnpm --dir web dev"

$children = @()

# cmd /c envuelve a cada hijo y taskkill /T mata el arbol completo.
# Sin esto, matar el wrapper de uv deja a Python escuchando en el puerto.
function Stop-Children {
    foreach ($p in $children) {
        if ($p -and -not $p.HasExited) {
            & taskkill /PID $p.Id /T /F 2>&1 | Out-Null
        }
    }
}

try {
    $children += Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $apiCmd `
        -WorkingDirectory $root -PassThru -NoNewWindow
    $children += Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $webCmd `
        -WorkingDirectory $root -PassThru -NoNewWindow

    $estado = $null
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $estado = Invoke-RestMethod 'http://127.0.0.1:8000/api/estado' -TimeoutSec 2
            break
        }
        catch { }
    }

    if ($null -eq $estado) {
        Write-Host 'La API no respondio en 20 s. Revisa la salida de arriba.' -ForegroundColor Red
        exit 1
    }

    Write-Host "API OK  ok=$($estado.ok)  ai_disponible=$($estado.ai_disponible)" -ForegroundColor Green
    Write-Host 'Web     http://127.0.0.1:5173   (Ctrl+C baja los dos)' -ForegroundColor Green

    if ($Check) { Write-Host 'Autotest OK.' -ForegroundColor Green; exit 0 }

    while ($true) { Start-Sleep -Seconds 1 }
}
finally {
    Stop-Children
}
