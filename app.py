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
# 2. MODEL VE GÜVENLİK
# ---------------------------------------------------------
def gemini_ayarla():
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("🚨 API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol edin.")
        st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("models/gemini-2.5-flash-preview-09-2025")

model = gemini_ayarla()

# ---------------------------------------------------------
# 3. ARAYÜZ BAŞLIĞI
# ---------------------------------------------------------
st.title("🤖 MarmaraTOG WhatsApp Analiz")
st.markdown("Bu panelde hem yapay zeka ile sohbet edebilir hem de grubun istatistiklerini inceleyebilirsiniz.")

# ---------------------------------------------------------
# 4. DOSYA YÜKLEME VE İŞLEME
# ---------------------------------------------------------
uploaded_file = st.sidebar.file_uploader("WhatsApp Excel Dosyasını Yükle", type=["xlsx", "xls"])

if uploaded_file:
    try:
        # Veriyi Oku
        df = pd.read_excel(uploaded_file)
        
        # Orijinal veriyi sakla (Grafikler için)
        raw_df = df.copy()

        # Chat için veriyi ters çevir ve metne dök
        chat_df = df.iloc[::-1]
        text_data = ""
        for index, row in chat_df.iterrows():
            row_text = " | ".join([str(val) for val in row.values])
            text_data += row_text + "\n"

        st.sidebar.success(f"✅ Dosya Yüklendi! {len(df)} satır veri.")

        # -----------------------------------------------------
        # SEKME (TAB) YAPISI
        # -----------------------------------------------------
        tab1, tab2 = st.tabs(["💬 Yapay Zeka Asistanı", "📊 İstatistik Paneli"])

        # --- TAB 1: SOHBET ASİSTANI ---
        with tab1:
            st.subheader("Sohbet Analizi")
            
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Veri hakkında bir soru sor..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Gemini 2.5 Flash analiz ediyor..."):
                        try:
                            full_prompt = f"Veri:\n{text_data}\n\nSoru: {prompt}"
                            response = model.generate_content(full_prompt)
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Hata: {e}")

        # --- TAB 2: İSTATİSTİK PANELİ ---
        with tab2:
            st.subheader("Grup İstatistikleri")
            st.info("Grafiklerin oluşması için aşağıdan ilgili sütunları seçiniz.")

            # 1. En Çok Mesaj Atanlar (Bar Grafiği)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🏆 En Çok Konuşanlar")
                # Kullanıcıya "Gönderen" sütunu hangisi diye soruyoruz (Hata riskini sıfırlar)
                author_col = st.selectbox("Hangi sütunda İsimler/Numaralar var?", df.columns, index=0)
                
                if author_col:
                    top_users = df[author_col].value_counts().head(10) # İlk 10 kişi
                    st.bar_chart(top_users)

            # 2. Zaman Analizi (Opsiyonel)
            with col2:
                st.markdown("### 📅 Veri Dağılımı")
                date_col = st.selectbox("Hangi sütunda Tarihler var? (Opsiyonel)", ["Seçiniz"] + list(df.columns))
                
                if date_col != "Seçiniz":
                    # Tarihleri gün bazında say
                    try:
                        # Tarih formatını anlamaya çalış
                        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                        daily_counts = df[date_col].dt.date.value_counts().sort_index()
                        st.line_chart(daily_counts)
                    except:
                        st.warning("Tarih formatı algılanamadı.")
                else:
                    st.write("Zaman grafiği için tarih sütununu seçin.")

            # 3. Ham Veri Önizleme
            with st.expander("📂 Ham Veriyi Görüntüle"):
                st.dataframe(df)

    except Exception as e:
        st.error(f"Dosya işlenirken hata oluştu: {e}")

else:
    st.info("👈 Analiz ve İstatistikler için Excel dosyanızı yükleyin.")