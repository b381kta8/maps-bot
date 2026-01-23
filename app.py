import streamlit as st
import pandas as pd
import re, time, os, subprocess, sys

# --- OTOMATİK KURULUM ---
def install_browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

# --- GELİŞMİŞ E-POSTA BULUCU ---
def email_bul(html):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, html)
    yasakli = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', 'wixpress', 'sentry']
    return list(set([e.lower() for e in emails if not any(y in e.lower() for y in yasakli)]))

def tarama_yap(sorgu, limit):
    install_browser()
    from playwright.sync_api import sync_playwright
    sonuclar = []
    with sync_playwright() as p:
        st.info("🌐 Tarayıcı hazırlanıyor...")
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()
        
        page.goto(f"https://www.google.com/maps/search/{sorgu.replace(' ', '+')}", timeout=60000)
        time.sleep(5)

        listings = page.locator('a[href*="/maps/place/"]').all()
        st.write(f"📋 {len(listings)} firma bulundu. {limit} tanesi taranıyor...")

        for i, item in enumerate(listings[:limit]):
            try:
                item.click()
                time.sleep(3)
                isim = page.locator('h1').first.inner_text()
                st.write(f"🔍 {i+1}. İnceleniyor: **{isim}**")
                
                web_el = page.locator('a[data-item-id="authority"]')
                web_url = web_el.get_attribute("href") if web_el.is_visible() else None
                
                mailler = []
                if web_url:
                    sp = context.new_page()
                    sp.goto(web_url, timeout=20000, wait_until="domcontentloaded")
                    time.sleep(4)
                    mailler = email_bul(sp.content())
                    
                    if not mailler: # Mail yoksa iletişim sayfasına bak
                        iletisim = sp.locator('a:has-text("İletişim"), a:has-text("Contact"), a:has-text("Bize Ulaşın")').first
                        if iletisim.is_visible():
                            iletisim.click()
                            time.sleep(3)
                            mailler = email_bul(sp.content())
                    sp.close()
                
                if mailler: st.success(f"   ✅ Bulunan: {', '.join(mailler)}")
                sonuclar.append({"Firma": isim, "Web": web_url, "E-postalar": ", ".join(mailler)})
            except: continue
        browser.close()
    return sonuclar

# --- ARAYÜZ ---
st.set_page_config(page_title="Maps Bot", layout="wide")
st.title("📍 Profesyonel Maps E-posta Botu")

with st.sidebar:
    st.header("🔍 Arama Filtreleri")
    sehir = st.text_input("Şehir (İsteğe bağlı):", "İstanbul")
    ilce = st.text_input("İlçe (İsteğe bağlı):", "Beşiktaş")
    sektor = st.text_input("Sektör:", "Hukuk Bürosu")
    limit = st.slider("Limit:", 1, 50, 10)
    basla = st.button("Taramayı Başlat 🚀")

if basla:
    tam_sorgu = f"{sehir} {ilce} {sektor}".strip()
    veriler = tarama_yap(tam_sorgu, limit)
    if veriler:
        df = pd.DataFrame(veriler)
        st.dataframe(df)
        st.download_button("📥 Excel İndir", df.to_csv(index=False, sep=';').encode('utf-8-sig'), "sonuc.csv")
