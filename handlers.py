from datetime import timedelta
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command

from config import ADMIN_IDS, CHANNEL_ID
from database import (
    add_scheduled_post, mark_news_processed, 
    get_upcoming_posts, delete_scheduled_post
)
from news_service import get_latest_legal_news
from ai_service import rewrite_news_with_ai
from time_utils import parse_schedule_time, get_now

router = Router()

class PostStates(StatesGroup):
    waiting_for_news_media = State()
    waiting_for_news_time = State()
    waiting_for_manual_content = State()
    waiting_for_manual_time = State()

news_drafts = {}
manual_drafts = {}

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚖️ Huquqiy yangilik topish (AI)")],
            [KeyboardButton(text="✍️ Qo'lda post tayyorlash")],
            [KeyboardButton(text="📋 Rejadagi postlar"), KeyboardButton(text="⚙️ Holatni tekshirish")]
        ],
        resize_keyboard=True
    )

def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("Kechirasiz, bu bot faqat \"AHD\" advokatlik firmasi administratori uchun.")
        return
        
    welcome = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        "🏛 <b>\"AHD\" advokatlik firmasi</b> kanali uchun avtomatik post yordamchisiga xush kelibsiz.\n\n"
        "⚡️ <b>Tizim sozlamalari:</b>\n"
        "• Har 3 soatda O'zbekiston Adliya vazirligi va Kun.uz huquqiy bo'limidan sara qonunchilik ma'lumotlarini qidiraman;\n"
        "• Kanalga chiqishidan 30 daqiqa oldin sizga tayyor postni taklif qilaman;\n"
        "• Siz ruxsat bersangiz, 30 daqiqadan so'ng kanalga avtomatik joylanadi;\n"
        "• Shuningdek, xohlagan vaqtingizda qo'lda ham post rejalashtirishingiz mumkin."
    )
    await message.answer(welcome, reply_markup=get_main_keyboard(), parse_mode="HTML")

@router.message(F.text == "⚙️ Holatni tekshirish")
async def check_status(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
        
    status_text = (
        "⚙️ <b>Tizim holati:</b>\n\n"
        f"👤 <b>Admin ID:</b> <code>{message.from_user.id}</code>\n"
        f"📢 <b>Kanal:</b> <code>{CHANNEL_ID}</code>\n"
        f"🕒 <b>Hozirgi vaqt:</b> <code>{get_now().strftime('%Y-%m-%d %H:%M')}</code>\n"
        f"🔄 <b>Avtomatik qidiruv:</b> Har 3 soatda (postdan 30 daqiqa oldin)\n"
    )
    
    try:
        chat = await bot.get_chat(CHANNEL_ID)
        status_text += f"✅ <b>Kanalga ulanish:</b> Muvaffaqiyatli ({chat.title})\n"
    except Exception as e:
        status_text += f"⚠️ <b>Kanalga ulanishda xato:</b> {e}\n"

    await message.answer(status_text, parse_mode="HTML")

# ==================== 1. HUQUQIY YANGILIKLAR BO'LIMI ====================

@router.message(F.text == "⚖️ Huquqiy yangilik topish (AI)")
async def generate_legal_news_manual(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
        
    status_msg = await message.answer("🔍 <i>Adliya vazirligi va qonunchilik yangiliklari qidirilmoqda...</i>", parse_mode="HTML")
    
    news = await get_latest_legal_news()
    if not news:
        await status_msg.edit_text("Hozircha yangi huquqiy ma'lumot topilmadi. Keyinroq urinib ko'ring.")
        return
        
    await status_msg.edit_text("✍️ <i>AI advokatlik firmasi uslubida tahliliy post tayyorlamoqda...</i>", parse_mode="HTML")
    
    rewritten_text = await rewrite_news_with_ai(
        title=news["title"],
        description=news["description"],
        link=news["link"],
        source=news["source"]
    )
    
    user_id = message.from_user.id
    news_drafts[user_id] = {
        "title": news["title"],
        "text": rewritten_text,
        "link": news["link"],
        "source": news["source"],
        "media_type": "photo" if news.get("image_url") else "none",
        "media_file_id": news.get("image_url")
    }
    
    await status_msg.delete()
    
    # 30 daqiqadan keyingi vaqtni hisoblash
    target_dt = get_now() + timedelta(minutes=30)
    target_time_str = target_dt.strftime("%H:%M")
    full_target_time = target_dt.strftime("%Y-%m-%d %H:%M")
    
    await send_legal_post_confirmation(message.chat.id, user_id, bot, target_time_str, full_target_time)

async def send_legal_post_confirmation(chat_id: int, user_id: int, bot: Bot, target_time_str: str, full_target_time: str):
    draft = news_drafts.get(user_id)
    if not draft:
        return
        
    # Foydalanuvchi talab qilgan aynan 3 ta tugma
    buttons = [
        [
            InlineKeyboardButton(
                text=f"✅ {target_time_str} da post joylansin [Ruxsat berish]", 
                callback_data=f"auth_approve_{full_target_time}"
            )
        ],
        [
            InlineKeyboardButton(text="🚀 Hoziroq joylash", callback_data="auth_post_now")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="auth_cancel")
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    preview_header = "⚖️ <b>Yangi huquqiy post tayyorlandi:</b>\n" + "—" * 25 + "\n\n"
    full_text = preview_header + draft["text"]
    
    # Agar rasm bo'lsa rasm bilan, aks holda matn
    if draft["media_type"] == "photo" and draft["media_file_id"]:
        try:
            await bot.send_photo(chat_id, draft["media_file_id"], caption=full_text, reply_markup=markup, parse_mode="HTML")
            return
        except Exception:
            pass
            
    await bot.send_message(chat_id, full_text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)

# 1) Ruxsat berish -> 30 daqiqadan keyin chiqadi
@router.callback_query(F.data.startswith("auth_approve_"))
async def cb_auth_approve(call: CallbackQuery):
    full_target_time = call.data.replace("auth_approve_", "")
    user_id = call.from_user.id
    draft = news_drafts.get(user_id)
    
    if not draft:
        await call.message.answer("Qoralama topilmadi.")
        await call.answer()
        return
        
    add_scheduled_post(
        post_type="legal_news",
        caption=draft["text"],
        media_type=draft["media_type"],
        media_file_id=draft["media_file_id"],
        schedule_time=full_target_time
    )
    mark_news_processed(draft["link"], draft["title"])
    for aid in ADMIN_IDS:
        news_drafts.pop(aid, None)
    
    time_display = full_target_time.split(" ")[-1]
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        f"✅ <b>Ruxsat berildi!</b>\nPost <b>{time_display}</b> da (30 daqiqadan so'ng) @ahd_advokat kanaliga avtomatik joylanadi.",
        parse_mode="HTML"
    )
    await call.answer()

# 2) Hoziroq joylash
@router.callback_query(F.data == "auth_post_now")
async def cb_auth_post_now(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    draft = news_drafts.get(user_id)
    
    if not draft:
        await call.message.answer("Qoralama topilmadi.")
        await call.answer()
        return
        
    try:
        if draft["media_type"] == "photo" and draft["media_file_id"]:
            await bot.send_photo(CHANNEL_ID, draft["media_file_id"], caption=draft["text"], parse_mode="HTML")
        else:
            await bot.send_message(CHANNEL_ID, draft["text"], parse_mode="HTML")
            
        mark_news_processed(draft["link"], draft["title"])
        for aid in ADMIN_IDS:
            news_drafts.pop(aid, None)
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("🚀 <b>Post hoziroq @ahd_advokat kanaliga chiqarildi!</b>", parse_mode="HTML")
    except Exception as e:
        await call.message.answer(f"Kanalga yuborishda xatolik yuz berdi: {e}")
        
    await call.answer()

# 3) Bekor qilish
@router.callback_query(F.data == "auth_cancel")
async def cb_auth_cancel(call: CallbackQuery):
    for aid in ADMIN_IDS:
        news_drafts.pop(aid, None)
    await call.message.delete()
    await call.message.answer("❌ Post bekor qilindi.")
    await call.answer()

# Agar admin o'sha postga rasm/video qo'shmoqchi bo'lsa (shunchaki rasm yuborishi kifoya)
@router.message(F.photo | F.video)
async def handle_admin_media(message: Message, bot: Bot):
    user_id = message.from_user.id
    if user_id in news_drafts:
        if message.photo:
            news_drafts[user_id]["media_type"] = "photo"
            news_drafts[user_id]["media_file_id"] = message.photo[-1].file_id
        elif message.video:
            news_drafts[user_id]["media_type"] = "video"
            news_drafts[user_id]["media_file_id"] = message.video.file_id
            
        await message.answer("🖼 <b>Media yangilikka biriktirildi!</b>", parse_mode="HTML")
        target_dt = get_now() + timedelta(minutes=30)
        await send_legal_post_confirmation(
            message.chat.id, user_id, bot, 
            target_dt.strftime("%H:%M"), target_dt.strftime("%Y-%m-%d %H:%M")
        )

# ==================== 2. QO'LDA POST TAYYORLASH ====================

@router.message(F.text == "✍️ Qo'lda post tayyorlash")
async def start_manual_post(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
        
    await state.set_state(PostStates.waiting_for_manual_content)
    await message.answer(
        "✍️ <b>Kanalga chiqarmoqchi bo'lgan postni yuboring:</b>\n"
        "(Matn, rasm yoki video yuborishingiz mumkin. Bekor qilish uchun /cancel deb yozing)",
        parse_mode="HTML"
    )

@router.message(PostStates.waiting_for_manual_content)
async def process_manual_content(message: Message, state: FSMContext):
    user_id = message.from_user.id
    media_type = "none"
    media_file_id = None
    caption = message.html_text or ""
    
    if message.photo:
        media_type = "photo"
        media_file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        media_file_id = message.video.file_id
    elif message.animation:
        media_type = "animation"
        media_file_id = message.animation.file_id
        
    manual_drafts[user_id] = {
        "caption": caption,
        "media_type": media_type,
        "media_file_id": media_file_id
    }
    
    await state.set_state(PostStates.waiting_for_manual_time)
    await message.answer(
        "✅ <b>Post qabul qilindi!</b>\n\n"
        "Qachon kanalga joylashtirilsin? Masalan: <code>18:30</code>, <code>+45m</code> yoki <code>hozir</code> deb yozing:",
        parse_mode="HTML"
    )

@router.message(PostStates.waiting_for_manual_time)
async def process_manual_time(message: Message, state: FSMContext, bot: Bot):
    target_time = parse_schedule_time(message.text)
    if not target_time:
        await message.answer("Vaqt noto'g'ri. Masalan: <code>18:30</code> yoki <code>+30m</code> deb yozing.")
        return
        
    user_id = message.from_user.id
    draft = manual_drafts.get(user_id)
    if not draft:
        await message.answer("Post topilmadi.")
        await state.clear()
        return
        
    if message.text.strip().lower() in ["hozir", "now"]:
        try:
            if draft["media_type"] == "photo":
                await bot.send_photo(CHANNEL_ID, draft["media_file_id"], caption=draft["caption"], parse_mode="HTML")
            elif draft["media_type"] == "video":
                await bot.send_video(CHANNEL_ID, draft["media_file_id"], caption=draft["caption"], parse_mode="HTML")
            else:
                await bot.send_message(CHANNEL_ID, draft["caption"], parse_mode="HTML")
            await message.answer("🚀 <b>Post kanalga joylandi!</b>", parse_mode="HTML")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")
    else:
        add_scheduled_post(
            post_type="manual",
            caption=draft["caption"],
            media_type=draft["media_type"],
            media_file_id=draft["media_file_id"],
            schedule_time=target_time
        )
        await message.answer(f"🎉 <b>Post saqlandi!</b>\n⏰ Chiqarish vaqti: <b>{target_time}</b>", parse_mode="HTML")
        
    manual_drafts.pop(user_id, None)
    await state.clear()

# ==================== 3. REJADAGI POSTLAR ====================

@router.message(F.text == "📋 Rejadagi postlar")
async def show_upcoming(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    posts = get_upcoming_posts(limit=10)
    if not posts:
        await message.answer("Hozircha rejalashtirilgan postlar mavjud emas.")
        return
        
    text = "📋 <b>Rejadagi postlar:</b>\n\n"
    buttons = []
    for p in posts:
        preview = (p["caption"][:35] + "...") if p["caption"] else "[Media]"
        text += f"🔹 <b>#{p['id']}</b> | ⏰ <code>{p['schedule_time']}</code>\n"
        text += f"   <i>{preview}</i>\n\n"
        buttons.append([InlineKeyboardButton(text=f"🗑 #{p['id']} o'chirish", callback_data=f"del_{p['id']}")])
        
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.callback_query(F.data.startswith("del_"))
async def cb_delete_upcoming(call: CallbackQuery):
    post_id = int(call.data.replace("del_", ""))
    delete_scheduled_post(post_id)
    await call.message.answer(f"🗑 #{post_id} post o'chirildi.")
    await call.answer()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    news_drafts.pop(message.from_user.id, None)
    manual_drafts.pop(message.from_user.id, None)
    await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard())
