import os

async def notify_admin(bot, data):
    chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    text = (
        "Новая запись:
"
        f"Имя: {data.name}
"
        f"Телефон: {data.phone}
"
        f"Цель: {data.goal}
"
        f"Направление: {data.direction}"
    )
    await bot.send_message(chat_id, text)
```### follow_up.py
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

def init_scheduler(bot):
    scheduler = AsyncIOScheduler()
    # Здесь можно добавить задания для авторассылок
    scheduler.start()
