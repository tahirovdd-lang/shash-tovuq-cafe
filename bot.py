import os
import json
import logging
import asyncio
import re

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logging.basicConfig(level=logging.INFO)

# ===================== ENV =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден в переменных окружения")

# ===================== SETTINGS =====================
ADMIN_ID = 6013591658
ADMINS = {6013591658}

WEBAPP_URL = "https://tahirovdd-lang.github.io/shash-tovuq-cafe/?v=1"
CHANNEL_USERNAME = "@shashtovuqfastfood"
MAP_URL = "https://yandex.uz/maps/org/200404730149/?ll=66.968820%2C39.669089&z=16.65"

# ВАЖНО: для канала используем start= (не startapp, не web_app)
OPEN_BOT_LINK = "https://t.me/SHASH_TOVUQ_bot?start=menu"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ===================== UI =====================
WEBAPP_BTN_TEXT = "🔵 Ochish / Открыть / Open"

WELCOME_3LANG = (
    "🇷🇺 <b>Добро пожаловать в SHASH TOVUQ!</b> 👋\n"
    "Нажмите «Открыть» ниже и оформите заказ.\n\n"
    "🇺🇿 <b>SHASH TOVUQ ga xush kelibsiz!</b> 👋\n"
    "Pastdagi «Ochish» tugmasini bosing va buyurtma bering.\n\n"
    "🇬🇧 <b>Welcome to SHASH TOVUQ!</b> 👋\n"
    "Tap “Open” below to place an order."
)

def menu_kb() -> ReplyKeyboardMarkup:
    # ✅ Это и есть настоящая “синяя кнопка” WebApp (работает в личке с ботом)
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=WEBAPP_BTN_TEXT, web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )

def pinned_post_kb() -> InlineKeyboardMarkup:
    # ✅ Это кнопка под постом в КАНАЛЕ (inline). “Синей” как WebApp она не станет,
    # но мы делаем стиль: 🔵 + CAPS + 1 большая кнопка
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔵 OCHISH / ОТКРЫТЬ / OPEN", url=OPEN_BOT_LINK)],
        [InlineKeyboardButton(text="📍 Manzil / Адрес", url=MAP_URL)]
    ])

# ===================== HELPERS =====================
def safe_html(s) -> str:
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))

def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    p = phone.strip()
    p = re.sub(r"[^\d+]", "", p)
    if p.startswith("998"):
        p = "+" + p
    return p

def payment_label(val: str) -> str:
    v = (val or "").strip().lower()
    if v in ("cash", "кэш", "кеш", "нал", "наличные", "naqd", "naqdi"):
        return "Наличные"
    if v in ("card", "карта", "karta", "plastik", "plastic", "click"):
        return "Карта / CLICK"
    if v in ("online", "transfer", "перевод"):
        return "Онлайн / Перевод"
    return val or "—"

def type_label(val: str) -> str:
    v = (val or "").strip().lower()
    if v in ("delivery", "доставка"):
        return "Доставка"
    if v in ("pickup", "самовывоз", "takeaway"):
        return "Самовывоз"
    return val or "—"

def build_user_link_html(from_user: types.User, data: dict) -> str:
    tg = data.get("tg") or {}
    username = tg.get("username") or from_user.username
    first_name = tg.get("first_name") or from_user.first_name or "Клиент"

    if username:
        u = safe_html(username.lstrip("@"))
        return f'👤 Клиент: <a href="https://t.me/{u}">@{u}</a>'
    return f'👤 Клиент: <a href="tg://user?id={from_user.id}">{safe_html(first_name)}</a>'

def build_phone_html(phone: str) -> str:
    p = normalize_phone(phone)
    if not p:
        return "📞 Телефон: <b>—</b>"
    return f'📞 Телефон: <a href="tel:{safe_html(p)}"><b>{safe_html(p)}</b></a>'

def is_admin(message: types.Message) -> bool:
    return bool(message.from_user and message.from_user.id in ADMINS)

# ===================== COMMANDS =====================
@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    # пользователь может прийти по кнопке из канала (?start=menu) — всё равно покажем WebApp кнопку
    await message.answer(WELCOME_3LANG, reply_markup=menu_kb())

@dp.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await message.answer(WELCOME_3LANG, reply_markup=menu_kb())

@dp.message(Command("id"))
async def my_id(message: types.Message):
    await message.answer(f"🆔 Ваш user_id: <b>{message.from_user.id}</b>")

# ✅ /post и /post@botname
@dp.message(F.text.regexp(r"^/post(@\w+)?$"))
async def post_to_channel(message: types.Message):
    if not is_admin(message):
        await message.answer("⛔ Нет доступа к /post")
        return

    post_text = (
        "🍗 <b>SHASH TOVUQ</b>\n"
        "Fast Food • Samarkand\n\n"
        "🇺🇿 Buyurtma berish uchun tugmani bosing 👇\n"
        "🇷🇺 Для заказа нажмите кнопку ниже 👇\n"
        "🇬🇧 Tap the button below to order 👇"
    )

    try:
        sent = await bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=post_text,
            reply_markup=pinned_post_kb()
        )
    except Exception as e:
        logging.exception("POST FAILED")
        await message.answer(
            "❌ <b>Не смог отправить пост в канал.</b>\n\n"
            f"<b>Ошибка:</b> <code>{type(e).__name__}</code>\n"
            f"<b>Текст:</b> <code>{str(e)[:350]}</code>"
        )
        return

    pinned = False
    try:
        await bot.pin_chat_message(
            chat_id=CHANNEL_USERNAME,
            message_id=sent.message_id,
            disable_notification=True
        )
        pinned = True
    except Exception as e:
        logging.warning(f"Pin failed: {e}")

    await message.answer("✅ Пост отправлен в канал." + (" 📌 Закреплено." if pinned else " ⚠️ Не закреплено (нет права)."))

# ===================== WEBAPP DATA =====================
@dp.message(F.web_app_data)
async def webapp_order(message: types.Message):
    raw = message.web_app_data.data
    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    await message.answer(
        "✅ <b>Заказ принят!</b>\nSHASH TOVUQ благодарит вас 😊",
        reply_markup=menu_kb()
    )

    phone = data.get("phone", "")
    address = data.get("address", "")
    pay = payment_label(data.get("payment"))
    otype = type_label(data.get("type"))
    total = data.get("total", "—")
    comment = data.get("comment", "")
    order_id = data.get("order_id", "")

    items_txt = ""
    items_list = data.get("items")
    if isinstance(items_list, list) and items_list:
        for it in items_list:
            try:
                nm = safe_html(it.get("name", ""))
                qty = safe_html(it.get("qty", ""))
                sm = safe_html(it.get("sum", ""))
                items_txt += f"• {nm} × <b>{qty}</b> = <b>{sm}</b>\n"
            except Exception:
                pass

    if not items_txt:
        order = data.get("order", {})
        if isinstance(order, dict) and order:
            items_txt = "\n".join([f"• <code>{safe_html(k)}</code> × <b>{safe_html(v)}</b>" for k, v in order.items()])
        else:
            items_txt = "• —"

    admin_text = (
        "🔥 <b>НОВЫЙ ЗАКАЗ — SHASH TOVUQ</b>\n\n"
        f"{build_user_link_html(message.from_user, data)}\n"
        f"{build_phone_html(phone)}\n"
        + (f"🧾 Заказ ID: <b>{safe_html(order_id)}</b>\n" if order_id else "")
        + f"🚚 Тип: <b>{safe_html(otype)}</b>\n"
        + f"📍 Адрес: <b>{safe_html(address) if address else '—'}</b>\n"
        + f"💳 Оплата: <b>{safe_html(pay)}</b>\n"
    )

    if comment:
        admin_text += f"💬 Комментарий: <b>{safe_html(comment)}</b>\n"

    admin_text += (
        "\n"
        f"{items_txt}\n\n"
        f"💰 <b>{safe_html(total)}</b> сум"
    )

    await bot.send_message(ADMIN_ID, admin_text)

# ===================== FALLBACK =====================
@dp.message()
async def fallback(message: types.Message):
    await message.answer(WELCOME_3LANG, reply_markup=menu_kb())

# ===================== MAIN =====================
async def main():
    logging.info("🚀 SHASH TOVUQ bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
