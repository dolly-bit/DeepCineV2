# Start DeepCine's existing PostgreSQL container, wait until it accepts connections,
# then start the FastAPI development server.
# Run this from an activated backend virtual environment:
#   .\venv\Scripts\Activate.ps1
#   .\start.ps1

$ErrorActionPreference = "Stop"
$containerName = "deepcine-postgres"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found. Start Docker Desktop and try again."
}

$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not running. Start Docker Desktop, then run this script again."
}

$container = docker inspect $containerName 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Container '$containerName' was not found. This script will not create or replace your database."
}

$running = docker inspect --format '{{.State.Running}}' $containerName
if ($running -ne "true") {
    Write-Host "Starting existing PostgreSQL container '$containerName'..."
    docker start $containerName
    if ($LASTEXITCODE -ne 0) {
        throw "Could not start '$containerName'."
    }
} else {
    Write-Host "PostgreSQL container '$containerName' is already running."
}

Write-Host "Waiting for PostgreSQL to accept connections..."
$ready = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    docker exec $containerName pg_isready -q
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $ready) {
    throw "PostgreSQL did not become ready within 60 seconds. Check: docker logs $containerName"
}

Write-Host "PostgreSQL is ready. Starting DeepCine API..."
python -m uvicorn app.main:app --reload
