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
BOT_TOKEN = os.getenv(7789111664:AAHFxzibymG5omwu7kI1N-oSOy1j4rscGr4)
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# In-memory storage
user_data = {}

# Start handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('ℹ️ О студии'), KeyboardButton('📝 Записаться на пробное'))
    await message.answer(
        'Привет! Я бот студии. Я могу рассказать о студии и записать вас на пробное занятие.',
        reply_markup=keyboard
    )

# Info handler
@dp.message(lambda msg: msg.text == 'ℹ️ О студии')
async def studio_info(message: types.Message):
    await message.answer(
        'Наша студия предлагает занятия по разным направлениям: фитнес, танцы, йога. Выберите в меню "Записаться на пробное" и я помогу оформить запись.'
    )

# Booking start
@dp.message(lambda msg: msg.text == '📝 Записаться на пробное')
async def book_start(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('📞 Позвонить администратору', callback_data='CALL_ADMIN'))
    kb.add(InlineKeyboardButton('🖥 Записаться через бота', callback_data='BOOK_VIA_BOT'))
    await message.answer('Выберите опцию:', reply_markup=kb)

# Call admin
@dp.callback_query(lambda c: c.data == 'CALL_ADMIN')
async def call_admin(cb: types.CallbackQuery):
    await cb.message.answer('Позвоните по номеру: +7XXX')
    await cb.answer()

# Booking via bot: ask goal
@dp.callback_query(lambda c: c.data == 'BOOK_VIA_BOT')
async def book_via_bot(cb: types.CallbackQuery):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add('Хочу укрепить здоровье', 'Хочу научиться танцевать')
    kb.add('Хочу похудеть', 'Другое')
    user_data[cb.from_user.id] = BookingData()
    await cb.message.answer('Для чего вы хотите прийти на занятия?', reply_markup=kb)
    user_data[cb.from_user.id].step = 'ask_goal'
    await cb.answer()

# Generic handler
@dp.message(lambda msg: True)
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
        await message.answer('Выберите направление занятий:', reply_markup=kb)
        return

    if data.step == 'ask_direction':
        data.direction = message.text
        data.step = 'ask_name'
        await message.answer('Пожалуйста, введите ваше имя (как вас зовут):')
        return

    if data.step == 'ask_name':
        data.name = message.text
        data.step = 'ask_phone'
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(KeyboardButton('Отправить контакт', request_contact=True))
        await message.answer('Отправьте ваш номер телефона, нажав кнопку:', reply_markup=kb)
        return

    if message.contact and data.step == 'ask_phone':
        data.phone = message.contact.phone_number
        data.step = 'confirm'
        # Properly close the f-string and parentheses
        await message.answer(
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
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton('Подтвердить', callback_data='CONFIRM'))
        kb.add(InlineKeyboardButton('Отмена', callback_data='CANCEL'))
        await message.answer('Подтверждаете запись?', reply_markup=kb)
        return

# Confirmation
@dp.callback_query(lambda c: c.data == 'CONFIRM')
async def confirm(cb: types.CallbackQuery):
    uid = cb.from_user.id
    data = user_data.pop(uid)
    # Notify admin
    await notify_admin(bot, data)
    await cb.message.answer('Спасибо! Ваша запись принята. Администратор свяжется с вами.')
    await cb.answer()

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
