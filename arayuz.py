import streamlit as st
import subprocess
import pandas as pd
import os
import time
import requests

# Giriş Kontrolü
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("Şifre:", type="password")
    if st.button("Giriş"):
        if pwd == "üç": # ŞİFREYİ BURADAN DEĞİŞTİRİN
            st.session_state.auth = True
            st.rerun()
    st.stop()

@st.cache_data
def il_ilce_verisi_al():
    url = "https://raw.githubusercontent.com/fatihyigit/turkiye-iller-ilceler-json/master/data.json"
    try:
        r = requests.get(url)
        data = r.json()
        return {item["name"]: [d["name"] for d in item["districts"]] for item in data}
    except: return {"Hata": ["Veri Alınamadı"]}

turkiye_data = il_ilce_verisi_al()

st.title("📍 Maps E-posta Toplayıcı")

with st.sidebar:
    sektor = st.text_input("Sektör", "Hukuk Bürosu")
    sehir = st.selectbox("Şehir", sorted(list(turkiye_data.keys())))
    ilce = st.selectbox("İlçe", sorted(turkiye_data[sehir]))
    limit = st.slider("Limit", 1, 50, 10)
    baslat = st.button("Başlat 🚀")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 Günlük")
    log_alani = st.empty()

if baslat:
    with open("ayarlar.txt", "w", encoding="utf-8") as f:
        f.write(f"{sehir} {ilce} {sektor}|{limit}")
    
    if os.path.exists("bot_log.txt"): os.remove("bot_log.txt")
    process = subprocess.Popen(["python", "bot.py"])
    
    while process.poll() is None:
        if os.path.exists("bot_log.txt"):
            with open("bot_log.txt", "r", encoding="utf-8") as f:
                log_alani.code(f.read())
        time.sleep(1)
    st.success("Bitti!")

with col2:
    st.subheader("📊 Sonuçlar")
    if os.path.exists("firmalar_sonuc.csv"):
        st.dataframe(pd.read_csv("firmalar_sonuc.csv", sep=';'))
