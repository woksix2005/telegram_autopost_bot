import asyncio
import os
import threading, time
from flask import Flask
import logging
import telebot
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler_service import start_scheduler

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.Telebot(TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


async def main():
    if not BOT_TOKEN:
        print("\n❌ XATOLIK: .env faylida BOT_TOKEN ko'rsatilmagan!")
        print("Iltimos, .env faylini ochib @BotFather dan olingan tokenni kiriting.\n")
        return

    # Ma'lumotlar bazasini ishga tushirish
    init_db()
    logging.info("Baza ishga tushirildi.")

    # Bot va Dispatcher yaratish
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    # Vaqt rejalashtiruvchisini ishga tushirish
    start_scheduler(bot)
    logging.info("Scheduler (vaqt rejalashtiruvchi) ishga tushdi.")

    logging.info("Bot muvaffaqiyatli ishga tushdi! Xabarlar kutilmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")


app = Flask(__name__)


@app.route("/")
def health():
    return "Bot ishlayapti", 200


def run_bot():
    bot.remove_webhook()
    while True:  # xato bo'lsa qayta urinadi
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print("Polling xatosi:", e, flush=True)
        time.sleep(5)


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


bot.infinity_polling()
