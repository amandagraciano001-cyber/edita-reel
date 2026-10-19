# Instala a skill Edita reel no Claude Code e/ou no Codex, no Windows.
# Uso (no PowerShell, dentro desta pasta):
#   powershell -ExecutionPolicy Bypass -File instalar.ps1            (acha sozinho os agentes instalados)
#   powershell -ExecutionPolicy Bypass -File instalar.ps1 -Claude    (só Claude Code)
#   powershell -ExecutionPolicy Bypass -File instalar.ps1 -Codex     (só Codex)
param([switch]$Claude, [switch]$Codex)
$ErrorActionPreference = 'Stop'
$Nome = 'edita-reel'
$Aqui = $PSScriptRoot
$Casa = $env:USERPROFILE
$Alvos = @()
if ($Claude) { $Alvos += (Join-Path $Casa '.claude\skills') }
if ($Codex)  { $Alvos += (Join-Path $Casa '.agents\skills') }
if ($Alvos.Count -eq 0) {
    if ((Test-Path (Join-Path $Casa '.claude')) -or (Get-Command claude -ErrorAction SilentlyContinue)) { $Alvos += (Join-Path $Casa '.claude\skills') }
    if ((Test-Path (Join-Path $Casa '.codex')) -or (Test-Path (Join-Path $Casa '.agents')) -or (Get-Command codex -ErrorAction SilentlyContinue)) { $Alvos += (Join-Path $Casa '.agents\skills') }
}
if ($Alvos.Count -eq 0) { throw 'Não encontrei o Claude Code nem o Codex neste computador. Rode de novo com -Claude ou -Codex.' }

$Falta = $false
$Py = $null
foreach ($c in @('py', 'python')) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        $args0 = @(); if ($c -eq 'py') { $args0 = @('-3') }
        try { & $c @args0 -c 'import sys; assert sys.version_info >= (3,9)' 2>$null; $ok = ($LASTEXITCODE -eq 0) } catch { $ok = $false }
        if ($ok) { $Py = $c; $PyArgs = $args0; break }
    }
}
if (-not $Py) { Write-Host 'Falta o Python 3.9 ou mais novo. Instale com:  winget install Python.Python.3.12'; $Falta = $true }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Write-Host 'Falta o ffmpeg. Instale com:  winget install Gyan.FFmpeg'; $Falta = $true }
if ($Falta) { throw 'Instale o que falta, feche e abra o PowerShell, e rode o instalador de novo.' }

foreach ($Base in $Alvos) {
    $Destino = Join-Path $Base $Nome
    New-Item -ItemType Directory -Force -Path $Destino | Out-Null
    Get-ChildItem -Force $Destino | Where-Object { $_.Name -ne '.venv' } | Remove-Item -Recurse -Force
    Copy-Item -Recurse -Force (Join-Path (Join-Path $Aqui $Nome) '*') $Destino
    Write-Host "Copiado para $Destino"
    $VenvPy = Join-Path $Destino '.venv\Scripts\python.exe'
    if (-not (Test-Path $VenvPy)) { & $Py @PyArgs -m venv (Join-Path $Destino '.venv') }
    Write-Host 'Instalando as bibliotecas (uma vez só, pode levar alguns minutos)...'
    & $VenvPy -m pip install -q --upgrade pip
    & $VenvPy -m pip install -q -r (Join-Path $Destino 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'A instalação das bibliotecas falhou.' }
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        Write-Host '  Placa NVIDIA encontrada: a transcrição tenta usar a placa (precisa das bibliotecas CUDA 12; sem elas, roda no processador).'
    } else {
        Write-Host '  A transcrição vai rodar no processador. Se ficar lenta, use a variável EDITA_REEL_MODELO=small.'
    }
}

Write-Host ''
Write-Host 'Pronto. Abra uma sessão nova do agente e chame:'
foreach ($Base in $Alvos) {
    if ($Base -like '*\.claude\skills') { Write-Host "  Claude Code: /$Nome" } else { Write-Host "  Codex: `$$Nome" }
}
