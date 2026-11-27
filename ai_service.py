import aiohttp
from config import GEMINI_API_KEY

LEGAL_PROMPT = """Siz O'zbekistondagi "AHD" advokatlik firmasi rasmiy kanali (@ahd_advokat) bosh huquqshunos-muharririsiz.
Sizga taqdim etilayotgan huquqiy ma'lumotni (Adliya vazirligi yoki OAV yangiligini) qayta ishlab, kanal uchun professional post tayyorlab bering.

MUHIM QOIDALAR:
1. ASLO asl matnni aynan o'zidek qilib ko'chirib qo'ymang!
2. Yangilikning asl huquqiy mazmunini o'zgartirmang, lekin uni sal kengaytirib, xalqchil va tushunarli qilib yozing.
3. Obunachilarga (fuqarolarga) bu qoida nima uchun muhimligi va ularga qanday ta'sir qilishi haqida qisqa tushuntirish bering.
4. Mos keluvchi huquqiy emojilarni qo'ying (⚖️, 🏛, 📌, ❗️, 💡, 📜).
5. Post oxiriga qisqa advokat xulosasi yoki tavsiyasini qo'shing.
6. Asl manba havolasini ko'rsating.
7. HTML teglari (<b>qalin</b>, <i>kursiv</i>, <a href="...">link</a>) dan foydalaning.

Ma'lumot sarlavhasi: {title}
Ma'lumot matni: {description}
Manba havolasi: {link}
Manba nomi: {source}

Faqat tayyor post matnini yozing. Ortiqcha kirish so'zlari yoki izohlarsiz."""

WORKING_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-flash-latest"
]

async def rewrite_news_with_ai(title: str, description: str, link: str, source: str) -> str:
    """Gemini AI yordamida huquqiy ma'lumotni advokatlik firmasi uslubida qayta yozadi"""
    if not GEMINI_API_KEY:
        return format_fallback(title, description, link, source)
        
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": LEGAL_PROMPT.format(
                        title=title,
                        description=description,
                        link=link,
                        source=source
                    )}
                ]
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        for model in WORKING_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
            except Exception as e:
                print(f"{model} orqali generatsiyada xatolik: {e}")
                continue

    return format_fallback(title, description, link, source)

def format_fallback(title: str, description: str, link: str, source: str) -> str:
    """Agar AI vaqtincha javob bermasa, advokatlik uslubidagi sifatli format"""
    return (
        f"⚖️ <b>HUQUQIY AXBOROT | {title}</b>\n\n"
        f"📌 <b>Mazmuni:</b>\n{description}\n\n"
        f"💡 <i>Eslatib o'tamiz: O'z huquqlaringizni bilish va qonunchilik talablariga rioya qilish har bir fuqaroning burchidir.</i>\n\n"
        f"🔗 <b>Rasmiy manba:</b> <a href=\"{link}\">{source}</a>\n"
        f"🏛 <b>\"AHD\" advokatlik firmasi</b>"
    )
