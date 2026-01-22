import streamlit as st
import subprocess
import pandas as pd
import os
import time

# --- TÜRKİYE VERİSİ (HIZLI AÇILIŞ İÇİN KODUN İÇİNDE) ---
# Örnek olarak ana iller; tüm listeyi ekleyebiliriz.
TURKIYE_DATA = {
    "İstanbul": ["Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", "Esenler", "Esenyurt", "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane", "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer", "Silivri", "Sultanbeyli", "Sultangazi", "Şile", "Şişli", "Tuzla", "Ümraniye", "Üsküdar", "Zeytinburnu"],
    "Ankara": ["Akyurt", "Altındağ", "Ayaş", "Bala", "Beypazarı", "Çamlıdere", "Çankaya", "Çubuk", "Elmadağ", "Etimesgut", "Evren", "Gölbaşı", "Güdül", "Haymana", "Kahramankazan", "Kalecik", "Keçiören", "Kızılcahamam", "Mamak", "Nallıhan", "Polatlı", "Pursaklar", "Sincan", "Şereflikoçhisar", "Yenimahalle"],
    "İzmir": ["Aliağa", "Balçova", "Bayındır", "Bayraklı", "Bergama", "Beydağ", "Bornova", "Buca", "Çeşme", "Çiğli", "Dikili", "Foça", "Gaziemir", "Güzelbahçe", "Karabağlar", "Karaburun", "Karşıyaka", "Kemalpaşa", "Kınık", "Kiraz", "Konak", "Menderes", "Menemen", "Narlıdere", "Ödemiş", "Seferihisar", "Selçuk", "Tire", "Torbalı", "Urla"]
}

# --- ŞİFRE KONTROLÜ ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Güvenli Giriş")
    pwd = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş"):
        if pwd == "üç": # Burayı değiştirin
            st.session_state.auth = True
            st.rerun()
    st.stop()

st.title("📍 Google Maps E-posta Toplayıcı")

with st.sidebar:
    st.header("🔍 Arama Ayarları")
    sektor = st.text_input("Sektör", "Hukuk Bürosu")
    
    # Arama doğrulamalı İl seçimi
    sehir = st.selectbox("İl Seçiniz (Arayarak Bulabilirsiniz)", sorted(TURKIYE_DATA.keys()), index=0)
    
    # İlçe seçimi
    ilce = st.selectbox("İlçe Seçiniz", sorted(TURKIYE_DATA[sehir]))
    
    limit = st.slider("İncelenecek Firma Sayısı", 1, 50, 10)
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
    
    # Botu çalıştırırken terminal çıktılarını doğrudan ekrana basacak yapı
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
