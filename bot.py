import os
os.system("playwright install chromium")
import os
# Sunucuda tarayıcı kurulumunu tetiklemek için kritik satır
os.system("playwright install chromium")

from playwright.sync_api import sync_playwright
# ... (kodun geri kalanı aynı)

import os
import subprocess

# Sunucuda playwright eksikse kurmaya zorlar
os.system("playwright install chromium")

from playwright.sync_api import sync_playwright
import time
import re
import pandas as pd
import os

def log_yaz(mesaj):
    with open("bot_log.txt", "a", encoding="utf-8") as f:
        f.write(mesaj + "\n")

def email_bul(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = list(set(re.findall(pattern, text)))
    temiz = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))]
    return list(set(temiz))

def run():
    if os.path.exists("bot_log.txt"): os.remove("bot_log.txt")
    
    try:
        with open("ayarlar.txt", "r", encoding="utf-8") as f:
            ayar = f.read().split("|")
            arama_sorgusu, limit_sayisi = ayar[0], int(ayar[1])
    except:
        arama_sorgusu, limit_sayisi = "İstanbul Beşiktaş Giyim", 10

    with sync_playwright() as p:
        log_yaz("🌐 Tarayıcı motoru hazırlanıyor...")
        # Sunucu uyumluluğu için chromium ayarları
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        page = context.new_page()
        
        log_yaz(f"🚀 Arama başlatıldı: {arama_sorgusu}")
        try:
            page.goto(f"https://www.google.com/maps/search/{arama_sorgusu.replace(' ', '+')}", timeout=60000)
            time.sleep(5)

            # Kaydırma işlemi
            for _ in range(2):
                page.mouse.wheel(0, 2000)
                time.sleep(2)

            listings = page.locator('a[href*="/maps/place/"]').all()
            log_yaz(f"📋 {len(listings)} firma bulundu.")
            
            veriler = []
            for i, listing in enumerate(listings[:limit_sayisi]):
                try:
                    listing.click()
                    time.sleep(3)
                    
                    # Firma ismini çekme (Güncel seçici)
                    isim = page.locator('h1').first.inner_text() if page.locator('h1').count() > 0 else "Bilinmiyor"
                    log_yaz(f"🔍 ({i+1}) İnceleniyor: {isim}")
                    
                    web_el = page.locator('a[data-item-id="authority"]')
                    web_url = web_el.get_attribute("href") if web_el.is_visible() else None
                    
                    mailler = []
                    if web_url:
                        temp_page = context.new_page()
                        temp_page.goto(web_url, timeout=20000)
                        time.sleep(4)
                        mailler = email_bul(temp_page.content())
                        temp_page.close()
                    
                    if mailler: log_yaz(f"   ✅ Bulundu: {', '.join(mailler)}")
                    veriler.append({"Firma": isim, "Web": web_url, "E-postalar": ", ".join(mailler)})
                except: continue

            pd.DataFrame(veriler).to_csv("firmalar_sonuc.csv", index=False, sep=';', encoding="utf-8-sig")
            log_yaz("✨ İşlem başarıyla tamamlandı.")
        except Exception as e:
            log_yaz(f"❌ Hata oluştu: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    run()



