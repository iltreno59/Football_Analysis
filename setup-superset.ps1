#!/usr/bin/env powershell
# Скрипт для пересоздания Superset контейнеров с необходимыми драйверами

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Football Analysis - Superset Docker Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "1️⃣  Проверка Docker..." -ForegroundColor Yellow
$dockerCheck = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker не установлен!" -ForegroundColor Red
    Write-Host "Установите Docker Desktop с https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker найден: $dockerCheck" -ForegroundColor Green

# Переход в директорию проекта
Write-Host ""
Write-Host "2️⃣  Переход в директорию проекта..." -ForegroundColor Yellow
cd d:\Football_Analysis
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Не удалось перейти в d:\Football_Analysis" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Находимся в: $(Get-Location)" -ForegroundColor Green

# Остановка и удаление старых контейнеров
Write-Host ""
Write-Host "3️⃣  Удаление старых контейнеров и объемов..." -ForegroundColor Yellow
docker-compose down -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Нет старых контейнеров (это нормально)" -ForegroundColor Yellow
}
Write-Host "✅ Старые контейнеры удалены" -ForegroundColor Green

# Пересборка Superset образа
Write-Host ""
Write-Host "4️⃣  Сборка Superset контейнера с драйверами PostgreSQL..." -ForegroundColor Yellow
Write-Host "Это может занять 2-5 минут..." -ForegroundColor Gray
docker-compose build superset
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке контейнера" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Контейнер собран" -ForegroundColor Green

# Запуск контейнеров
Write-Host ""
Write-Host "5️⃣  Запуск контейнеров..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при запуске контейнеров" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Контейнеры запущены" -ForegroundColor Green

# Ожидание инициализации
Write-Host ""
Write-Host "6️⃣  Ожидание инициализации Superset (это займет 30-60 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Мониторинг логов
Write-Host ""
Write-Host "📊 Проверка статуса контейнеров:" -ForegroundColor Cyan
docker-compose ps

# Проверка логов Superset
Write-Host ""
Write-Host "📋 Последние логи Superset:" -ForegroundColor Cyan
docker-compose logs superset | Select-Object -Last 20

# Финальная проверка
Write-Host ""
Write-Host "⏳ Финальная проверка (ждем 10 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "✨ Проверка доступности:" -ForegroundColor Cyan
$response = curl.exe -s -o /dev/null -w "%{http_code}" http://localhost:8080/health -m 5
if ($response -eq "200") {
    Write-Host "✅ Superset готов! (HTTP $response)" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Superset доступен: http://localhost:8080" -ForegroundColor Green
    Write-Host "👤 Username: admin" -ForegroundColor Green
    Write-Host "🔑 Password: admin" -ForegroundColor Green
} else {
    Write-Host "⏳ Superset еще инициализируется (HTTP $response)" -ForegroundColor Yellow
    Write-Host "Подождите еще 30-60 секунд и перезагрузите http://localhost:8080" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Готово! Перезагрузите Football Analysis" -ForegroundColor Cyan
Write-Host "   http://localhost:3000" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
