import os

async def notify_admin(bot, data):
    chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    text = (
        "Новая запись:\n"
        f"Имя: {data.name}\n"
        f"Телефон: {data.phone}\n"
        f"Цель: {data.goal}\n"
        f"Направление: {data.direction}"
    )
    await bot.send_message(chat_id, text)

async def notify_admin(bot, data):
    chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    await bot.send_message(
        chat_id,
        f"Новая запись:\nИмя: {data.name}\nТелефон: {data.phone}\nЦель: {data.goal}\nНаправление: {data.direction}"
    )
