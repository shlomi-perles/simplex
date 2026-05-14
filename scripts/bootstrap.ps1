#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
}

Write-Host "Syncing Python environment..."
uv sync

Write-Host ""
Write-Host "System dependencies (Windows):"
Write-Host "  winget install MiKTeX.MiKTeX"
Write-Host "  winget install Gyan.FFmpeg"
Write-Host ""
Write-Host "Verify with: uv run simplex doctor"
