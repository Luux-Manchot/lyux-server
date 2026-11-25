param(
    [string]$SshUser = "lyux-admin",
    [string]$SshHost = "127.0.0.1",
    [int]$SshPort = 2222,
    [string]$RemoteDir = "/opt/lyux"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "Synchronisation vers ${SshUser}@${SshHost}:${SshPort}:${RemoteDir} ..."

scp -P $SshPort -r "$RepoRoot\lyux-server-api" "${SshUser}@${SshHost}:${RemoteDir}/"
scp -P $SshPort -r "$RepoRoot\apps\admin-ui" "${SshUser}@${SshHost}:${RemoteDir}/apps/"
scp -P $SshPort "$RepoRoot\lyux-server-infra\docker-compose.yml" "${SshUser}@${SshHost}:${RemoteDir}/lyux-server-infra/docker-compose.yml"

Write-Host "Reconstruction et demarrage de lyux-api et lyux-admin-ui (lyux-hub conserve en parallele)..."
ssh -p $SshPort "${SshUser}@${SshHost}" "cd ${RemoteDir}/lyux-server-infra && docker compose up -d --build lyux-api lyux-admin-ui && docker compose ps lyux-api lyux-hub lyux-admin-ui"

Write-Host ""
Write-Host "Termine :"
Write-Host "  - Ancien panneau (Hub)   : http://localhost:8086 (ou http://hub.lyux.lan)"
Write-Host "  - Nouvelle interface     : http://localhost:8087 (ou http://admin.lyux.lan)"
Write-Host "  - API LyuX               : http://localhost:8000"
