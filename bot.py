from playwright.sync_api import sync_playwright
import time
import re
import pandas as pd
import os

def log_yaz(mesaj):
    with open("bot_log.txt", "a", encoding="utf-8") as f:
        f.write(mesaj + "\n")

def email_bul(html_content):
    # Hem metin hem de gizli mailto linklerini yakalar
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = set(re.findall(pattern, html_content))
    temiz = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'))]
    return list(set(temiz))

def run():
    if os.path.exists("bot_log.txt"): os.remove("bot_log.txt")
    
    try:
        with open("ayarlar.txt", "r", encoding="utf-8") as f:
            ayar = f.read().split("|")
            arama_sorgusu, limit_sayisi = ayar[0], int(ayar[1])
    except:
        arama_sorgusu, limit_sayisi = "İstanbul Hukuk Büroları", 10

    with sync_playwright() as p:
        # Bot engellerini aşmak için tarayıcıyı daha gerçekçi başlatıyoruz
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        log_yaz(f"🚀 Derin Tarama Başladı: {arama_sorgusu}")
        page.goto(f"https://www.google.com/maps/search/{arama_sorgusu.replace(' ', '+')}")
        time.sleep(5)

        # Liste Kaydırma
        page.hover('div[role="feed"]')
        for _ in range(3):
            page.mouse.wheel(0, 3000)
            time.sleep(2)

        listings = page.locator('a[href*="/maps/place/"]').all()
        veriler = []

        for i, listing in enumerate(listings[:limit_sayisi]):
            try:
                isim = listing.get_attribute("aria-label")
                log_yaz(f"🔍 ({i+1}/{limit_sayisi}) {isim}")
                listing.click()
                time.sleep(3)
                
                web_el = page.locator('a[data-item-id="authority"]')
                web_url = web_el.get_attribute("href") if web_el.is_visible() else None
                
                tel = "Bilinmiyor"
                tel_el = page.locator('button[data-item-id^="phone:tel:"]')
                if tel_el.is_visible(): tel = tel_el.get_attribute("data-item-id").split(":")[-1]
                
                mailler = set()
                if web_url:
                    try:
                        # Her site için yeni ve tertemiz bir sekme
                        temp_page = context.new_page()
                        # 'wait_until' kaldırıldı, bazen siteler sonsuza kadar yükleniyor
                        temp_page.goto(web_url, timeout=25000)
                        time.sleep(6) # İçeriğin gelmesi için sabırla bekle
                        
                        # 1. Ana sayfayı tara
                        for m in email_bul(temp_page.content()): mailler.add(m)
                        
                        # 2. Eğer mail yoksa alt sayfaları (İletişim/Hakkımızda) daha agresif ara
                        if not mailler:
                            # Sayfadaki tüm linkleri bul
                            links = temp_page.locator("a").all()
                            alt_sayfa_url = None
                            for link in links:
                                h = (link.get_attribute("href") or "").lower()
                                t = (link.inner_text() or "").lower()
                                if any(x in h or x in t for x in ["iletisim", "contact", "ulasin", "about", "hakkimizda"]):
                                    alt_sayfa_url = h if h.startswith("http") else web_url.rstrip("/") + "/" + h.lstrip("/")
                                    break # İlk bulduğunu al
                            
                            if alt_sayfa_url:
                                temp_page.goto(alt_sayfa_url, timeout=15000)
                                time.sleep(3)
                                for m in email_bul(temp_page.content()): mailler.add(m)

                        temp_page.close()
                    except:
                        pass
                
                if mailler:
                    log_yaz(f"   ✅ Mailler: {', '.join(mailler)}")
                else:
                    log_yaz("   ❌ E-posta bulunamadı (Bot engeli veya mail yok).")
                
                veriler.append({"Firma Adı": isim, "Telefon": tel, "Web Sitesi": web_url, "E-postalar": ", ".join(mailler)})
            except:
                continue

        pd.DataFrame(veriler).to_csv("firmalar_sonuc.csv", index=False, sep=';', encoding="utf-8-sig")
        log_yaz("✨ Tarama tamamlandı.")
        browser.close()

if __name__ == "__main__":
    run()