import streamlit as st
import google.generativeai as genai
import pandas as pd

# ---------------------------------------------------------
# 1. SAYFA AYARLARI
# ---------------------------------------------------------
st.set_page_config(
    page_title="MarmaraTOG Asistanı",
    page_icon="🤖",
    layout="wide"
)

# ---------------------------------------------------------
# 2. MODEL VE GÜVENLİK KURULUMU (PRO VERSİYON)
# ---------------------------------------------------------
def gemini_ayarla():
    # Anahtarı SADECE Streamlit Secrets'tan alıyoruz.
    # Kullanıcıya sormak yok, kutu yok.
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("🚨 Sistem Hatası: API Anahtarı tanımlanmamış! Lütfen yönetici ile iletişime geçin.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # Modeli SABİTLEDİK (Kazanan Model)
    # Preview versiyonu analizde daha iyi olduğu için bunu seçtik.
    return genai.GenerativeModel("models/gemini-2.5-flash-preview-09-2025")

model = gemini_ayarla()

# ---------------------------------------------------------
# 3. ARAYÜZ
# ---------------------------------------------------------
st.title("🤖 MarmaraTOG WhatsApp Asistanı")
st.markdown("Bu asistan, MarmaraTOG WhatsApp kayıtlarını analiz eder. Dosyanızı yükleyin ve sohbete başlayın.")

# ---------------------------------------------------------
# 4. İŞLEMLER
# ---------------------------------------------------------
uploaded_file = st.sidebar.file_uploader("WhatsApp Excel Dosyasını Yükle", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Veriyi ters çevir (En güncel mesaj en üstte olsun)
        df = df.iloc[::-1]
        
        text_data = ""
        for index, row in df.iterrows():
            row_text = " | ".join([str(val) for val in row.values])
            text_data += row_text + "\n"

        st.success(f"✅ Dosya başarıyla yüklendi! Toplam {len(df)} satır veri analize hazır.")

        # Sohbet Geçmişi Yönetimi
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Kullanıcı Soru Sorduğunda
        if prompt := st.chat_input("Sorunuzu yazın..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Gemini 2.5 Flash (Preview) analiz ediyor..."):
                    try:
                        # SINIRSIZ MOD: text_data'nın tamamını gönderiyoruz.
                        # Ücretli sürümde 1 Milyon token limitin olduğu için
                        # [:25000] gibi kesmelere gerek yok.
                        full_prompt = f"Veri:\n{text_data}\n\nSoru: {prompt}"
                        
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")

    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")

else:
    st.info("👈 Başlamak için lütfen sol menüden Excel dosyanızı yükleyin.")