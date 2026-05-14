# Football Analysis - Frontend

React приложение для анализа ролей футболистов с интегрированным Apache Superset.

## 🚀 Структура проекта

```
frontend/
├── public/              # Статические файлы
│   └── index.html
├── src/
│   ├── components/      # Переиспользуемые компоненты
│   │   └── SupersetEmbed.js
│   ├── pages/           # Страницы приложения
│   │   ├── Dashboard.js
│   │   ├── PlayerAnalysis.js
│   │   └── Reports.js
│   ├── App.js           # Основной компонент с роутингом
│   ├── App.css
│   ├── index.js
│   └── index.css
├── package.json
└── .env                 # Переменные окружения
```

## 📋 Этапы разработки

### ✅ Этап 1: Базовая структура (текущий)
- [x] Создана структура React проекта
- [x] Установлены зависимости (package.json)
- [x] Реализована основная навигация (AppBar + Router)
- [x] Создана страница Dashboard с основной информацией
- [x] Подготовлена интеграция с Superset (компонент SupersetEmbed)
- [x] Создана страница PlayerAnalysis для поиска и анализа игроков
- [x] Создана страница Reports для просмотра отчётов

### 📍 Этап 2: API интеграция (следующий)
- [ ] Создать API endpoints на backend для:
  - `/api/stats` - общая статистика
  - `/api/players/search` - поиск игроков
  - `/api/players/{id}/recommendations` - рекомендации упражнений
  - `/api/reports` - список отчётов
  - `/api/superset-token` - токен для Superset

### 🎨 Этап 3: Улучшение UI/UX
- [ ] Добавить more detailed player profiles
- [ ] Реализовать фильтры и сортировку
- [ ] Добавить графики и визуализацию данных
- [ ] Стилизировать компоненты

### 📊 Этап 4: Superset интеграция
- [ ] Настроить Apache Superset
- [ ] Создать dashboards в Superset
- [ ] Обновить SupersetEmbed с реальными dashboard IDs
- [ ] Добавить интерактивные фильтры

## 🛠️ Установка и запуск

```bash
# Установка зависимостей
npm install

# Запуск в режиме разработки
npm start

# Сборка для продакшена
npm build
```

Приложение откроется на `http://localhost:3000`

## 🔗 Зависимости

- **react**: 18.2.0 - UI библиотека
- **react-router-dom**: 6.8.0 - Роутинг
- **@mui/material**: 5.11.0 - UI компоненты
- **superset-ui-embedded-sdk**: 1.3.0 - Встраивание Superset
- **axios**: 1.3.0 - HTTP клиент

## 🔐 Переменные окружения (.env)

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_SUPERSET_URL=http://localhost:8088
REACT_APP_SUPERSET_DASHBOARD_ID=1
```

## 📌 Текущее состояние

**Завершено:**
- ✅ Базовая навигация и маршрутизация
- ✅ Страница Dashboard с статистикой
- ✅ Страница PlayerAnalysis с поиском (макет)
- ✅ Страница Reports с таблицей отчётов (макет)
- ✅ Компонент для встраивания Superset

**TODO:**
- Подключить реальные API endpoints
- Настроить Superset
- Добавить аутентификацию
- Улучшить дизайн и UX

## 📝 Примечания

- Компоненты используют Material-UI (MUI) для стилизации
- Все API endpoints имеют TODO комментарии - нужно заменить на реальные URLs
- SupersetEmbed требует корректной конфигурации Superset на backend
