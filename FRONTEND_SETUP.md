# 📱 Frontend React + Superset - Этап 1

## ✅ Что сделано на этом этапе

### 1️⃣ Базовая структура React проекта
- ✅ Создана папка `frontend/` с полной структурой проекта
- ✅ Настроены зависимости (package.json)
- ✅ Созданы основные файлы (index.html, App.js, etc.)

### 2️⃣ Главная навигация
```
AppBar с меню:
  - Dashboard (главная страница)
  - Players (анализ игроков)
  - Reports (отчёты)
```

### 3️⃣ Страницы приложения

#### 📊 Dashboard (`/`)
- Статистика (Всего игроков, Ролей, Отчётов)
- Информация о системе анализа
- Встроенный Superset Dashboard (компонент SupersetEmbed)

#### 🔍 Players (`/players`)
- Поиск игрока по имени
- Отображение информации об игроке
- Кнопка "Получить рекомендации упражнений"
- Таблица дефицитных метрик
- Список рекомендуемых упражнений

#### 📋 Reports (`/reports`)
- Таблица всех созданных отчётов
- Просмотр деталей отчёта в диалоговом окне
- Информация об упражнениях в отчёте

### 4️⃣ Компоненты

#### SupersetEmbed.js
```javascript
// Встраивание Apache Superset Dashboard
- Загрузка гостевого токена с backend
- Обработка ошибок загрузки
- Поддержка динамического выбора dashboard ID
```

### 5️⃣ Backend API endpoints

Добавлены новые endpoints для фронтенда:
```
GET /api/stats                          → Основная статистика
GET /api/players/search?name=...        → Поиск игрока
GET /api/players/{id}/recommendations   → Рекомендации упражнений
GET /api/reports                        → Список отчётов
GET /api/reports/{id}                   → Детали отчёта
POST /api/superset-token                → Токен для Superset
```

## 🚀 Как запустить

### 1. Установка зависимостей frontend

```bash
cd d:\Football_Analysis\frontend
npm install
```

### 2. Запуск frontend в режиме разработки

```bash
npm start
```

Приложение откроется на `http://localhost:3000`

### 3. Убедитесь, что backend запущен

```bash
cd d:\Football_Analysis
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 Следующие этапы разработки

### 📍 Этап 2: API интеграция и Superset
- [ ] Протестировать все endpoints
- [ ] Настроить Apache Superset на http://localhost:8088
- [ ] Создать dashboard в Superset
- [ ] Получить реальный гостевой токен от Superset
- [ ] Полностью настроить SupersetEmbed компонент

### 🎨 Этап 3: UI/UX улучшения
- [ ] Добавить Loading states
- [ ] Добавить Error boundaries
- [ ] Улучшить дизайн таблиц
- [ ] Добавить фильтры и сортировку
- [ ] Реализовать pagination

### 🔐 Этап 4: Аутентификация
- [ ] Добавить страницу логина
- [ ] JWT токены
- [ ] Protected routes
- [ ] Проверка прав доступа

### 📊 Этап 5: Дополнительные функции
- [ ] Выгрузка отчётов в PDF
- [ ] Сравнение игроков
- [ ] История анализа
- [ ] Уведомления

## 📁 Структура папок

```
frontend/
├── public/
│   └── index.html           # Главный HTML
├── src/
│   ├── components/
│   │   └── SupersetEmbed.js # Компонент встраивания Superset
│   ├── pages/
│   │   ├── Dashboard.js     # Главная страница
│   │   ├── PlayerAnalysis.js# Анализ игроков
│   │   └── Reports.js       # Отчёты
│   ├── App.js              # Главный компонент
│   ├── App.css
│   ├── index.js
│   └── index.css
├── .env                     # Переменные окружения
├── .gitignore
├── package.json
└── README.md
```

## 🔧 Переменные окружения

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_SUPERSET_URL=http://localhost:8088
REACT_APP_SUPERSET_DASHBOARD_ID=1
```

### Backend (.env)
```
DB_USER=postgres
DB_PASSWORD=nikita
DB_HOST=127.0.0.1
DB_PORT=5433
DB_NAME=football_analysis
ACCESS_TOKEN_EXPIRE_MINUTES=120
JWT_SECRET_KEY=somekindalongnotsocomplicatedlinewithlengthofthirtytwocharacters
```

## 📝 TODO комментарии в коде

В компонентах и страницах оставлены TODO комментарии для интеграции с реальными API endpoints:

```javascript
// TODO: Замените на реальный API endpoint
const response = await fetch('http://localhost:8000/api/...');
```

После запуска backend эти endpoints должны работать автоматически.

## 💡 Советы

1. **Установка npm пакетов**: Если возникают ошибки, попробуйте `npm install --force`
2. **CORS**: Backend уже настроен для работы с фронтенда (allow_origins=["*"])
3. **Superset**: Пока компонент имеет базовую реализацию, нужна настройка
4. **Debugging**: Используйте браузер DevTools (F12) для проверки Network запросов

## 🔗 Ссылки на ресурсы

- [React Documentation](https://react.dev)
- [Material-UI Documentation](https://mui.com)
- [React Router Documentation](https://reactrouter.com)
- [Superset Embedded SDK](https://superset.apache.org/docs/using-superset/connecting-to-a-database)

---

**Статус**: ✅ Этап 1 завершён  
**Дата**: 14 Мая 2026  
**Следующий шаг**: Настройка Superset и тестирование API endpoints
