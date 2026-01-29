import streamlit as st
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="MarmaraTOG Asistanı", page_icon="🤖", layout="wide")

# ---------------------------------------------------------
# MODEL SEÇİMİ (GARANTİLİ LİSTE YÖNTEMİ)
# ---------------------------------------------------------
def gemini_ayarla():
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.sidebar.text_input("Google API Anahtarı", type="password")
    
    if not api_key:
        st.warning("Lütfen sol taraftan veya Secrets üzerinden API anahtarı giriniz.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    try:
        # Google'dan o an MÜSAİT olan modelleri çekiyoruz
        uygun_modeller = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                uygun_modeller.append(m.name)
        
        secilen_model = None

        # 1. ÖNCELİK: Listede isminde "1.5-flash" geçen İLK model
        # (Örn: models/gemini-1.5-flash-001 veya models/gemini-1.5-flash-latest)
        for m in uygun_modeller:
            if "1.5-flash" in m:
                secilen_model = m
                break
        
        # 2. ÖNCELİK: Eğer 1.5 yoksa, herhangi bir "flash"
        if not secilen_model:
            for m in uygun_modeller:
                if "flash" in m:
                    secilen_model = m
                    break

        # 3. GÜVENLİK AĞI: Hiçbiri yoksa listedeki ilk modeli al (Asla 404 vermez)
        if not secilen_model and uygun_modeller:
            secilen_model = uygun_modeller[0]

        # KANIT: Seçilen resmi ismi ekrana yaz
        st.sidebar.success(f"✅ Çalışan Model: {secilen_model}")
        
        return genai.GenerativeModel(secilen_model)

    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        st.stop()

model = gemini_ayarla()

st.title("🤖 MarmaraTOG WhatsApp Asistanı")
st.markdown("Bu asistan, yüklediğiniz WhatsApp geçmişini analiz eder ve sorularınızı cevaplar.")

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
                        full_prompt = f"Veri: {text_data[:80000]}\nSoru: {prompt}"
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Cevap üretilirken hata: {e}")
    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")
else:
    st.info("👈 Başlamak için Excel dosyanızı yükleyin.")