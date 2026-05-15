# Исправление ошибки PostgreSQL в Superset Docker

## Проблема

```
ModuleNotFoundError: No module named 'psycopg2'
```

**Причина:** В стандартном Docker образе Apache Superset не установлены драйверы для подключения к PostgreSQL (psycopg2 и pg8000).

## Решение

Я создал **custom Dockerfile** который автоматически устанавливает необходимые зависимости.

### Что было сделано:

1. **Dockerfile.superset** - custom образ с установленными:
   - `psycopg2-binary` - основной драйвер PostgreSQL
   - `pg8000` - альтернативный драйвер (pure Python)

2. **docker-compose.yaml** - обновлен для использования custom образа вместо готового

3. **setup-superset.ps1** - PowerShell скрипт для автоматизации

## Как исправить (выбери 1 вариант)

### Вариант 1️⃣ - Автоматический (РЕКОМЕНДУЕТСЯ)

**Откройте PowerShell и запустите:**

```powershell
cd d:\Football_Analysis
.\setup-superset.ps1
```

Этот скрипт:
- ✅ Проверит Docker
- ✅ Удалит старые контейнеры
- ✅ Пересоберет образ с нужными драйверами
- ✅ Запустит контейнеры
- ✅ Проверит статус

### Вариант 2️⃣ - Ручной

**Откройте PowerShell:**

```powershell
# Перейти в директорию проекта
cd d:\Football_Analysis

# Удалить старые контейнеры и объемы
docker-compose down -v

# Пересоздать контейнер Superset с новыми зависимостями
docker-compose build superset

# Запустить все контейнеры
docker-compose up -d

# Подождать 30-60 секунд
Start-Sleep -Seconds 45

# Проверить статус
docker-compose ps

# Посмотреть логи Superset
docker-compose logs superset
```

### Вариант 3️⃣ - Если Вы используете WSL или Linux

```bash
cd d:/Football_Analysis
docker-compose down -v
docker-compose build superset
docker-compose up -d
sleep 45
docker-compose ps
docker-compose logs superset
```

## Проверка после запуска

### ✅ Что должно быть:

```
Container        Status
superset_app     Up (healthy)
football_db      Up (healthy)
football_redis   Up (healthy)
```

### Если Superset не стартует, проверьте логи:

```powershell
# Полные логи
docker-compose logs superset

# Последние 50 строк
docker-compose logs superset | Select-Object -Last 50

# Live логи (Ctrl+C для выхода)
docker-compose logs -f superset
```

### Типичные ошибки и решения

| Ошибка | Решение |
|--------|---------|
| `Cannot connect to database` | Подождите еще 30 секунд, PostgreSQL инициализируется |
| `Worker failed to boot` | Перестартуйте: `docker-compose restart superset` |
| `Image build failed` | Проверьте Docker: `docker --version` |

## После успешного запуска

1. **Откройте** http://localhost:8080 в браузере
2. **Логин**: admin
3. **Пароль**: admin (см. `.env`)
4. **Перезагрузите** http://localhost:3000 (Football Analysis)
5. Интерактивная аналитика должна работать! 🎉

## Дополнительно

### Посмотреть какие образы построены:
```powershell
docker images | grep -i superset
```

### Очистить всё и начать заново:
```powershell
# Удалить контейнеры, объемы И образы
docker-compose down -v
docker rmi football_analysis-superset
docker-compose up -d
```

### Посмотреть переменные окружения Superset:
```powershell
docker-compose exec superset env | grep SUPERSET
```

## Файлы конфигурации

- `Dockerfile.superset` - custom Docker образ
- `superset_config.py` - конфигурация Superset
- `docker-compose.yaml` - оркестрация контейнеров
- `.env` - переменные окружения
- `setup-superset.ps1` - автоматический скрипт

Все они уже готовы к использованию! 🚀
