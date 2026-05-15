#!/usr/bin/env powershell
# Скрипт для проверки статуса Superset

Write-Host "🔍 Проверка статуса Football Analysis Docker контейнеров" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
$dockerCheck = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker не запущен или не установлен!" -ForegroundColor Red
    exit 1
}

cd d:\Football_Analysis

# Статус контейнеров
Write-Host "📊 Статус контейнеров:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "📋 Логи Superset (последние 30 строк):" -ForegroundColor Yellow
docker-compose logs superset | Select-Object -Last 30

Write-Host ""
Write-Host "🌐 Проверка доступности:" -ForegroundColor Yellow

# Проверка Superset
$supersetCheck = curl.exe -s -o /dev/null -w "%{http_code}" http://localhost:8080 -m 2
if ($supersetCheck -eq "200" -or $supersetCheck -eq "302") {
    Write-Host "✅ Superset доступен: http://localhost:8080 (HTTP $supersetCheck)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Superset: HTTP $supersetCheck (может инициализироваться)" -ForegroundColor Yellow
}

# Проверка Backend
$backendCheck = curl.exe -s -o /dev/null -w "%{http_code}" http://localhost:8000/health -m 2
if ($backendCheck -eq "200") {
    Write-Host "✅ Backend доступен: http://localhost:8000/health (HTTP $backendCheck)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Backend: HTTP $backendCheck (убедитесь что uvicorn запущен)" -ForegroundColor Yellow
}

# Проверка Frontend
$frontendCheck = curl.exe -s -o /dev/null -w "%{http_code}" http://localhost:3000 -m 2
if ($frontendCheck -eq "200" -or $frontendCheck -eq "304") {
    Write-Host "✅ Frontend доступен: http://localhost:3000 (HTTP $frontendCheck)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend: HTTP $frontendCheck (убедитесь что npm start запущен)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "💾 Использование памяти:" -ForegroundColor Yellow
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}" | grep -E "football_|superset"

Write-Host ""
Write-Host "✨ Все готово!" -ForegroundColor Cyan
