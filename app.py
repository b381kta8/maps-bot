import streamlit as st
import asyncio
import sys
import os
import subprocess

# --- BROWSER KURULUMU (CLOUD) ---
def install_playwright_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Install error: {e}")

if "browser_installed" not in st.session_state:
    with st.spinner("Sistem hazırlanıyor..."):
        install_playwright_browser()
        st.session_state["browser_installed"] = True

# --- GÜVENLİK ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if not st.session_state['authenticated']:
    st.set_page_config(page_title="Giriş", layout="centered")
    st.title("🔒 Giriş")
    pwd = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        if pwd == "üç":
            st.session_state['authenticated'] = True
            st.rerun()
        else: st.error("Hatalı şifre")
    st.stop()

# --- WINDOWS AYARI ---
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

# --- YARDIMCI FONKSİYONLAR ---
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
st.set_page_config(page_title="Google Maps Scraper Ultimate", layout="wide")

st.markdown("""
<div style="position: fixed; top: 65px; right: 20px; z-index: 99999; background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(10px); padding: 8px 16px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.4); font-size: 12px; font-weight: 600; color: #333; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
    🚀 Made by ÜÇ & AI
</div>""", unsafe_allow_html=True)

st.title("☁️ Google Maps Scraper (Katı Filtre Modu)")
st.caption("Sadece e-postası olanlar. Mükerrer yok. Liste sonuna kadar tarama.")

with st.sidebar:
    st.header("Parametreler")
    city = st.text_input("İl", "İstanbul")
    district = st.text_input("İlçe", "Kadıköy")
    keyword = st.text_input("Sektör", "Giyim Mağazası")
    max_target = st.number_input("Hedef Mail Sayısı", 1, 1000, 20)
    
    st.info(f"💡 {max_target} temiz mail bulmak için bot yaklaşık {max_target * 40} işletmeyi tarayacaktır. Lütfen sabırlı olun.")
    
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
    stat_candidates = st.metric("Toplanan Aday", 0)
    stat_emails = st.metric("✅ Kaydedilen Mail", len(st.session_state['results']))

with col2:
    result_table = st.empty()
    if st.session_state['results']:
        result_table.dataframe(pd.DataFrame(st.session_state['results']), use_container_width=True)

# --- ENGINE ---
if st.session_state.get('start_scraping', False):
    status_text.info("Bot başlatılıyor...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        try:
            # 1. HARİTA ARAMASI
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
            
            # 2. DEVASA HAVUZ TOPLAMA (ULTRA AGRESİF SCROLL)
            listings = []
            prev_cnt = 0
            fails = 0
            
            # Formül: 1 mail bulmak için ortalama 40-50 işletme gezmek gerekir.
            # Hedefin 50 katı kadar aday toplayalım ki garanti olsun.
            target_pool = max_target * 50 
            
            status_text.warning(f"Derin tarama yapılıyor... Hedef havuz: {target_pool} aday (Bu işlem uzun sürebilir)")
            
            while len(listings) < target_pool:
                if not st.session_state.get('start_scraping', False): break
                
                # Mouse Scroll
                page.hover('div[role="feed"]')
                page.mouse.wheel(0, 10000) # Daha sert scroll
                time.sleep(1)
                
                # Klavye "End" tuşu (Google Maps'i tetikler)
                page.keyboard.press("End")
                time.sleep(1)

                listings = page.locator('div[role="article"]').all()
                count = len(listings)
                stat_candidates.metric("Toplanan Aday", count)
                
                if count == prev_cnt:
                    fails += 1
                    status_text.text(f"Liste yükleniyor... ({fails}/15)")
                    
                    # Eğer takıldıysa yukarı aşağı yapıp "salla"
                    if fails > 5:
                        page.mouse.wheel(0, -1000)
                        time.sleep(0.5)
                        page.mouse.wheel(0, 5000)
                    
                    # 15 deneme boyunca sayı artmazsa, harita bitmiş demektir.
                    if fails > 15: 
                        status_text.info("Haritadaki tüm işletmeler yüklendi.")
                        break
                else: 
                    fails = 0
                
                prev_cnt = count

            status_text.success(f"{len(listings)} aday bulundu. Mail avı başlıyor...")
            
            # 3. ANALİZ VE FİLTRELEME
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
                    
                    # FİLTRE: Web sitesi yoksa direkt atla (Vakit kaybetme)
                    if not website: continue
                    
                    # FİLTRE: Mükerrer Site Kontrol
                    clean_url = website.rstrip("/")
                    if clean_url in st.session_state['processed_urls']: continue
                    st.session_state['processed_urls'].add(clean_url)
                    
                    # FİLTRE: Yasaklı Domainler
                    if any(b in website for b in BLOCKED_DOMAINS): continue

                    status_text.text(f"Taranıyor: {name}")
                    
                    # SİTEYE GİRİŞ
                    sp = context.new_page()
                    email = None
                    
                    try:
                        for attempt in range(2): 
                            try:
                                sp.goto(website, timeout=12000)
                                break
                            except: time.sleep(1)
                        
                        emails = extract_emails_from_page(sp)
                        if not emails:
                            for cl in sp.locator("a[href*='iletisim'], a[href*='contact'], a[href*='hakkimizda']").all():
                                lnk = cl.get_attribute("href")
                                if lnk:
                                    if not lnk.startswith("http"): lnk = website.rstrip("/") + "/" + lnk.lstrip("/")
                                    sp.goto(lnk, timeout=8000)
                                    emails = extract_emails_from_page(sp)
                                    if emails: break
                        
                        if emails:
                            for em in emails:
                                # FİLTRE: Bu mail listede var mı?
                                if em in [r['E-posta'] for r in st.session_state['results']]: continue
                                
                                # FİLTRE: Mail çalışıyor mu?
                                if verify_domain_mx(em):
                                    email = em
                                    break
                    except: pass
                    finally: sp.close()
                    
                    # SADECE MAIL VARSA KAYDET
                    if email:
                        st.session_state['results'].append({
                            "Firma İsmi": name,
                            "İl": city,
                            "İlçe": district,
                            "Telefon": phone,
                            "Web Sitesi": website,
                            "E-posta": email,
                            "Yöntem": "Web"
                        })
                        result_table.dataframe(pd.DataFrame(st.session_state['results']), use_container_width=True)
                        stat_emails.metric("✅ Kaydedilen Mail", len(st.session_state['results']))

                except: continue

        except Exception as e: st.error(f"Hata: {e}")
        finally:
            browser.close()
            if st.session_state['start_scraping']:
                st.session_state['start_scraping'] = False
