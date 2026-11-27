from datetime import datetime, timedelta
import zoneinfo
from config import TIMEZONE

def get_tz():
    try:
        return zoneinfo.ZoneInfo(TIMEZONE)
    except Exception:
        return zoneinfo.ZoneInfo("Asia/Tashkent")

def get_now() -> datetime:
    return datetime.now(get_tz())

def parse_schedule_time(input_str: str):
    """
    Turli formatdagi vaqtlarni 'YYYY-MM-DD HH:MM' formatiga o'tkazadi:
    - 'hozir' -> hozirgi vaqt
    - '15:30' -> bugungi 15:30 (agar o'tib ketgan bo'lsa ertangi 15:30)
    - '+30' yoki '+30m' -> 30 daqiqadan keyin
    - '+1h' yoki '+2h' -> 1 yoki 2 soatdan keyin
    - 'YYYY-MM-DD HH:MM' yoki 'DD.MM.YYYY HH:MM'
    """
    now = get_now()
    s = input_str.strip().lower()

    if s in ["hozir", "now", "darhol"]:
        return now.strftime("%Y-%m-%d %H:%M")

    # +daqiqalar (+15, +30m, +45m)
    if s.startswith("+"):
        val = s[1:]
        if val.endswith("m"):
            minutes = int(val[:-1])
            target = now + timedelta(minutes=minutes)
            return target.strftime("%Y-%m-%d %H:%M")
        elif val.endswith("h") or val.endswith("s"):
            hours = int(val[:-1])
            target = now + timedelta(hours=hours)
            return target.strftime("%Y-%m-%d %H:%M")
        elif val.isdigit():
            target = now + timedelta(minutes=int(val))
            return target.strftime("%Y-%m-%d %H:%M")

    # HH:MM formati (masalan, 18:30)
    if ":" in s and len(s) in [4, 5]:
        parts = s.split(":")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            hour = int(parts[0])
            minute = int(parts[1])
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                # Agar bugungi vaqt o'tib ketgan bo'lsa, ertangi kunga qo'yamiz
                target += timedelta(days=1)
            return target.strftime("%Y-%m-%d %H:%M")

    # To'liq sana va vaqt (DD.MM.YYYY HH:MM)
    for fmt in ("%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(s, fmt)
            target = dt.replace(tzinfo=get_tz())
            return target.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass

    return None
