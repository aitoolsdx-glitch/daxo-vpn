import asyncio
import sqlite3
import os  # Добавь эту строку обязательно!
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- НАСТРОЙКИ (БЕРЕМ ИЗ ПАНЕЛИ RENDER) ---
API_TOKEN = os.getenv('BOT_TOKEN')
CRYPTO_TOKEN = os.getenv('CRYPTO_TOKEN')
ADMIN_ID = 5476069446  # ID можно оставить так, это не секрет


bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ ---
db = sqlite3.connect("vpn_pro.db")
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, status TEXT DEFAULT 'free')")
cur.execute("CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, config TEXT, type TEXT)")
db.commit()

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Получить VPN", callback_data="get_vpn")],
        [InlineKeyboardButton(text="💎 Купить Premium (Crypto)", callback_data="buy_premium")],
        [InlineKeyboardButton(text="📊 Профиль", callback_data="profile")]
    ])

# --- ЛОГИКА ОПЛАТЫ (ЭМУЛЯЦИЯ ЧЕРЕЗ КНОПКУ) ---
@dp.callback_query(F.data == "buy_premium")
async def pay_process(call: CallbackQuery):
    # Здесь логика создания чека через API CryptoPay (упрощено для работы)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 5$ (USDT)", url="https://t.me/CryptoBot?start=test")],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_pay")]
    ])
    await call.message.answer("💎 **Покупка Premium доступа**\n\nПосле оплаты ты получишь доступ к VIP-серверам с низкой задержкой.", reply_markup=kb)

@dp.callback_query(F.data == "check_pay")
async def check_pay(call: CallbackQuery):
    # Тут должна быть проверка через requests.get(CRYPTO_PAY_API)
    await call.answer("⏳ Платеж обрабатывается или не найден. Попробуй позже.", show_alert=True)

# --- ЛОГИКА ВЫДАЧИ ---
@dp.callback_query(F.data == "get_vpn")
async def send_vpn(call: CallbackQuery):
    cur.execute("SELECT config FROM keys ORDER BY RANDOM() LIMIT 1")
    res = cur.fetchone()
    if res:
        await call.message.answer(f"🚀 **Твой ключ готов:**\n\n`{res[0]}`\n\nСкопируй и импортируй в v2rayNG / Shadowsocks.")
    else:
        await call.message.answer("❌ Свободные ключи закончились. Напиши @Danilo_191")

# --- АДМИН ПАНЕЛЬ ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Юзеры", callback_data="a_stats"), InlineKeyboardButton(text="🔑 Ключи", callback_data="a_keys")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="a_bc")],
        [InlineKeyboardButton(text="➕ Добавить VLESS", callback_data="a_add")]
    ])
    await message.answer("🛠 **Daxo Control Panel**", reply_markup=kb)

# Добавление ключей (просто отправь боту ссылку если ты админ)
@dp.message(F.text.regexp(r"(vless|vmess|ss)://"))
async def add_key_auto(message: types.Message):
    if message.from_id != ADMIN_ID: return
    cur.execute("INSERT INTO keys (config, type) VALUES (?, ?)", (message.text, "premium"))
    db.commit()
    await message.answer("✅ Ключ добавлен в базу системы!")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())