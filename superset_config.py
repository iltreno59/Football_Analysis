import os
from datetime import timedelta

# Ключ безопасности для Superset
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "hQgaMf0c9vxswAVGCX0RLoFHSVngTD7i8TJOML3TDotKP0GfJ0LYNgkx")

# Настройки базы данных метаданных Superset
# При использовании docker-compose, db - это имя сервиса PostgreSQL
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    "postgresql://postgres:football_analysis_2024@db:5432/superset_metadata"
)

# Роль по умолчанию для неавторизованных пользователей
AUTH_ROLE_ADMIN = "Admin"
AUTH_ROLE_PUBLIC = "Public"

# Включаем возможность встраивания (Embedded SDK)
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "ALLOW_ADHOC_SUBQUERY": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "VERSIONED_EXPORT": True,
}

# Включаем CORS для фронтенда
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': [
        'http://localhost:3000',
        'http://localhost:8000',
        'http://localhost:8080',
    ]
}

# Разрешаем встраивание в iframe
HTTP_HEADERS = {
    'X-Frame-Options': 'ALLOWALL',
    'X-Content-Type-Options': 'nosniff',
}

# Content Security Policy для встраивания
TALISMAN_CONFIG = {
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'", "http://localhost:3000"],
        "frame-ancestors": ["'self'", "http://localhost:3000", "http://localhost:8000"],
        "object-src": ["'none'"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "http://localhost:3000"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https:"],
        "font-src": ["'self'", "data:"],
    },
    "force_https": False,
    "strict_transport_security": False,
}

# Конфиг для Guest Token (встраивания)
GUEST_TOKEN_JWT_SECRET = os.getenv("GUEST_TOKEN_JWT_SECRET", "test-guest-token-secret-key-123")
GUEST_ROLE_NAME = "Public"

# Время жизни guest token (1 час)
GUEST_TOKEN_JWT_ALGORITHM = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 3600

# WTForms конфиг
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Кэширование
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
}

# Дополнительные настройки
ROW_LIMIT = 10000
SUPERSET_WORKERS = 4
SUPERSET_WEBSERVER_PORT = 8088

# Для развития
FLASK_ENV = "production"
DEBUG = False

# Таймауты
SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = 10
SQLLAB_ASYNC_TIME_LIMIT_SEC = 600
