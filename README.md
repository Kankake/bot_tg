# Telegram Studio Bot (Manual)

Бот студии без интеграции с таблицами: все данные вводятся вручную через диалог.

## Установка
1. Склонируйте репозиторий.
2. Создайте `.env` на основе `.env.example` и заполните:
   ```dotenv
   BOT_TOKEN=...
   ADMIN_CHAT_ID=...
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Запустите бота:
   ```bash
   python main.py
   ```

## Сценарий
1. `/start` → меню
2. «Записаться на пробное» → выбор цели и направления
3. Ввод имени и телефона
4. Подтверждение → уведомление администратору

## Дальше
- Добавлять follow-up-сообщения в `follow_up.py`
