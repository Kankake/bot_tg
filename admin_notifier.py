import os

async def notify_admin(bot, data):
    chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    text = f"Новая запись:\nИмя: {data.name}\nТелефон: {data.phone}\nЦель: {data.goal}\nНаправление: {data.direction}"
    await bot.send_message(chat_id, text)
