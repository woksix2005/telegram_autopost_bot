from datetime import timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import CHANNEL_ID, ADMIN_IDS, TIMEZONE
from database import get_due_posts, mark_post_status
from time_utils import get_now
from news_service import get_latest_legal_news
from ai_service import rewrite_news_with_ai

scheduler = AsyncIOScheduler(timezone=TIMEZONE)

async def check_and_publish_due_posts(bot: Bot):
    """Har 30 soniyada vaqti yetgan postlarni kanalga chiqaradi"""
    current_time_str = get_now().strftime("%Y-%m-%d %H:%M")
    due_posts = get_due_posts(current_time_str)
    
    if not due_posts or not CHANNEL_ID:
        return

    for post in due_posts:
        post_id = post["id"]
        media_type = post["media_type"]
        media_file_id = post["media_file_id"]
        caption = post["caption"]
        
        try:
            if media_type == "photo" and media_file_id:
                await bot.send_photo(CHANNEL_ID, media_file_id, caption=caption, parse_mode="HTML")
            elif media_type == "video" and media_file_id:
                await bot.send_video(CHANNEL_ID, media_file_id, caption=caption, parse_mode="HTML")
            elif media_type == "animation" and media_file_id:
                await bot.send_animation(CHANNEL_ID, media_file_id, caption=caption, parse_mode="HTML")
            else:
                await bot.send_message(CHANNEL_ID, caption, parse_mode="HTML")
                
            mark_post_status(post_id, "sent")
            
            # Barcha adminlarga xabar berish
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id, 
                        f"📢 <b>Post #{post_id} rejalashtirilgan vaqtda @ahd_advokat kanaliga muvaffaqiyatli joylandi!</b>",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"Post #{post_id} yuborishda xatolik: {e}")
            mark_post_status(post_id, f"failed: {str(e)[:50]}")
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, f"⚠️ Post #{post_id} yuborilmadi. Xatolik: {e}")
                except Exception:
                    pass

async def auto_legal_news_job(bot: Bot):
    """Har 3 soatda yangi huquqiy post topib, chiqishidan 30 daqiqa oldin barcha adminlarga taklif qilish"""
    if not ADMIN_IDS:
        return
        
    try:
        news = await get_latest_legal_news()
        if not news:
            return
            
        rewritten_text = await rewrite_news_with_ai(
            title=news["title"],
            description=news["description"],
            link=news["link"],
            source=news["source"]
        )
        
        from handlers import news_drafts, send_legal_post_confirmation
        
        target_dt = get_now() + timedelta(minutes=30)
        target_time_str = target_dt.strftime("%H:%M")
        full_target_time = target_dt.strftime("%Y-%m-%d %H:%M")
        
        # Barcha adminlarga qoralama saqlash va xabar yuborish
        for admin_id in ADMIN_IDS:
            news_drafts[admin_id] = {
                "title": news["title"],
                "text": rewritten_text,
                "link": news["link"],
                "source": news["source"],
                "media_type": "photo" if news.get("image_url") else "none",
                "media_file_id": news.get("image_url")
            }
            try:
                await bot.send_message(
                    admin_id, 
                    "⚖️ <b>Yangi huquqiy ma'lumot tayyorlandi!</b> (30 daqiqadan so'ng kanalga chiqadi)",
                    parse_mode="HTML"
                )
                await send_legal_post_confirmation(admin_id, admin_id, bot, target_time_str, full_target_time)
            except Exception as e:
                print(f"Admin {admin_id} ga xabar yuborishda xatolik: {e}")
                
    except Exception as e:
        print(f"Avtomatik huquqiy post jarayonida xatolik: {e}")

def start_scheduler(bot: Bot):
    # Har 30 soniyada rejadagi postlarni tekshirish
    scheduler.add_job(
        check_and_publish_due_posts, 
        "interval", 
        seconds=30, 
        args=[bot]
    )
    
    # Har 3 soatda huquqiy yangilik qidirish (kunduzi 08:30, 11:30, 14:30, 17:30, 20:30 da)
    scheduler.add_job(
        auto_legal_news_job,
        "cron",
        hour="8,11,14,17,20",
        minute=30,
        args=[bot]
    )
    
    scheduler.start()
