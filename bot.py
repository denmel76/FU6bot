import asyncio
import logging
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, WEBHOOK_URL, ADMIN_ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

CLEANING_TYPES = {
    "standard": "Стандартная",
    "general": "Генеральная"
}

class OrderState(StatesGroup):
    name = State()
    type = State()
    area = State()
    address = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Здравствуйте! Давайте закажем уборку.\nКак вас зовут?")
    await state.set_state(OrderState.name)

@dp.message(OrderState.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Стандартная", callback_data="type_standard")],
        [InlineKeyboardButton(text="Генеральная", callback_data="type_general")]
    ])
    await message.answer("Выберите тип уборки:", reply_markup=keyboard)
    await state.set_state(OrderState.type)

@dp.callback_query(OrderState.type, F.data.startswith("type_"))
async def process_type(callback: CallbackQuery, state: FSMContext):
    type_key = callback.data.split("_")[1]
    await state.update_data(cleaning_type=CLEANING_TYPES.get(type_key))
    await callback.message.edit_text("Введите площадь в кв.м. (только число):")
    await state.set_state(OrderState.area)

@dp.message(OrderState.area)
async def process_area(message: types.Message, state: FSMContext):
    try:
        area = float(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите число (например, 50).")
        return
    
    await state.update_data(area=area)
    await message.answer("Введите адрес:")
    await state.set_state(OrderState.address)

@dp.message(OrderState.address)
async def process_address(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    payload = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "name": user_data['name'],
        "cleaning_type": user_data['cleaning_type'],
        "area": user_data['area'],
        "address": message.text
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(WEBHOOK_URL, json=payload) as response:
                if response.status == 200:
                    await message.answer("✅ Спасибо! Ваша заявка принята. Менеджер свяжется с вами.")
                else:
                    await message.answer("⚠️ Ошибка сервера. Попробуйте позже.")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("⚠️ Сервер недоступен.")
    
    await state.clear()

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
