import streamlit as st
import asyncio
import sys
import os
import subprocess

# --- BROWSER SETUP (CLOUD) ---
def install_playwright_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("Browser installed.")
    except Exception as e:
        print(f"Install error: {e}")

if "browser_installed" not in st.session_state:
    with st.spinner("Sistem hazırlanıyor..."):
        install_playwright_browser()
        st.session_state["browser_installed"] = True

# --- LOGIN ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if not st.session_state['authenticated']:
    st.set_page_config(page_title="Giriş", layout="centered")
    st.title("🔒 Giriş")
    pwd = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        if pwd == "üç":
            st.session_state['authenticated'] = True
            st.rerun()
        else: st.error("Yanlış şifre")
    st.stop()

# --- WINDOWS FIX ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time
import dns.resolver

# --- AYARLAR ---
BLOCKED_DOMAINS = ["facebook.com", "instagram.com", "twitter.com", "linkedin.com", "youtube.com", "pinterest.com", "trendyol.com", "hepsiburada.com", "n11.com", "amazon.com"]

if 'results' not in st.session_state: st.session_state['results'] = []
if 'processed_urls' not in st.session_state: st.session_state['processed_urls'] = set()

# --- FONKSIYONLAR ---
def verify_domain_mx(email):
    try:
        dns.resolver.resolve(email.split('@')[1], 'MX')
        return True
    except: return False

def clean_obfuscated_email(text):
    return text.replace(" [at] ", "@").replace("(at)", "@").replace(" at ", "@").replace(" [dot] ", ".").replace("(dot)", ".").replace(" dot ", ".")

def extract_emails_from_page(page):
    found = set()
    try:
        for link in page.locator("a[href^='mailto:']").all():
            href = link.get_attribute("href")
            if href and "@" in href: found.add(href.replace("mailto:", "").split("?")[0].strip())
        
        content = clean_obfuscated_email(page.content())
        for email in re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(?!png|jpg|jpeg|gif|css|js)[a-zA-Z]{2,}', content):
            if len(email) < 50: found.add(email)
    except: pass
    return list(found)

def convert_df(df):
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Firmalar')
    return output.getvalue()

# --- ARAYÜZ ---
st.set_page_config(page_title="Google Maps Scraper Pro", layout="wide")

st.markdown("""
<div style="position: fixed; top: 65px; right: 20px; z-index: 99999; background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(10px); padding: 8px 16px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.4); font-size: 12px; font-weight: 600; color: #333; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
    🚀 Made by ÜÇ & AI
</div>""", unsafe_allow_html=True)

st.title("☁️ Google Maps Scraper (Gelişmiş Mod)")

with st.sidebar:
    st.header("Parametreler")
    city = st.text_input("İl", "İstanbul")
    district = st.text_input("İlçe", "Kadıköy")
    keyword = st.text_input("Sektör", "Giyim Mağazası")
    max_target = st.number_input("Hedef Firma Sayısı", 1, 1000, 50)
    
    st.divider()
    # YENİ ÖZELLİK: ESNEK KAYIT
    save_without_mail = st.checkbox("E-postası olmayanları da kaydet (Telefon için)", value=True)
    st.caption("İşaretlerseniz, mail bulunamasa bile firma listeye eklenir. Böylece listeniz çok daha hızlı dolar.")
    
    st.divider()
    if st.button("Başlat", type="primary"):
        st.session_state['start_scraping'] = True
        st.session_state['results'] = []
        st.session_state['processed_urls'] = set()
    
    if st.button("Durdur"):
        st.session_state['start_scraping'] = False
        
    if len(st.session_state['results']) > 0:
        df = pd.DataFrame(st.session_state['results'])
        st.download_button("📥 İndir", convert_df(df), "sonuc.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

col1, col2 = st.columns([1, 2])
with col1:
    status_text = st.empty()
    progress_bar = st.progress(0)
    st.divider()
    stat_total = st.metric("✅ Toplam Kayıt", len(st.session_state['results']))

with col2:
    result_table = st.empty()
    if st.session_state['results']:
        result_table.dataframe(pd.DataFrame(st.session_state['results']), use_container_width=True)

# --- ENGINE ---
if st.session_state.get('start_scraping', False):
    status_text.info("Başlatılıyor...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        try:
            # ARAMA
            search_term = f"{city} {district} {keyword}"
            page.goto("https://www.google.com/maps?hl=tr", timeout=60000)
            try: page.get_by_role("button", name="Tümünü kabul et").click(timeout=3000)
            except: pass

            try:
                sb = page.locator("input#searchboxinput").or_(page.locator("input[name='q']")).first
                sb.wait_for(state="visible", timeout=30000)
                sb.fill(search_term)
                page.keyboard.press("Enter")
            except: st.error("Arama kutusu hatası"); st.stop()
            
            page.wait_for_selector('div[role="feed"]', timeout=30000)
            
            # AGRESİF SCROLL (Daha fazla aday toplamak için)
            listings = []
            prev_cnt = 0
            fails = 0
            # E-posta bulma oranı %10 ise, 100 hedef için 1000 aday gerekir.
            # Hedefin 20 katı kadar aday toplamaya çalışalım.
            target_pool = max_target * 20 
            
            status_text.warning(f"Havuz dolduruluyor... Hedef havuz: {target_pool} aday")
            
            while len(listings) < target_pool:
                if not st.session_state.get('start_scraping', False): break
                
                page.hover('div[role="feed"]')
                page.mouse.wheel(0, 5000)
                time.sleep(1.5)
                
                # Bazen yukarı aşağı yapmak yüklemeyi tetikler
                if len(listings) % 50 == 0:
                    page.mouse.wheel(0, -1000)
                    time.sleep(0.5)
                    page.mouse.wheel(0, 5000)

                listings = page.locator('div[role="article"]').all()
                status_text.text(f"Havuz: {len(listings)} işletme")
                
                if len(listings) == prev_cnt:
                    fails += 1
                    if fails > 8: break # 8 deneme boyunca artmazsa son
                else: fails = 0
                prev_cnt = len(listings)

            status_text.success(f"{len(listings)} aday bulundu. Analiz başlıyor...")
            
            # ANALİZ
            for listing in listings:
                if len(st.session_state['results']) >= max_target:
                    st.success("Hedefe ulaşıldı!"); st.session_state['start_scraping'] = False; break
                if not st.session_state.get('start_scraping', False): break
                
                progress_bar.progress(min(len(st.session_state['results']) / max_target, 1.0))
                
                try:
                    listing.click()
                    time.sleep(1)
                    
                    name = "Bilinmiyor"; website = None; phone = None
                    try: name = page.locator('h1.DUwDvf').first.inner_text()
                    except: pass
                    
                    try: 
                        wb = page.locator('[data-item-id="authority"]').first
                        if wb.count() > 0: website = wb.get_attribute("href")
                    except: pass
                    
                    try:
                        pb = page.locator('[data-item-id^="phone:"]').first
                        if pb.count() > 0: phone = pb.get_attribute("aria-label").replace("Telefon: ", "")
                    except: pass
                    
                    # Mükerrer Kontrol
                    clean_url = website.rstrip("/") if website else name
                    if clean_url in st.session_state['processed_urls']: continue
                    st.session_state['processed_urls'].add(clean_url)
                    
                    if website and any(b in website for b in BLOCKED_DOMAINS): continue

                    status_text.text(f"İnceleniyor: {name}")
                    
                    email = None
                    method = "-"
                    
                    # WEB SİTESİ VARSA MAİL ARA
                    if website:
                        sp = context.new_page()
                        try:
                            sp.goto(website, timeout=12000)
                            emails = extract_emails_from_page(sp)
                            
                            if not emails:
                                # İletişim sayfalarına bak
                                for cl in sp.locator("a[href*='iletisim'], a[href*='contact']").all():
                                    lnk = cl.get_attribute("href")
                                    if lnk:
                                        if not lnk.startswith("http"): lnk = website.rstrip("/") + "/" + lnk.lstrip("/")
                                        sp.goto(lnk, timeout=8000)
                                        emails = extract_emails_from_page(sp)
                                        if emails: break
                            
                            if emails:
                                for em in emails:
                                    if em not in [r['E-posta'] for r in st.session_state['results']]:
                                        if verify_domain_mx(em):
                                            email = em; method = "Web Sitesi"; break
                        except: pass
                        finally: sp.close()
                    
                    # KAYIT KARARI
                    should_save = False
                    
                    if email:
                        should_save = True
                    elif save_without_mail: 
                        # Mail yok ama kullanıcı "Hepsini kaydet" dediyse
                        should_save = True
                        email = "-" # Mail yoksa tire koy
                        method = "Sadece Telefon"

                    if should_save:
                        st.session_state['results'].append({
                            "Firma İsmi": name,
                            "İl": city,
                            "İlçe": district,
                            "Telefon": phone,
                            "Web Sitesi": website,
                            "E-posta": email,
                            "Yöntem": method
                        })
                        result_table.dataframe(pd.DataFrame(st.session_state['results']), use_container_width=True)
                        stat_total.metric("✅ Toplam Kayıt", len(st.session_state['results']))

                except: continue

        except Exception as e: st.error(f"Hata: {e}")
        finally:
            browser.close()
            if st.session_state['start_scraping']:
                st.session_state['start_scraping'] = False
