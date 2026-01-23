import streamlit as st
import pandas as pd
import re, time, os, subprocess, sys

# --- OTOMATİK KURULUM VE TARAYICI HAZIRLIĞI ---
def install_browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    # Sunucuda tarayıcı eksikse zorla indir (Hata almamak için kritik)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

def email_bul(html_content):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, html_content)
    yasakli = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', 'sentry', 'wixpress']
    return list(set([e.lower() for e in emails if not any(y in e.lower() for y in yasakli)]))

def tarama_yap(sorgu, limit):
    install_browser()
    from playwright.sync_api import sync_playwright
    sonuclar = []
    with sync_playwright() as p:
        st.info("🌐 Tarayıcı başlatılıyor, lütfen bekleyin...")
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()
        
        # Google Maps Arama
        page.goto(f"https://www.google.com/maps/search/{sorgu.replace(' ', '+')}", timeout=60000)
        time.sleep(5)

        for _ in range(2): # Kaydırma
            page.mouse.wheel(0, 2000)
            time.sleep(2)

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
                    try:
                        sp = context.new_page()
                        sp.goto(web_url, timeout=25000, wait_until="domcontentloaded")
                        time.sleep(4)
                        mailler = email_bul(sp.content())
                        
                        # E-posta bulamazsa derin tarama (İletişim sayfası)
                        if not mailler:
                            iletisim = sp.locator('a:has-text("İletişim"), a:has-text("Contact"), a:has-text("Bize Ulaşın")').first
                            if iletisim.is_visible():
                                iletisim.click()
                                time.sleep(3)
                                mailler = email_bul(sp.content())
                        sp.close()
                    except: pass
                
                if mailler: st.success(f"   ✅ Bulunan: {', '.join(mailler)}")
                sonuclar.append({"Firma": isim, "Web": web_url, "E-postalar": ", ".join(mailler)})
            except: continue
        browser.close()
    return sonuclar

# --- ARAYÜZ ---
st.set_page_config(page_title="Maps Bot", layout="wide")
st.title("📍 Profesyonel Google Maps Veri Botu")

with st.sidebar:
    st.header("🔍 Arama Filtreleri")
    sehir = st.text_input("Şehir (İsteğe bağlı):", "İstanbul")
    ilce = st.text_input("İlçe (İsteğe bağlı):", "Beşiktaş")
    sektor = st.text_input("Sektör:", "Hukuk Bürosu")
    limit = st.slider("Limit:", 1, 50, 10)
    basla = st.button("Taramayı Başlat 🚀")

if basla:
    veriler = tarama_yap(f"{sehir} {ilce} {sektor}".strip(), limit)
    if veriler:
        df = pd.DataFrame(veriler)
        st.dataframe(df)
        st.download_button("📥 Excel İndir", df.to_csv(index=False, sep=';').encode('utf-8-sig'), "sonuc.csv")
