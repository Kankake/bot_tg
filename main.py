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
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
if not ADMIN_CHAT_ID:
    raise RuntimeError("ADMIN_CHAT_ID not set in .env")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

# Initialize bot and dispatcher
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Storage for user bookings
user_data: dict[int, BookingData] = {}

# /start handler
def reply_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('ℹ️ О студии'), KeyboardButton('📝 Записаться на пробное'))
    return message.answer('Привет! Я бот студии. Чем могу помочь?', reply_markup=kb)

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await reply_menu(message)

@dp.message(lambda m: m.text == 'ℹ️ О студии')
async def studio_info(message: types.Message):
    text = 'Наша студия: фитнес, танцы, йога. Выберите "Записаться на пробное".'
    await message.answer(text)

@dp.message(lambda m: m.text == '📝 Записаться на пробное')
async def book_start(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('📞 Позвонить администратору', callback_data='CALL_ADMIN'))
    kb.add(InlineKeyboardButton('🖥 Записаться через бота', callback_data='BOOK'))
    await message.answer('Выберите опцию:', reply_markup=kb)

@dp.callback_query(lambda c: c.data == 'CALL_ADMIN')
async def call_admin(cb: types.CallbackQuery):
    await cb.message.answer('Позвоните администратору по номеру +7XXX')
    await cb.answer()

@dp.callback_query(lambda c: c.data == 'BOOK')
async def book_flow(cb: types.CallbackQuery):
    user_data[cb.from_user.id] = BookingData()
    user_data[cb.from_user.id].step = 'ask_goal'
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add('Фитнес', 'Танцы', 'Йога', 'Другое')
    await cb.message.answer('Для чего вы хотите прийти на занятия?', reply_markup=kb)
    await cb.answer()

@dp.message(lambda m: True)
async def handle_steps(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        return
    data = user_data[uid]

    if data.step == 'ask_goal':
        data.goal = message.text
        data.step = 'ask_direction'
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add('Фитнес', 'Танцы', 'Йога', 'Другое')
        await message.answer('Выберите направление:', reply_markup=kb)
        return

    if data.step == 'ask_direction':
        data.direction = message.text
        data.step = 'ask_name'
        await message.answer('Введите ваше имя:')
        return

    if data.step == 'ask_name':
        data.name = message.text
        data.step = 'ask_phone'
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(KeyboardButton('Отправить контакт', request_contact=True))
        await message.answer('Отправьте контакт:', reply_markup=kb)
        return

    if data.step == 'ask_phone' and message.contact:
        data.phone = message.contact.phone_number
        data.step = 'confirm'
        confirm_text = (
            f"Подтвердите следующие данные:\n"
            f"Имя: {data.name}\n"
            f"Телефон: {data.phone}\n"
            f"Цель: {data.goal}\n"
            f"Направление: {data.direction}"
        )
        await message.answer(confirm_text)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton('Подтвердить', callback_data='CONFIRM'))
        kb.add(InlineKeyboardButton('Отмена', callback_data='CANCEL'))
        await message.answer('Подтверждаете?', reply_markup=kb)
        return

@dp.callback_query(lambda c: c.data == 'CONFIRM')
async def confirm(cb: types.CallbackQuery):
    data = user_data.pop(cb.from_user.id)
    await notify_admin(bot, data)
    await cb.message.answer('Спасибо, запись принята.')
    await cb.answer()

@dp.callback_query(lambda c: c.data == 'CANCEL')
async def cancel(cb: types.CallbackQuery):
    user_data.pop(cb.from_user.id, None)
    await cb.message.answer('Запись отменена.')
    await cb.answer()

# Scheduler for follow-ups
init_scheduler(bot)

if __name__ == '__main__':
    dp.run_polling(bot)
