import streamlit as st
import pandas as pd
import re
import time
import os
import subprocess
import sys

# --- OTOMATİK KURULUM VE TARAYICI HAZIRLIĞI ---
def install_browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    # Sunucuda tarayıcı eksikse zorla indir
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

def email_bul(html_content):
    # Regex: Metin ve mailto linklerini kapsar
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, html_content)
    # Gereksiz dosyaları ve sahte eşleşmeleri temizle
    yasakli = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', 'sentry.io', 'wixpress.com']
    temiz = [e.lower() for e in emails if not any(y in e.lower() for y in yasakli)]
    return list(set(temiz))

def tarama_yap(sorgu, limit):
    install_browser()
    from playwright.sync_api import sync_playwright
    
    sonuclar = []
    with sync_playwright() as p:
        st.info("🌐 Tarayıcı başlatılıyor, lütfen bekleyin...")
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        page = context.new_page()
        
        # Google Maps Arama
        maps_url = f"https://www.google.com/maps/search/{sorgu.replace(' ', '+')}"
        page.goto(maps_url, timeout=60000)
        time.sleep(5)

        # Liste kaydırma (Daha fazla sonuç için)
        for _ in range(2):
            page.mouse.wheel(0, 2000)
            time.sleep(2)

        listings = page.locator('a[href*="/maps/place/"]').all()
        st.write(f"📋 {len(listings)} firma bulundu. İlk {limit} tanesi taranıyor...")

        for i, item in enumerate(listings[:limit]):
            try:
                item.click()
                time.sleep(3)
                
                # Firma Adı
                isim = page.locator('h1').first.inner_text() if page.locator('h1').count() > 0 else "Bilinmiyor"
                st.write(f"🔍 {i+1}. İnceleniyor: **{isim}**")
                
                # Web Sitesi
                web_el = page.locator('a[data-item-id="authority"]')
                web_url = web_el.get_attribute("href") if web_el.is_visible() else None
                
                mailler = []
                if web_url:
                    try:
                        sp = context.new_page()
                        sp.goto(web_url, timeout=25000, wait_until="domcontentloaded")
                        time.sleep(4)
                        
                        # 1. Aşama: Ana Sayfa Taraması
                        mailler = email_bul(sp.content())
                        
                        # 2. Aşama: Alt Sayfa Taraması (E-posta bulamazsa)
                        if not mailler:
                            # İletişim linklerini ara
                            iletisim_btn = sp.locator('a:has-text("İletişim"), a:has-text("Contact"), a:has-text("Bize Ulaşın"), a:has-text("iletisim")').first
                            if iletisim_btn.is_visible():
                                iletisim_btn.click()
                                time.sleep(3)
                                mailler = email_bul(sp.content())
                        sp.close()
                    except:
                        pass
                
                if mailler:
                    st.success(f"   ✅ Bulunanlar: {', '.join(mailler)}")
                
                sonuclar.append({"Firma": isim, "Web": web_url, "E-postalar": ", ".join(mailler)})
            except:
                continue
        
        browser.close()
    return sonuclar

# --- ARAYÜZ ---
st.set_page_config(page_title="Maps E-posta Botu", layout="wide")
st.title("📍 Profesyonel Veri Toplama Botu")

if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.sidebar.text_input("Şifre:", type="password")
    if st.sidebar.button("Giriş"):
        if pwd == "123456": st.session_state.auth = True; st.rerun()
    st.stop()

with st.sidebar:
    st.header("Arama Filtreleri")
    sehir = st.text_input("Şehir (Opsiyonel):", "İstanbul")
    ilce = st.text_input("İlçe (Opsiyonel):", "Beşiktaş")
    sektor = st.text_input("Sektör / Firma Türü:", "Hukuk Bürosu")
    limit = st.slider("Firma Limiti:", 1, 50, 10)
    baslat = st.button("Taramayı Başlat 🚀")

if baslat:
    tam_sorgu = f"{sehir} {ilce} {sektor}".strip()
    if sektor:
        veriler = tarama_yap(tam_sorgu, limit)
        if veriler:
            st.success("İşlem Tamamlandı!")
            df = pd.DataFrame(veriler)
            st.dataframe(df)
            st.download_button("📥 Excel Olarak İndir", df.to_csv(index=False, sep=';').encode('utf-8-sig'), "sonuc.csv")
    else:
        st.warning("En azından bir 'Sektör' belirtmelisiniz.")
