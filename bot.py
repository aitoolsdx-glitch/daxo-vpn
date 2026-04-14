import asyncio
import sqlite3
import os
import threading
import http.server
import socketserver
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- СЕРВЕР-ОБМАНКА ДЛЯ RENDER ---
def run_dummy_server():
    # Render требует, чтобы на порту 8080 что-то "жило"
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    # Уменьшаем таймаут, чтобы не блокировать систему
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"DEBUG: Dummy server started on port {port}")
        httpd.serve_forever()

# Запускаем обманку в отдельном потоке, чтобы она не мешала боту
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- НАСТРОЙКИ (БЕРЕМ ИЗ ENV) ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 5476069446  # Твой ID

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
    buttons = [
        [InlineKeyboardButton(text="⚡ Получить VPN", callback_data="get_vpn")],
        [InlineKeyboardButton(text="💎 Купить Premium", callback_data="buy_premium")],
        [InlineKeyboardButton(text="📊 Мой профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (message.from_user.id,))
    db.commit()
    await message.answer(f"Привет, {message.from_user.first_name}! Это **CHIIP VPN**.\n\nНажми кнопку ниже, чтобы получить доступ.", reply_markup=main_kb())

@dp.callback_query(F.data == "get_vpn")
async def send_vpn(call: CallbackQuery):
    cur.execute("SELECT config FROM keys ORDER BY RANDOM() LIMIT 1")
    key = cur.fetchone()
    if key:
        await call.message.answer(f"Твой ключ доступа:\n\n`{key[0]}`\n\nСкопируй его в приложение V2Ray/v2rayNG.", parse_mode="Markdown")
    else:
        await call.message.answer("❌ Ключи закончились. Админ скоро добавит новые!")
    await call.answer()

@dp.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    cur.execute("SELECT status FROM users WHERE id = ?", (call.from_user.id,))
    status = cur.fetchone()[0]
    await call.message.answer(f"👤 Профиль: {call.from_user.first_name}\n🔓 Статус: {status.upper()}")
    await call.answer()

# --- АДМИН-ПАНЕЛЬ (ДОБАВЛЕНИЕ КЛЮЧЕЙ) ---
@dp.message(F.text.startswith("vless://") | F.text.startswith("vmess://") | F.text.startswith("ss://"))
async def add_key(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        cur.execute("INSERT INTO keys (config) VALUES (?)", (message.text,))
        db.commit()
        await message.answer("✅ Ключ успешно добавлен в базу!")
    else:
        await message.answer("У тебя нет прав для добавления ключей.")

# --- ЗАПУСК ---
async def main():
    print("--- CHIIP SYSTEM ONLINE ---")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())