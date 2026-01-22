import streamlit as st
import subprocess
import pandas as pd
import os
import time
import requests # Yeni kütüphane

# --- GÜVENLİK ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Giriş Paneli")
    pwd = st.text_input("Özel Erişim Şifresi:", type="password")
    if st.button("Sisteme Giriş Yap"):
        if pwd == "üç": # ŞİFRENİ BURADAN GÜNCELLE
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Hatalı Şifre!")
    st.stop()

# --- TÜM TÜRKİYE VERİSİNİ ÇEKME ---
@st.cache_data # Veriyi her seferinde internetten çekmemesi için önbelleğe alır
def il_ilce_verisi_al():
    # Güvenilir bir kaynaktan Türkiye il-ilçe JSON verisi
    url = "https://raw.githubusercontent.com/fatihyigit/turkiye-iller-ilceler-json/master/data.json"
    try:
        response = requests.get(url)
        data = response.json()
        # Veriyi Streamlit'in anlayacağı {İl: [İlçeler]} formatına çevir
        il_dict = {}
        for item in data:
            il_adi = item["name"]
            ilceler = [ilce["name"] for ilce in item["districts"]]
            il_dict[il_adi] = ilceler
        return il_dict
    except:
        return {"İstanbul": ["Beşiktaş", "Şişli"]} # Hata durumunda yedek

turkiye_data = il_ilce_verisi_al()

st.title("📍 Google Maps E-posta Toplayıcı")

with st.sidebar:
    st.header("🔍 Arama Ayarları")
    sektor = st.text_input("Sektör (Örn: Hukuk Bürosu)", "Hukuk Bürosu")
    
    # Şehir seçimi (Alfabetik sıralı)
    sehirler = sorted(list(turkiye_data.keys()))
    sehir = st.selectbox("Şehir Seçin", sehirler)
    
    # İlçe seçimi (Seçilen şehre göre dinamik)
    ilceler = sorted(turkiye_data[sehir])
    ilce = st.selectbox("İlçe Seçin", ilceler)
    
    limit = st.slider("Firma Sayısı", 1, 50, 10)
    baslat = st.button("Taramayı Başlat 🚀")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 İşlem Logları")
    log_alani = st.empty()

if baslat:
    sorgu = f"{sehir} {ilce} {sektor}"
    with open("ayarlar.txt", "w", encoding="utf-8") as f:
        f.write(f"{sorgu}|{limit}")
    
    if os.path.exists("bot_log.txt"): os.remove("bot_log.txt")
    
    # Botu başlat
    process = subprocess.Popen(["python", "bot.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    while process.poll() is None:
        if os.path.exists("bot_log.txt"):
            with open("bot_log.txt", "r", encoding="utf-8") as f:
                log_alani.code(f.read())
        time.sleep(1)
    
    st.success("Tarama Tamamlandı!")

with col2:
    st.subheader("📊 Sonuçlar")
    if os.path.exists("firmalar_sonuc.csv"):
        df = pd.read_csv("firmalar_sonuc.csv", sep=';')
        st.dataframe(df)
        st.download_button("📥 Excel İndir", open("firmalar_sonuc.csv", "rb"), "sonuclar.csv")
