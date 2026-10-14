# Деплой

## Автоматический
При push в `main` → GitHub Actions автоматически:
1. Делает бекап текущей версии
2. Копирует `frontend/index.html` и `backend/api.py` на сервер
3. Синхронизирует `/var/www/colibri/`
4. Перезапускает `colibri-api.service`
5. Проверяет `/api/health`

## Настройка GitHub Secrets
В репозитории → Settings → Secrets → Actions:
- `SERVER_HOST` — IP сервера (13.143.175.163)
- `SERVER_USER` — SSH пользователь (root)
- `SERVER_PASS` — SSH пароль

## Ручной деплой
```bash
scp frontend/index.html root@13.143.175.163:/root/colibri/build/
scp backend/api.py root@13.143.175.163:/root/colibri/api/
ssh root@13.143.175.163 "cp /root/colibri/build/index.html /var/www/colibri/ && systemctl restart colibri-api.service"
```

## VK Mini App
- URL: `https://app.nevessta.ru`
- VK Hosting: **не используется**
