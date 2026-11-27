import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent").strip()

# Adminlar ro'yxatini yuklash (bir nechta admin ID sini vergul bilan yozish mumkin: 12345,67890)
raw_admins = os.getenv("ADMIN_IDS", "") or os.getenv("ADMIN_ID", "")
ADMIN_IDS = []
for part in raw_admins.split(","):
    part = part.strip()
    if part.isdigit():
        ADMIN_IDS.append(int(part))

# Eski bitta ADMIN_ID uchun moslik
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 0

AUTO_NEWS_HOUR = int(os.getenv("AUTO_NEWS_HOUR", "9"))
AUTO_NEWS_MINUTE = int(os.getenv("AUTO_NEWS_MINUTE", "0"))
