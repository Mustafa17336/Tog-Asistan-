import streamlit as st
import google.generativeai as genai
import pandas as pd
import altair as alt

# ---------------------------------------------------------
# 1. AYARLAR
# ---------------------------------------------------------
st.set_page_config(page_title="MarmaraTOG Asistanı", page_icon="📊", layout="wide")

def gemini_ayarla():
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("models/gemini-2.5-flash-preview-09-2025")
    st.error("🚨 API Anahtarı Eksik!")
    st.stop()

model = gemini_ayarla()

st.title("📊 MarmaraTOG Analiz Paneli")

# ---------------------------------------------------------
# 2. VERİ YÜKLEME
# ---------------------------------------------------------
uploaded_file = st.sidebar.file_uploader("WhatsApp Excel Dosyasını Yükle", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        # --- OTOMATİK SÜTUN TAHMİNİ ---
        # Tahmin etmeye çalış, bulamazsan ilk sütunu al
        tahmini_isim_sutunu = next((col for col in df.columns if "onderen" in col.lower() or "ender" in col.lower() or "author" in col.lower()), df.columns[0])
        tahmini_tarih_sutunu = next((col for col in df.columns if "arih" in col.lower() or "date" in col.lower() or "ime" in col.lower()), df.columns[1] if len(df.columns) > 1 else df.columns[0])

        # Veriyi Hazırla (Chat için)
        chat_df = df.iloc[::-1] # Eskiden yeniye
        text_data = ""
        for index, row in chat_df.iterrows():
            text_data += " | ".join([str(val) for val in row.values]) + "\n"

        # -----------------------------------------------------
        # SEKME YAPISI
        # -----------------------------------------------------
        tab1, tab2 = st.tabs(["📈 İstatistik Paneli (Dashboard)", "💬 Yapay Zeka Asistanı"])

        # --- TAB 1: DASHBOARD (DİNAMİK ETİKETLİ) ---
        with tab1:
            st.markdown("### 🚀 Genel Bakış")
            
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                author_col = st.selectbox("👤 İsimlerin olduğu sütun:", df.columns, index=df.columns.get_loc(tahmini_isim_sutunu))
            with col_sel2:
                date_col = st.selectbox("📅 Tarihlerin olduğu sütun:", df.columns, index=df.columns.get_loc(tahmini_tarih_sutunu))

            # --- METRİK KARTLARI ---
            if author_col and date_col:
                total_msgs = len(df)
                total_users = df[author_col].nunique()
                top_user = df[author_col].mode()[0]
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Toplam Mesaj", f"{total_msgs}")
                m2.metric("Aktif Kişi Sayısı", f"{total_users}")
                m3.metric("Grup Lideri", f"{top_user}")
                
                st.divider()

                # --- GRAFİKLER ---
                g1, g2 = st.columns(2)

                # Grafik 1: En Çok Konuşanlar (DİNAMİK ETİKET)
                with g1:
                    st.subheader("🏆 En Çok Konuşan İlk 10")
                    
                    # Veriyi hazırla ama sütun ismini DEĞİŞTİRME, kullanıcının seçtiği kalsın
                    user_counts = df[author_col].value_counts().head(10).reset_index()
                    user_counts.columns = [author_col, "Mesaj Sayısı"] # Dinamik İsim + Sabit Sayaç
                    
                    chart = alt.Chart(user_counts).mark_bar().encode(
                        x=alt.X('Mesaj Sayısı', title='Mesaj Adedi'), 
                        y=alt.Y(author_col, sort='-x', title=author_col), # <-- BURASI ARTIK DİNAMİK (Seçilen sütun adı yazar)
                        tooltip=[author_col, 'Mesaj Sayısı'],
                        color=alt.value("#3182bd") # Tek renk daha şık durur
                    ).properties(height=400)
                    
                    st.altair_chart(chart, use_container_width=True)

                # Grafik 2: Zaman Çizelgesi (TEMİZ ETİKET)
                with g2:
                    st.subheader("📅 Mesaj Yoğunluğu")
                    try:
                        df["ParsedDate"] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
                        daily_counts = df.groupby(df["ParsedDate"].dt.date).size().reset_index(name='Mesaj')
                        
                        chart2 = alt.Chart(daily_counts).mark_area(
                            line={'color':'darkgreen'},
                            color=alt.Gradient(
                                gradient='linear',
                                stops=[alt.GradientStop(color='darkgreen', offset=0),
                                       alt.GradientStop(color='white', offset=1)],
                                x1=1, x2=1, y1=1, y2=0
                            )
                        ).encode(
                            x=alt.X('ParsedDate:T', title='Tarih'), # "ParsedDate" yazısı yerine "Tarih" yazacak
                            y=alt.Y('Mesaj:Q', title='Günlük Mesaj Sayısı'),
                            tooltip=[alt.Tooltip('ParsedDate:T', title='Tarih', format='%d %B %Y'), 'Mesaj']
                        ).properties(height=400)
                        
                        st.altair_chart(chart2, use_container_width=True)
                    except:
                        st.warning("Tarih formatı grafiğe çevrilemedi.")

        # --- TAB 2: AI ASİSTAN ---
        with tab2:
            st.subheader("💬 Sohbet Analizi")
            
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Veri hakkında soru sor..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Analiz ediliyor..."):
                        try:
                            full_prompt = f"Veri:\n{text_data}\n\nSoru: {prompt}"
                            response = model.generate_content(full_prompt)
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Hata: {e}")

    except Exception as e:
        st.error(f"Dosya işlenirken hata oluştu: {e}")

else:
    st.info("👈 Analiz için lütfen Excel dosyanızı yükleyin.")