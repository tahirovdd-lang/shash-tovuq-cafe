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

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден в переменных окружения")

# ====== НАСТРОЙКИ ======
BOT_USERNAME = "shash_tovuq_bot"          # без @
ADMIN_ID = 6013591658

# WebApp (GitHub Pages)
WEBAPP_URL = "https://tahirovdd-lang.github.io/shash-tovuq-cafe/?v=1"

# Канал
CHANNEL_USERNAME = "@shashtovuqfastfood"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ====== ПРИВЕТСТВИЕ (3 ЯЗЫКА + ФЛАГИ) ======
WELCOME_3LANG = (
    "🇷🇺 <b>Добро пожаловать в SHASH TOVUQ!</b> 👋\n"
    "Выберите любимые блюда и оформите заказ — просто нажмите «Открыть» ниже.\n\n"
    "🇺🇿 <b>SHASH TOVUQ ga xush kelibsiz!</b> 👋\n"
    "Sevimli taomlaringizni tanlang va buyurtma bering — "
    "buning uchun pastdagi «Ochish» tugmasini bosing.\n\n"
    "🇬🇧 <b>Welcome to SHASH TOVUQ!</b> 👋\n"
    "Choose your favorite dishes and place an order — just tap “Open” below."
)

# ====== КНОПКА (НИЖНЯЯ) ДЛЯ ЛИЧКИ ======
MENU_BTN_TEXT = "Ochish / Открыть / Open"

def menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MENU_BTN_TEXT, web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )

async def send_welcome(message: types.Message):
    await message.answer(WELCOME_3LANG, reply_markup=menu_kb())

# ====== КНОПКА ДЛЯ КАНАЛА (INLINE) ======
def channel_webapp_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔵 Ochish / Открыть / Open",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]])

# ====== УТИЛИТЫ ======
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
    if v in ("online", "перевод", "transfer"):
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
    return bool(message.from_user and message.from_user.id == ADMIN_ID)

# ========= START =========
@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    await send_welcome(message)

@dp.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await send_welcome(message)

@dp.message(F.text == MENU_BTN_TEXT)
async def menu_button(message: types.Message):
    # Ничего не делаем: WebApp откроется сам по кнопке
    return

# ========= ПУБЛИКАЦИЯ В КАНАЛ =========
# Команда: /post  -> отправляет пост в канал + пытается закрепить
@dp.message(Command("post"))
async def post_to_channel(message: types.Message):
    if not is_admin(message):
        await message.answer("⛔ Команда доступна только администратору.")
        return

    text = (
        "🍗 <b>SHASH TOVUQ — Меню и заказ</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение и оформить заказ 👇"
    )

    # 1) отправляем пост
    sent = await bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=text,
        reply_markup=channel_webapp_kb()
    )

    # 2) пробуем закрепить (если боту выдали право “Закреплять сообщения”)
    pinned = False
    try:
        await bot.pin_chat_message(
            chat_id=CHANNEL_USERNAME,
            message_id=sent.message_id,
            disable_notification=True
        )
        pinned = True
    except Exception as e:
        logging.warning(f"Не смог закрепить сообщение в канале: {e}")

    await message.answer(
        "✅ Пост отправлен в канал."
        + (" 📌 Сообщение закреплено." if pinned else " ℹ️ Не закрепил (проверь права бота: 'Закреплять сообщения').")
    )

# ========= ПРИЁМ ДАННЫХ ИЗ WEBAPP =========
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

    # ВАЖНО: в твоём WebApp ты отправляешь payload.items (красивые строки) и payload.order (словарь key->qty).
    # Здесь я аккуратно использую items, если они есть; иначе — order.
    lines = []
    items_list = data.get("items")
    if isinstance(items_list, list) and items_list:
        for it in items_list:
            try:
                nm = safe_html(it.get("name", ""))
                qty = safe_html(it.get("qty", ""))
                pr = safe_html(it.get("price", ""))
                sm = safe_html(it.get("sum", ""))
                # кратко и красиво
                lines.append(f"• {nm} × <b>{qty}</b> = <b>{sm}</b>")
            except Exception:
                pass

    if not lines:
        order = data.get("order", {})
        if isinstance(order, dict) and order:
            # если пришёл dict key->qty (как у тебя), то это не имена, а ключи.
            # всё равно покажем, чтобы не терять заказ.
            lines = [f"• <code>{safe_html(k)}</code> × <b>{safe_html(v)}</b>" for k, v in order.items()]

    items_text = "\n".join(lines) if lines else "• —"

    phone = data.get("phone", "")
    address = data.get("address", "")
    pay = payment_label(data.get("payment"))
    otype = type_label(data.get("type"))
    total = data.get("total", "—")
    comment = data.get("comment", "")
    order_id = data.get("order_id", "")

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
        f"{items_text}\n\n"
        f"💰 <b>{safe_html(total)}</b> сум"
    )

    await bot.send_message(ADMIN_ID, admin_text)

# ========= FALLBACK =========
@dp.message()
async def fallback(message: types.Message):
    await send_welcome(message)

async def main():
    logging.info("🚀 SHASH TOVUQ bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
