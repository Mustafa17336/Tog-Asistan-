import streamlit as st
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="MarmaraTOG Asistanı", page_icon="🤖", layout="wide")

def gemini_ayarla():
    # 1. API Anahtarını Al
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.sidebar.text_input("Google API Anahtarı", type="password")
    
    if not api_key:
        st.warning("Lütfen sol taraftan veya Secrets üzerinden API anahtarı giriniz.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    try:
        # 2. Tüm Modelleri Listele ve Kullanıcıya Seçtir
        uygun_modeller = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                uygun_modeller.append(m.name)
        
        # Eğer liste boşsa hata ver
        if not uygun_modeller:
            st.error("API anahtarınızla erişilebilen hiçbir model bulunamadı.")
            st.stop()

        # Varsayılan olarak 1.5-flash'ı bulmaya çalış (Seçili gelmesi için)
        varsayilan_index = 0
        for i, model_adi in enumerate(uygun_modeller):
            if "1.5-flash" in model_adi:
                varsayilan_index = i
                break

        # KULLANICI SEÇİMİ (Artık patron sensin)
        secilen_model_adi = st.sidebar.selectbox(
            "Kullanılacak Modeli Seçiniz:",
            uygun_modeller,
            index=varsayilan_index
        )
        
        st.sidebar.success(f"✅ Şu an Seçili: {secilen_model_adi}")
        
        return genai.GenerativeModel(secilen_model_adi)

    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        st.stop()

model = gemini_ayarla()

st.title("🤖 MarmaraTOG WhatsApp Asistanı")
st.markdown("Bu asistan, yüklediğiniz WhatsApp geçmişini analiz eder.")

uploaded_file = st.sidebar.file_uploader("WhatsApp Excel Dosyasını Yükle", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        text_data = ""
        for index, row in df.iterrows():
            row_text = " | ".join([str(val) for val in row.values])
            text_data += row_text + "\n"

        st.success(f"✅ Dosya yüklendi! {len(df)} satır analiz ediliyor.")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Sorunuzu yazın..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analiz yapılıyor..."):
                    try:
                        full_prompt = f"Veri: {text_data[:25000]}\nSoru: {prompt}"
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Hata: {e}")
    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")
else:
    st.info("👈 Başlamak için Excel dosyanızı yükleyin.")