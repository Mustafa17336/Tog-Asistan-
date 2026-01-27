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
# 2. API ANAHTARI VE MODEL KURULUMU (GÜNCELLENDİ)
# ---------------------------------------------------------
def gemini_ayarla():
    # Önce Streamlit Secrets'a bak, yoksa kenar çubuğundan iste
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.sidebar.text_input("Google API Anahtarı", type="password")
    
    if not api_key:
        st.warning("Lütfen sol taraftan veya Secrets üzerinden API anahtarı giriniz.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # --- KRİTİK DEĞİŞİKLİK ---
    # Eski arama döngüsünü sildik. Doğrudan 1.5 Flash'ı seçiyoruz.
    # Bu sayede sistem asla 2.5 veya başka modele gitmez.
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        st.error(f"Model yüklenirken hata oluştu: {e}")
        st.stop()

model = gemini_ayarla()

# ---------------------------------------------------------
# 3. ARAYÜZ VE BAŞLIKLAR
# ---------------------------------------------------------
st.title("🤖 MarmaraTOG WhatsApp Asistanı")
st.markdown("Bu asistan, yüklediğiniz WhatsApp geçmişini analiz eder ve sorularınızı cevaplar.")

# ---------------------------------------------------------
# 4. DOSYA YÜKLEME VE İŞLEME
# ---------------------------------------------------------
uploaded_file = st.sidebar.file_uploader("WhatsApp Excel Dosyasını Yükle", type=["xlsx", "xls"])

if uploaded_file:
    try:
        # Excel dosyasını oku
        df = pd.read_excel(uploaded_file)
        
        # Veriyi metne dönüştür (Yapay zekanın okuması için)
        # Sütun isimlerin farklıysa burayı güncelle (Tarih, Mesaj vb.)
        text_data = ""
        for index, row in df.iterrows():
            # Tüm satırı tek bir metin haline getiriyoruz
            row_text = " | ".join([str(val) for val in row.values])
            text_data += row_text + "\n"

        st.success(f"✅ Dosya yüklendi! Toplam {len(df)} satır veri analiz edildi.")

        # ---------------------------------------------------------
        # 5. SOHBET EKRANI (CHAT)
        # ---------------------------------------------------------
        
        # Sohbet geçmişini tutmak için session state
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Geçmiş mesajları ekrana yazdır
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Kullanıcıdan yeni soru al
        if prompt := st.chat_input("Gruba dair neyi merak ediyorsun?"):
            # Kullanıcı mesajını ekrana ve geçmişe ekle
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Yapay Zeka Cevabı Hazırlanıyor...
            with st.chat_message("assistant"):
                with st.spinner("Analiz yapılıyor..."):
                    try:
                        # RAG Mantığı: Soruyu ve Veriyi birleştirip soruyoruz
                        # Not: Veri çok büyükse burada Token hatası alabilirsin, 
                        # o durumda veri özetleme yapmak gerekir.
                        full_prompt = f"""
                        Aşağıdaki WhatsApp konuşma geçmişine dayanarak soruyu cevapla.
                        Sadece bu veriyi kullan, uydurma yapma. Samimi bir dil kullan.

                        VERİ:
                        {text_data[:100000]}  # İlk 100bin karakteri alıyoruz (Hız/Kota için sınır)

                        SORU: {prompt}
                        """
                        
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                        
                        # Cevabı geçmişe kaydet
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")

    except Exception as e:
        st.error(f"Dosya işlenirken hata oluştu: {e}")

else:
    st.info("👈 Lütfen sol menüden Excel dosyanızı yükleyin.")