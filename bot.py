import os
import subprocess
import sys

# Sunucuda Playwright ve Chromium yoksa zorla kurar
try:
    import playwright
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

from playwright.sync_api import sync_playwright
# ... geri kalan kodların ...import os
# Sunucuda tarayıcı motorunu kurmak için kritik komut
os.system("playwright install chromium")

from playwright.sync_api import sync_playwright
import time
import re
import pandas as pd

def log_yaz(mesaj):
    with open("bot_log.txt", "a", encoding="utf-8") as f:
        f.write(mesaj + "\n")

def email_bul(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = list(set(re.findall(pattern, text)))
    return [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))]

def run():
    if os.path.exists("bot_log.txt"): os.remove("bot_log.txt")
    
    try:
        with open("ayarlar.txt", "r", encoding="utf-8") as f:
            ayar = f.read().split("|")
            arama_sorgusu, limit_sayisi = ayar[0], int(ayar[1])
    except:
        arama_sorgusu, limit_sayisi = "İstanbul Beşiktaş Giyim", 5

    with sync_playwright() as p:
        log_yaz("🌐 Tarayıcı motoru hazırlanıyor...")
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        page = context.new_page()
        
        log_yaz(f"🚀 Arama başlatıldı: {arama_sorgusu}")
        page.goto(f"https://www.google.com/maps/search/{arama_sorgusu.replace(' ', '+')}")
        time.sleep(5)

        listings = page.locator('a[href*="/maps/place/"]').all()
        log_yaz(f"📋 {len(listings)} firma bulundu.")
        
        veriler = []
        for i, listing in enumerate(listings[:limit_sayisi]):
            try:
                listing.click()
                time.sleep(3)
                isim = page.locator('h1').first.inner_text() if page.locator('h1').count() > 0 else "Bilinmiyor"
                log_yaz(f"🔍 ({i+1}) İnceleniyor: {isim}")
                
                web_el = page.locator('a[data-item-id="authority"]')
                web_url = web_el.get_attribute("href") if web_el.is_visible() else None
                
                mailler = []
                if web_url:
                    tp = context.new_page()
                    tp.goto(web_url, timeout=20000)
                    time.sleep(4)
                    mailler = email_bul(tp.content())
                    tp.close()
                
                if mailler: log_yaz(f"   ✅ Bulundu: {', '.join(mailler)}")
                veriler.append({"Firma": isim, "Web": web_url, "E-postalar": ", ".join(mailler)})
            except: continue

        pd.DataFrame(veriler).to_csv("firmalar_sonuc.csv", index=False, sep=';', encoding="utf-8-sig")
        log_yaz("✨ İşlem başarıyla tamamlandı.")
        browser.close()

if __name__ == "__main__":
    run()

