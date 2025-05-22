import os

async def notify_admin(bot, data):
    chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    await bot.send_message(
        chat_id,
        f"Новая запись:
Имя: {data.name}
Телефон: {data.phone}
Цель: {data.goal}
Направление: {data.direction}"
    )
