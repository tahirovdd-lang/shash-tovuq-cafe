import os
import json
import logging
import asyncio

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден")

ADMIN_ID = 6013591658
ADMINS = {6013591658}

WEBAPP_URL = "https://tahirovdd-lang.github.io/shash-tovuq-cafe/?v=1"
CHANNEL_USERNAME = "@shashtovuqfastfood"

BOT_LINK = "https://t.me/SHASH_TOVUQ_bot"
STARTAPP_LINK = "https://t.me/SHASH_TOVUQ_bot?startapp=menu"  # откроет бот и покажет кнопку WebApp
# Если вдруг startapp не сработает на твоём клиенте — используй start:
# STARTAPP_LINK = "https://t.me/SHASH_TOVUQ_bot?start=menu"

MAP_URL = "https://yandex.uz/maps/org/200404730149/?ll=66.968820%2C39.669089&z=16.65"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

MENU_BTN_TEXT = "🔵 Ochish / Открыть / Open"

def menu_kb():
    # ✅ Это и есть “синяя кнопка” (web_app) — она работает в ЛИЧКЕ с ботом
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MENU_BTN_TEXT, web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )

def channel_kb_url():
    # ✅ В канале web_app нельзя -> делаем URL-кнопку
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔵 Ochish / Открыть / Open", url=STARTAPP_LINK)],
        [InlineKeyboardButton(text="📍 Manzil / Адрес / Location", url=MAP_URL)]
    ])

WELCOME = (
    "🍗 <b>SHASH TOVUQ</b>\n\n"
    "Нажмите кнопку ниже, чтобы открыть меню 👇"
)

@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    # command.args может быть "menu" если пришли по ?start=menu
    await message.answer(WELCOME, reply_markup=menu_kb())

@dp.message(Command("id"))
async def my_id(message: types.Message):
    await message.answer(f"🆔 Ваш user_id: <b>{message.from_user.id}</b>")

# ловим /post и /post@botname
@dp.message(F.text.regexp(r"^/post(@\w+)?$"))
async def post_to_channel(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Нет доступа к /post")
        return

    post_text = (
        "🍗 <b>SHASH TOVUQ — Menu & Buyurtma</b>\n\n"
        "🇺🇿 Buyurtma berish uchun tugmani bosing 👇\n"
        "🇷🇺 Для заказа нажмите кнопку ниже 👇\n"
        "🇬🇧 Tap the button below to order 👇\n\n"
        f"🤖 Бот: {BOT_LINK}"
    )

    try:
        sent = await bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=post_text,
            reply_markup=channel_kb_url()
        )
    except Exception as e:
        logging.exception("POST FAILED")
        await message.answer(
            "❌ <b>Не смог отправить пост в канал.</b>\n\n"
            f"<b>Ошибка:</b> <code>{type(e).__name__}</code>\n"
            f"<b>Текст:</b> <code>{str(e)[:350]}</code>\n\n"
            "Проверь права бота в канале: публиковать сообщения."
        )
        return

    pinned = "—"
    try:
        await bot.pin_chat_message(
            chat_id=CHANNEL_USERNAME,
            message_id=sent.message_id,
            disable_notification=True
        )
        pinned = "📌 Закреплено"
    except Exception as e:
        logging.warning(f"Pin failed: {e}")
        pinned = "⚠️ Не закреплено (нет права закреплять)"

    await message.answer(f"✅ Пост отправлен в канал\n{pinned}")

@dp.message(F.web_app_data)
async def webapp_order(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        data = {}

    await message.answer(
        "✅ <b>Заказ принят!</b>\nМы скоро свяжемся с вами 😊",
        reply_markup=menu_kb()
    )

    await bot.send_message(
        ADMIN_ID,
        "🔥 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
        f"<code>{json.dumps(data, ensure_ascii=False, indent=2)[:3500]}</code>"
    )

@dp.message()
async def fallback(message: types.Message):
    await message.answer(WELCOME, reply_markup=menu_kb())

async def main():
    logging.info("🚀 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
