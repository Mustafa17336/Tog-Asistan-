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
        tahmini_isim = next((c for c in df.columns if any(x in c.lower() for x in ['onderen','ender','author'])), df.columns[0])
        tahmini_tarih = next((c for c in df.columns if any(x in c.lower() for x in ['arih','date','ime'])), df.columns[1] if len(df.columns)>1 else df.columns[0])

        chat_df = df.iloc[::-1]
        text_data = ""
        for index, row in chat_df.iterrows():
            text_data += " | ".join([str(val) for val in row.values]) + "\n"

        tab1, tab2 = st.tabs(["📈 İstatistik Paneli", "💬 Yapay Zeka Asistanı"])

        # --- TAB 1: DASHBOARD (AKILLI V5) ---
        with tab1:
            st.markdown("### 🚀 Genel Bakış")
            
            c1, c2 = st.columns(2)
            with c1:
                col_left = st.selectbox("Sol Grafik Verisi (Kişiler vb.):", df.columns, index=df.columns.get_loc(tahmini_isim))
            with c2:
                col_right = st.selectbox("Sağ Grafik Verisi (Zaman/Tip vb.):", df.columns, index=df.columns.get_loc(tahmini_tarih))

            # --- METRİKLER ---
            if col_left and col_right:
                total_msgs = len(df)
                uniq_left = df[col_left].nunique()
                top_left = df[col_left].mode()[0] if not df[col_left].mode().empty else "Yok"
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Toplam Satır", f"{total_msgs}")
                m2.metric(f"Benzersiz {col_left}", f"{uniq_left}")
                m3.metric(f"En Sık Geçen {col_left}", str(top_left)[:15]+"..." if len(str(top_left))>15 else str(top_left))
                
                st.divider()

                g1, g2 = st.columns(2)

                # --- SOL GRAFİK (Yatay Bar - Kategorik) ---
                with g1:
                    st.subheader(f"🏆 {col_left} Analizi")
                    # Çok fazla benzersiz veri varsa (örn: Mesaj içeriği) grafik bozulur, uyaralım.
                    if df[col_left].nunique() > 1000:
                        st.warning(f"⚠️ '{col_left}' sütununda çok fazla çeşitlilik var, grafik yerine en sık geçenleri listeliyoruz.")
                        st.dataframe(df[col_left].value_counts().head(10), use_container_width=True)
                    else:
                        # İlk 10'u göster
                        data_counts = df[col_left].value_counts().head(10).reset_index()
                        data_counts.columns = [col_left, "Adet"]
                        
                        chart = alt.Chart(data_counts).mark_bar().encode(
                            x=alt.X('Adet', title='Sayısı'),
                            y=alt.Y(col_left, sort='-x', title=None), # Eksen etiketi temiz
                            tooltip=[col_left, 'Adet'],
                            color=alt.value("#3182bd")
                        ).properties(height=400)
                        st.altair_chart(chart, use_container_width=True)

                # --- SAĞ GRAFİK (MULTI-MOD: Tarih / Saat / Kategori) ---
                with g2:
                    st.subheader(f"📊 {col_right} Dağılımı")
                    
                    # 1. Senaryo: Tarih mi? (Parse etmeye çalış)
                    is_date = False
                    try:
                        # Sadece sayısal olmayan ve tarih formatına benzeyenleri dene
                        parsed_dates = pd.to_datetime(df[col_right], dayfirst=True, errors='coerce')
                        valid_dates = parsed_dates.dropna()
                        # Eğer sütunun %50'sinden fazlası tarihse, bu bir Tarih sütunudur.
                        if len(valid_dates) > len(df) * 0.5:
                            is_date = True
                    except:
                        is_date = False

                    # 2. Senaryo: Saat mi?
                    is_time = "saat" in col_right.lower() or "time" in col_right.lower()

                    # --- GRAFİK ÇİZİMİ ---
                    if is_time:
                        # SAAT GRAFİĞİ (Bar)
                        time_counts = df[col_right].value_counts().head(24).reset_index()
                        time_counts.columns = [col_right, "Adet"]
                        time_counts = time_counts.sort_values(by=col_right) # Saate göre sırala 00:00 -> 23:00
                        
                        c_time = alt.Chart(time_counts).mark_bar().encode(
                            x=alt.X(col_right, title='Saat', sort=None),
                            y=alt.Y('Adet', title='Mesaj Sayısı'),
                            color=alt.value("orange"),
                            tooltip=[col_right, 'Adet']
                        ).properties(height=400)
                        st.altair_chart(c_time, use_container_width=True)

                    elif is_date:
                        # TARİH GRAFİĞİ (Area)
                        daily = df.groupby(parsed_dates.dt.date).size().reset_index(name='Adet')
                        daily.columns = ['Tarih', 'Adet']
                        
                        c_date = alt.Chart(daily).mark_area(
                            line={'color':'darkgreen'},
                            color=alt.Gradient(
                                gradient='linear',
                                stops=[alt.GradientStop(color='darkgreen', offset=0), alt.GradientStop(color='white', offset=1)],
                                x1=1, x2=1, y1=1, y2=0
                            )
                        ).encode(
                            x=alt.X('Tarih:T', title='Zaman Çizelgesi'),
                            y=alt.Y('Adet:Q', title='Günlük Aktivite'),
                            tooltip=[alt.Tooltip('Tarih:T', format='%d %b %Y'), 'Adet']
                        ).properties(height=400)
                        st.altair_chart(c_date, use_container_width=True)

                    else:
                        # KATEGORİ GRAFİĞİ (DONUT CHART) - "Tip", "Durum" vb. için
                        # Eğer veri sayısı azsa (örn: Medya, Yazı -> 2 çeşit) Pasta yap
                        cat_counts = df[col_right].value_counts().head(10).reset_index()
                        cat_counts.columns = ["Kategori", "Adet"]
                        
                        base = alt.Chart(cat_counts).encode(
                            theta=alt.Theta("Adet", stack=True)
                        )
                        pie = base.mark_arc(outerRadius=120, innerRadius=60).encode(
                            color=alt.Color("Kategori"),
                            order=alt.Order("Adet", sort="descending"),
                            tooltip=["Kategori", "Adet"]
                        )
                        text = base.mark_text(radius=140).encode(
                            text=alt.Text("Adet"),
                            order=alt.Order("Adet", sort="descending"),
                            color=alt.value("white")  
                        )
                        st.altair_chart(pie + text, use_container_width=True)

        with tab2:
            st.subheader("💬 Sohbet Analizi")
            if "messages" not in st.session_state: st.session_state.messages = []
            for m in st.session_state.messages: st.chat_message(m["role"]).markdown(m["content"])
            if prompt := st.chat_input("Sorunuzu yazın..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.chat_message("user").markdown(prompt)
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
        st.error(f"Hata: {e}")
else:
    st.info("👈 Excel dosyasını yükleyin.")