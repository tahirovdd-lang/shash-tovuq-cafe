import os
import json
import logging
import asyncio

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logging.basicConfig(level=logging.INFO)

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден")

ADMIN_ID = 6013591658
ADMINS = {6013591658}

WEBAPP_URL = "https://tahirovdd-lang.github.io/shash-tovuq-cafe/?v=1"
CHANNEL_USERNAME = "@shashtovuqfastfood"
MAP_URL = "https://yandex.uz/maps/org/200404730149/?ll=66.968820%2C39.669089&z=16.65"

# ============================================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ================= КНОПКИ ====================
MENU_BTN_TEXT = "Ochish / Открыть / Open"

def menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text=MENU_BTN_TEXT,
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]],
        resize_keyboard=True
    )

def channel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔵 Ochish / Открыть / Open",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton(
            text="📍 Manzil / Адрес / Location",
            url=MAP_URL
        )]
    ])

# ================= /start ====================
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🍗 <b>SHASH TOVUQ</b>\n\nНажмите кнопку ниже 👇",
        reply_markup=menu_kb()
    )

# ================= /id ======================
@dp.message(Command("id"))
async def my_id(message: types.Message):
    await message.answer(f"🆔 Ваш user_id: <b>{message.from_user.id}</b>")

# ================= /post ====================
@dp.message(Command("post"))
async def post_to_channel(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Нет доступа")
        return

    post_text = (
        "🍗 <b>SHASH TOVUQ — Menu & Buyurtma</b>\n\n"
        "🇺🇿 Buyurtma berish uchun pastdagi tugmani bosing\n"
        "🇷🇺 Для заказа нажмите кнопку ниже\n"
        "🇬🇧 Tap the button below to order"
    )

    sent = await bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=post_text,
        reply_markup=channel_kb()
    )

    # пробуем закрепить
    try:
        await bot.pin_chat_message(
            chat_id=CHANNEL_USERNAME,
            message_id=sent.message_id,
            disable_notification=True
        )
        pinned = "📌 Закреплено"
    except:
        pinned = "⚠️ Не закреплено (проверь права бота)"

    await message.answer(f"✅ Пост отправлен в канал\n{pinned}")

# ============ WEBAPP DATA ===================
@dp.message(F.web_app_data)
async def webapp_order(message: types.Message):
    data = json.loads(message.web_app_data.data)

    await message.answer(
        "✅ <b>Заказ принят!</b>\nМы скоро свяжемся с вами 😊",
        reply_markup=menu_kb()
    )

    await bot.send_message(
        ADMIN_ID,
        f"🔥 <b>НОВЫЙ ЗАКАЗ</b>\n\n<code>{json.dumps(data, ensure_ascii=False, indent=2)}</code>"
    )

# ================= fallback =================
@dp.message()
async def fallback(message: types.Message):
    await start(message)

# ================= main =====================
async def main():
    logging.info("🚀 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
