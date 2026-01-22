import streamlit as st
import subprocess
import pandas as pd
import os
import time

# Şifre bölümü (Kendi şifrenizle güncelleyin)
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Şifre:", type="password")
    if st.button("Giriş"):
        if pwd == "üç": # Burayı güncelleyin
            st.session_state.auth = True
            st.rerun()
    st.stop()

st.title("📍 Google Maps E-posta Toplayıcı")

# Sidebar ayarları
with st.sidebar:
    sektor = st.text_input("Sektör", "Hukuk Bürosu")
    sehir = st.selectbox("Şehir", ["İstanbul", "Ankara", "İzmir"])
    limit = st.slider("Limit", 1, 50, 5)
    baslat = st.button("Taramayı Başlat")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 İşlem Logları")
    log_alani = st.empty()

if baslat:
    # Ayarları kaydet
    with open("ayarlar.txt", "w", encoding="utf-8") as f:
        f.write(f"{sehir} {sektor}|{limit}")
    
    # Log dosyasını sıfırla
    if os.path.exists("bot_log.txt"): os.remove("bot_log.txt")
    
    # BOTU ÇALIŞTIR VE HATALARI YAKALA
    try:
        # Sunucu üzerinde playwright kurulumunu tetiklemek için ek komut
        process = subprocess.Popen(["python", "bot.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        while process.poll() is None:
            if os.path.exists("bot_log.txt"):
                with open("bot_log.txt", "r", encoding="utf-8") as f:
                    log_alani.code(f.read())
            time.sleep(1)
        
        # Eğer bot hiç log üretmeden bittiyse hata çıktısını göster
        stdout, stderr = process.communicate()
        if stderr:
            st.error(f"Sistem Hatası: {stderr}")
            
    except Exception as e:
        st.error(f"Başlatma Hatası: {e}")

with col2:
    st.subheader("📊 Sonuçlar")
    if os.path.exists("firmalar_sonuc.csv"):
        st.dataframe(pd.read_csv("firmalar_sonuc.csv", sep=';'))
