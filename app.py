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
        tahmini_isim_sutunu = next((col for col in df.columns if "onderen" in col.lower() or "ender" in col.lower() or "author" in col.lower()), df.columns[0])
        tahmini_tarih_sutunu = next((col for col in df.columns if "arih" in col.lower() or "date" in col.lower() or "ime" in col.lower()), df.columns[1] if len(df.columns) > 1 else df.columns[0])

        # Veriyi Hazırla (Chat için)
        chat_df = df.iloc[::-1]
        text_data = ""
        for index, row in chat_df.iterrows():
            text_data += " | ".join([str(val) for val in row.values]) + "\n"

        # -----------------------------------------------------
        # SEKME YAPISI
        # -----------------------------------------------------
        tab1, tab2 = st.tabs(["📈 İstatistik Paneli", "💬 Yapay Zeka Asistanı"])

        # --- TAB 1: DASHBOARD ---
        with tab1:
            st.markdown("### 🚀 Genel Bakış")
            
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                author_col = st.selectbox("👤 İsim Sütunu:", df.columns, index=df.columns.get_loc(tahmini_isim_sutunu))
            with col_sel2:
                # Buraya artık "Analiz Sütunu" diyelim, çünkü Saat de seçilebilir
                date_col = st.selectbox("📅 Tarih/Zaman Sütunu:", df.columns, index=df.columns.get_loc(tahmini_tarih_sutunu))

            # --- METRİKLER ---
            if author_col and date_col:
                total_msgs = len(df)
                total_users = df[author_col].nunique()
                top_user = df[author_col].mode()[0]
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Toplam Mesaj", f"{total_msgs}")
                m2.metric("Aktif Kişi", f"{total_users}")
                m3.metric("Lider", f"{top_user}")
                
                st.divider()

                g1, g2 = st.columns(2)

                # GRAFİK 1: KİŞİLER (YATAY BAR)
                with g1:
                    st.subheader(f"🏆 {author_col} - İlk 10")
                    user_counts = df[author_col].value_counts().head(10).reset_index()
                    user_counts.columns = [author_col, "Mesaj Sayısı"]
                    
                    chart = alt.Chart(user_counts).mark_bar().encode(
                        x=alt.X('Mesaj Sayısı', title='Mesaj Adedi'), 
                        y=alt.Y(author_col, sort='-x', title=None),
                        tooltip=[author_col, 'Mesaj Sayısı'],
                        color=alt.value("#3182bd")
                    ).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)

                # GRAFİK 2: AKILLI ZAMAN GRAFİĞİ (Area veya Bar)
                with g2:
                    st.subheader(f"📊 {date_col} Analizi")
                    
                    # --- AKILLI KARAR MEKANİZMASI ---
                    # Eğer sütun adında "Saat" veya "Time" varsa -> BAR GRAFİĞİ (Dağılım) yap
                    is_time_column = "saat" in date_col.lower() or "time" in date_col.lower()
                    
                    if is_time_column:
                        # --- SENARYO A: SAAT ANALİZİ (BAR CHART) ---
                        # En yoğun saatleri göster
                        time_counts = df[date_col].value_counts().head(20).reset_index()
                        time_counts.columns = [date_col, "Mesaj Sayısı"]
                        # Sıralama yap (Saat olduğu için string sort genelde doğru çalışır: 09:00, 10:00...)
                        time_counts = time_counts.sort_values(by=date_col)

                        chart2 = alt.Chart(time_counts).mark_bar().encode(
                            x=alt.X(date_col, title=date_col, sort=None), # X eksenine saati koy
                            y=alt.Y('Mesaj Sayısı', title='Mesaj Sayısı'),
                            color=alt.value("orange"),
                            tooltip=[date_col, 'Mesaj Sayısı']
                        ).properties(height=400)
                        st.altair_chart(chart2, use_container_width=True)
                    
                    else:
                        # --- SENARYO B: TARİH ANALİZİ (AREA CHART - ESKİSİ GİBİ) ---
                        try:
                            df["ParsedDate"] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
                            # Geçersiz tarihleri at (NaT)
                            valid_dates = df.dropna(subset=["ParsedDate"])
                            
                            if not valid_dates.empty:
                                daily_counts = valid_dates.groupby(valid_dates["ParsedDate"].dt.date).size().reset_index(name='Mesaj')
                                
                                chart2 = alt.Chart(daily_counts).mark_area(
                                    line={'color':'darkgreen'},
                                    color=alt.Gradient(
                                        gradient='linear',
                                        stops=[alt.GradientStop(color='darkgreen', offset=0),
                                               alt.GradientStop(color='white', offset=1)],
                                        x1=1, x2=1, y1=1, y2=0
                                    )
                                ).encode(
                                    x=alt.X('ParsedDate:T', title='Tarih'),
                                    y=alt.Y('Mesaj:Q', title='Günlük Mesaj'),
                                    tooltip=[alt.Tooltip('ParsedDate:T', format='%d %B %Y'), 'Mesaj']
                                ).properties(height=400)
                                st.altair_chart(chart2, use_container_width=True)
                            else:
                                st.warning("Bu sütunda geçerli tarih verisi bulunamadı.")
                        except:
                            st.warning("Veri grafiğe dökülemedi.")

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
    st.info("👈 Excel dosyasını yükleyin.")