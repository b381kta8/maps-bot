import streamlit as st

# Şifre Kontrolü
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.title("🔒 Giriş Yapın")
        pwd = st.text_input("Şifreyi Giriniz:", type="password")
        if st.button("Giriş"):
            if pwd == "ozel_sifrem_123": # Burayı istediğin şifreyle değiştir
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Hatalı şifre!")
        return False
    return True

if not check_password():
    st.stop()

import streamlit as st
import subprocess
import pandas as pd
import os
import time

st.set_page_config(page_title="Maps Scraper", page_icon="📍", layout="wide")

# Şehir-İlçe Verisi
data = {
    "İstanbul": ["Beşiktaş", "Şişli", "Kadıköy", "Fatih", "Esenyurt", "Beyoğlu"],
    "Ankara": ["Çankaya", "Keçiören", "Yenimahalle"],
    "İzmir": ["Konak", "Bornova", "Karşıyaka"]
}

st.title("📍 Google Maps E-posta Toplayıcı")

with st.sidebar:
    st.header("🔍 Arama Ayarları")
    sektor = st.text_input("Sektör", "Perakende Giyim")
    sehir = st.selectbox("Şehir", list(data.keys()))
    ilce = st.selectbox("İlçe", data[sehir])
    limit = st.slider("Firma Sayısı", 5, 50, 10)
    baslat = st.button("Taramayı Başlat 🚀")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 İşlem Logları")
    log_box = st.empty()

if baslat:
    sorgu = f"{sehir} {ilce} {sektor}"
    with open("ayarlar.txt", "w", encoding="utf-8") as f:
        f.write(f"{sorgu}|{limit}")
    
    # Botu çalıştır
    process = subprocess.Popen(["python", "bot.py"])
    
    while process.poll() is None:
        if os.path.exists("bot_log.txt"):
            with open("bot_log.txt", "r", encoding="utf-8") as f:
                log_box.code(f.read())
        time.sleep(1)
    st.success("Tarama bitti!")

with col2:
    st.subheader("📊 Sonuçlar")
    if os.path.exists("firmalar_sonuc.csv"):
        df = pd.read_csv("firmalar_sonuc.csv", sep=';')
        st.dataframe(df)
        st.download_button("📥 Excel İndir", open("firmalar_sonuc.csv", "rb"), "liste.csv")