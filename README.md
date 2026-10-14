# Colibri Wedding Planner

VK Mini App для планирования свадьбы.

## Архитектура

```
GitHub (этот репозиторий) — источник кода
    ↓ git push (авто-деплой через GitHub Actions)
app.nevessta.ru (colibri server) — фронтенд + API
    ↑
VK Mini App (vk.com/app54816577)
```

## Функции
- 👰🤵 Данные свадьбы (имена, дата, бюджет, место)
- 👥 Гости (RSVP, блюда, столы, комментарии)
- 💰 Бюджет (категории, оплата, шкала)
- ✅ Задачи/чек-лист (приоритеты, дедлайны)
- 🪑 Рассадка (столы, назначение гостей)
- 🤝 Совместное планирование (роли, QR-приглашения)
- 🎨 6 тем оформления

## Структура
```
frontend/index.html — SPA приложение
backend/api.py      — Flask REST API
backend/requirements.txt
.github/workflows/deploy.yml — авто-деплой
```

## Технологии
- **Frontend:** HTML/CSS/JS (SPA), VK Bridge
- **Backend:** Flask + SQLite
- **Сервер:** nginx + certbot (SSL)
- **Хостинг:** colibri (13.143.175.163)
