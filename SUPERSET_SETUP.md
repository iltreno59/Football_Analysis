# Запуск Apache Superset для Football Analysis

## Быстрый старт (Docker Compose - рекомендуется)

### Требования
- Docker установлен и запущен
- Docker Compose

### Шаги

1. **Откройте PowerShell** и перейдите в корень проекта:
```powershell
cd d:\Football_Analysis
```

2. **Запустите Docker Compose**:
```powershell
docker-compose up -d
```

3. **Проверьте статус контейнеров** (примерно через 30-60 секунд):
```powershell
docker-compose ps
```

Вы должны увидеть:
- ✅ `superset_app` - running
- ✅ `football_db` - running  
- ✅ `football_redis` - running

4. **Откройте Apache Superset** в браузере:
   - URL: http://localhost:8080
   - Username: `admin`
   - Password: `admin`

5. **Перезагрузите Football Analysis Dashboard** (http://localhost:3000)
   - Интерактивная аналитика теперь должна работать

## Остановка

```powershell
docker-compose down
```

Удалить также объемы данных:
```powershell
docker-compose down -v
```

## Что создалось

### Сервисы
- **PostgreSQL** (порт 5432) - база данных для метаданных Superset
- **Apache Superset** (порт 8080) - интерактивная аналитика
- **Redis** (порт 6379) - кэширование

### Файлы конфигурации
- `superset_config.py` - конфигурация Superset
- `docker-compose.yaml` - оркестрация контейнеров
- `.env` - переменные окружения

## Устранение неполадок

### Контейнеры не стартуют
```powershell
# Проверьте логи
docker-compose logs superset

# Перестартуйте
docker-compose restart
```

### Superset работает, но dashboard не загружается
- Убедитесь что Backend FastAPI запущен на порту 8000
- Проверьте консоль браузера (F12 → Console) на ошибки

### Очистка всех данных и пересоздание
```powershell
docker-compose down -v
docker-compose up -d
```

## Первый запуск Superset (без Docker)

Если хотите запустить локально без Docker:

```bash
# Установка
pip install apache-superset

# Инициализация БД
superset db upgrade

# Создание admin пользователя
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin

# Загрузка примеров
superset load_examples

# Запуск
superset run -p 8080 --with-threads
```

## Дополнительно

Все параметры Superset можно изменить в файле `superset_config.py`.
