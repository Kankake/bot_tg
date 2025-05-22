import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv
from booking_data import BookingData
from follow_up import init_scheduler
from admin_notifier import notify_admin

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
if ADMIN_CHAT_ID is None:
    raise RuntimeError("ADMIN_CHAT_ID not set in environment")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# In-memory storage for booking data
user_data: dict[int, BookingData] = {}

# Start handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton('ℹ️ О студии'),
        KeyboardButton('📝 Записаться на пробное')
    )
    await message.answer(
        'Привет! Я бот студии. Я могу рассказать о студии и записать вас на пробное занятие.',
        reply_markup=keyboard
    )

# Studio info handler
@dp.message(lambda msg: msg.text == 'ℹ️ О студии')
async def studio_info(message: types.Message):
    await message.answer(
        'Наша студия предлагает занятия по фитнесу, танцам и йоге. Нажмите "Записаться на пробное", чтобы оформить запись.'
    )

# Booking start
@dp.message(lambda msg: msg.text == '📝 Записаться на пробное')
async def book_start(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('📞 Позвонить администратору', callback_data='CALL_ADMIN'))
    markup.add(InlineKeyboardButton('🖥 Записаться через бота', callback_data='BOOK_VIA_BOT'))
    await message.answer('Выберите опцию:', reply_markup=markup)

# Call admin callback
@dp.callback_query(lambda c: c.data == 'CALL_ADMIN')
async def call_admin(cb: types.CallbackQuery):
    await cb.message.answer('Позвоните по номеру: +7XXX')
    await cb.answer()

# Begin booking flow
@dp.callback_query(lambda c: c.data == 'BOOK_VIA_BOT')
async def book_via_bot(cb: types.CallbackQuery):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add('Хочу укрепить здоровье', 'Хочу научиться танцевать')
    kb.add('Хочу похудеть', 'Другое')
    user_data[cb.from_user.id] = BookingData()
    user_data[cb.from_user.id].step = 'ask_goal'
    await cb.message.answer('Для чего вы хотите прийти на занятия?', reply_markup=kb)
    await cb.answer()

# Generic message handler for booking steps
@dp.message(lambda msg: True)
async def handle_steps(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        return
    data = user_data[uid]

    # Step: ask goal
    if data.step == 'ask_goal':
        data.goal = message.text
        data.step = 'ask_direction'
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add('Фитнес', 'Танцы', 'Йога', 'Другое')
        await message.answer('Выберите направление занятий:', reply_markup=kb)
        return

    # Step: ask direction
    if data.step == 'ask_direction':
        data.direction = message.text
        data.step = 'ask_name'
        await message.answer('Пожалуйста, введите ваше имя:')
        return

    # Step: ask name
    if data.step == 'ask_name':
        data.name = message.text
        data.step = 'ask_phone'
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(KeyboardButton('Отправить контакт', request_contact=True))
        await message.answer('Отправьте ваш номер телефона:', reply_markup=kb)
        return

    # Step: ask phone (contact)
    if message.contact and data.step == 'ask_phone':
        data.phone = message.contact.phone_number
        data.step = 'confirm'
        # Confirmation message
        confirm_text = (
            f"Подтвердите данные:
"
            f"Имя: {data.name}
"
            f"Телефон: {data.phone}
"
            f"Цель: {data.goal}
"
            f"Направление: {data.direction}"
        )
        await message.answer(confirm_text)
        # Confirmation buttons
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton('Подтвердить', callback_data='CONFIRM'))
        kb.add(InlineKeyboardButton('Отмена', callback_data='CANCEL'))
        await message.answer('Подтверждаете запись?', reply_markup=kb)
        return

# Confirmation callback
@dp.callback_query(lambda c: c.data == 'CONFIRM')
async def confirm(cb: types.CallbackQuery):
    uid = cb.from_user.id
    data = user_data.pop(uid)
    # Notify admin
    await notify_admin(bot, data)
    await cb.message.answer('Спасибо! Ваша запись принята. Администратор свяжется с вами.')
    await cb.answer()

# Cancellation callback
@dp.callback_query(lambda c: c.data == 'CANCEL')
async def cancel(cb: types.CallbackQuery):
    user_data.pop(cb.from_user.id, None)
    await cb.message.answer('Запись отменена.')
    await cb.answer()

# Initialize follow-ups
init_scheduler(bot)

# Run bot
if __name__ == '__main__':
    dp.run_polling(bot)
