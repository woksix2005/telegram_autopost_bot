import aiohttp
import random
import re
import feedparser
from bs4 import BeautifulSoup
from database import is_news_processed

LEGAL_KEYWORDS = [
    "qonun", "qaror", "farmon", "sud", "jazo", "jinoyat", "ma'muriy", 
    "advokat", "huquq", "modda", "jarima", "vazirlik", "kompensatsiya", 
    "fuqaro", "mehnat", "aliment", "meros", "mulk", "prokuratura", 
    "ichki ishlar", "adliya", "notarius", "shartnoma", "soliq", "qamoq", 
    "kodeks", "tartib", "belgilandi", "ruxsat", "taqiqlandi", "majburiy", 
    "guvohnoma", "pasport", "idorasi", "amaliyot", "boshqarma"
]

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ").strip()

def is_legal_topic(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in LEGAL_KEYWORDS)

async def fetch_adliya_posts():
    """Adliya vazirligining rasmiy @huquqiyaxborot kanalidan so'nggi huquqiy postlarni oladi"""
    url = "https://t.me/s/huquqiyaxborot"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    posts = []
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    msgs = soup.find_all("div", class_="tgme_widget_message")
                    
                    for m in reversed(msgs):
                        text_el = m.find("div", class_="tgme_widget_message_text")
                        if not text_el:
                            continue
                            
                        text = text_el.get_text(separator="\n").strip()
                        post_id = m.get("data-post")
                        if not post_id:
                            continue
                            
                        link = f"https://t.me/{post_id}"
                        if is_news_processed(link):
                            continue
                            
                        # Birinchi qatorni sarlavha sifatida olamiz
                        lines = [line.strip() for line in text.split("\n") if line.strip()]
                        title = lines[0] if lines else "Huquqiy ma'lumot"
                        if len(title) > 100:
                            title = title[:97] + "..."
                            
                        # Rasm tekshirish
                        image_url = None
                        photo = m.find("a", class_="tgme_widget_message_photo_wrap")
                        if photo and "background-image" in photo.get("style", ""):
                            match = re.search(r"url\(['\"]?(.*?)['\"]?\)", photo["style"])
                            if match:
                                image_url = match.group(1)
                                
                        posts.append({
                            "title": title,
                            "description": text,
                            "link": link,
                            "image_url": image_url,
                            "source": "Adliya vazirligi (@huquqiyaxborot)"
                        })
    except Exception as e:
        print(f"Adliya kanalidan yuklashda xatolik: {e}")
        
    return posts

async def fetch_kun_uz_legal_posts():
    """Kun.uz ning faqat huquqiy mavzudagi yangiliklarini oladi"""
    url = "https://kun.uz/news/rss"
    headers = {"User-Agent": "Mozilla/5.0"}
    posts = []
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries:
                        link = getattr(entry, "link", "").strip()
                        title = getattr(entry, "title", "").strip()
                        raw_desc = getattr(entry, "summary", "") or getattr(entry, "description", "")
                        desc = clean_html(raw_desc)
                        
                        if not link or not title:
                            continue
                        if is_news_processed(link):
                            continue
                            
                        # FAQAT huquqiy mavzu bo'lsa qabul qilamiz
                        full_content = f"{title} {desc}"
                        if not is_legal_topic(full_content):
                            continue
                            
                        # Rasm URL
                        image_url = None
                        if hasattr(entry, "enclosures") and entry.enclosures:
                            for enc in entry.enclosures:
                                if enc.get("type", "").startswith("image/"):
                                    image_url = enc.get("href")
                                    break
                                    
                        posts.append({
                            "title": title,
                            "description": desc,
                            "link": link,
                            "image_url": image_url,
                            "source": "Kun.uz (Huquqiy bo'lim)"
                        })
    except Exception as e:
        print(f"Kun.uz huquqiy yangiliklarida xatolik: {e}")
        
    return posts

async def get_latest_legal_news():
    """
    Huquqiy yangiliklarni random rotatsiya bilan topadi:
    Ko'pincha Adliya vazirligidan, shuningdek Kun.uz huquqiy yangiliklaridan.
    """
    # 70% ehtimollik bilan birinchi Adliya vazirligidan qidiradi
    sources = [fetch_adliya_posts, fetch_kun_uz_legal_posts]
    if random.random() < 0.7:
        first_source, second_source = sources[0], sources[1]
    else:
        first_source, second_source = sources[1], sources[0]
        
    results = await first_source()
    if results:
        return results[0]
        
    results = await second_source()
    if results:
        return results[0]
        
    return None
