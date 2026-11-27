# 🤖 Telegram Avtoposting Boti (AI + Rejalashtiruvchi)

Ushbu bot Telegram kanalingiz uchun 2 ta asosiy vazifani bajaradi:
1. **Avtomatik yangiliklar (AI):** O'zbekistonning so'nggi va qiziqarli yangiliklarini (Kun.uz, Daryo.uz) topadi, Google Gemini AI yordamida Telegram kanali uchun moslab, ixcham va smayliklar (emojilar) bilan qayta yozadi, asl manba havolasini ko'rsatadi va sizga taqdim etadi. Siz unga o'sha yangilik bo'yicha rasm/video yoki gif biriktirib, belgilangan vaqtda kanalga chiqarishingiz mumkin.
2. **Qo'lda post rejalashtirish:** Istalgan matn, rasm, video yoki faylingizni yuborib, qachon (masalan: `18:30` yoki `+45m`) chiqishi kerakligini belgilaysiz. Bot vaqti kelganda avtomatik kanalga joylaydi.

---

## 🚀 O'rnatish va Ishga tushirish

### 1. Kerakli kutubxonalarni o'rnatish:
Terminal yoki buyruqlar satrida loyiha papkasiga kiring va quyidagilarni o'rnating:
```bash
pip install -r requirements.txt
```

### 2. Sozlamalarni kiritish (.env):
Loyihadagi `.env` faylini istalgan matn muharririda oching va quyidagi 4 ta maydonni to'ldiring:

- `BOT_TOKEN` — [@BotFather](https://t.me/BotFather) dan olingan bot tokeni (bepul).
- `CHANNEL_ID` — Botingiz admin bo'lgan kanalingiz usernamesi (masalan `@mening_kanalim`) yoki ID raqami.
- `ADMIN_ID` — O'zingizning shaxsiy Telegram ID raqamingiz ([@userinfobot](https://t.me/userinfobot) dan olinadi).
- `GEMINI_API_KEY` — [Google AI Studio](https://aistudio.google.com/) dan olingan bepul API kaliti.

### 3. Botni ishga tushirish:
```bash
python main.py
```

---

## 📱 Botdan foydalanish:

1. Botingizga kiring va **/start** tugmasini bosing.
2. Menyudan quyidagi buyruqlardan foydalanishingiz mumkin:
   - 📰 **"Qiziqarli yangilik topish (AI)"** — Yangilikni topadi, AI chiroyli qayta ishlaydi. Siz rasm/video qo'shib, vaqtini belgilashingiz mumkin.
   - ✍️ **"Qo'lda post tayyorlash"** — O'zingiz xohlagan matn va faylni yuborasiz, chiqarish vaqtini tanlaysiz.
   - 📋 **"Rejadagi postlar"** — Oldinda turgan rejalashtirilgan postlarni ko'rish va o'chirish.
   - ⚙️ **"Holatni tekshirish"** — Bot va kanal ulanishini tekshirish.

---

## ⏰ Vaqtni kiritish usullari:
Vaqt so'ralganda tayyor tugmalardan foydalanishingiz yoki quyidagicha yozishingiz mumkin:
- `14:30` — bugungi (yoki ertangi) soat 14:30 da;
- `+30m` — 30 daqiqadan keyin;
- `+2h` — 2 soatdan keyin;
- `hozir` — darhol kanalga joylash.
