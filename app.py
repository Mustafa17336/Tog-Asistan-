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

# ---------------------------------------------------------
# 2. DEMO VERİ OLUŞTURUCU (YENİ ÖZELLİK) 🧪
# ---------------------------------------------------------
def demo_veri_olustur():
    data = {
        'Tarih': ['01.01.2026', '01.01.2026', '02.01.2026', '02.01.2026', '02.01.2026', '03.01.2026', '03.01.2026', '03.01.2026', '03.01.2026', '04.01.2026', '04.01.2026'],
        'Saat': ['10:00', '10:05', '14:30', '14:32', '15:00', '09:00', '09:15', '12:00', '12:30', '20:00', '21:00'],
        'Gönderen': ['Ayşe (Başkan)', 'Mehmet (Yazılım)', 'Ayşe (Başkan)', 'Ali (Tasarım)', 'Mehmet (Yazılım)', 'Ali (Tasarım)', 'Ayşe (Başkan)', 'Mehmet (Yazılım)', 'Mehmet (Yazılım)', 'Ayşe (Başkan)', 'Ali (Tasarım)'],
        'Mesaj': ['Arkadaşlar proje teslimine az kaldı.', 'Ben backend tarafını hallettim.', 'Tasarım ne durumda Ali?', 'Renk paletini seçtim, atıyorum birazdan.', 'Harikasın, ben de veritabanını bağlıyorum.', 'Günaydın, logo revizesi bitti.', 'Süper, toplantı yapalım mı?', 'Ben acıktım, yemekhaneye inen var mı?', 'Bugün köfte varmış beyler.', 'Raporu sisteme yükledim.', 'Ellerine sağlık başkan.'],
        'Tip': ['Yazı', 'Yazı', 'Yazı', 'Yazı', 'Yazı', 'Medya', 'Yazı', 'Yazı', 'Yazı', 'Yazı', 'Yazı']
    }
    return pd.DataFrame(data)

st.title("📊 MarmaraTOG Analiz Paneli")

# ---------------------------------------------------------
# 3. VERİ YÜKLEME VE SEÇİM
# ---------------------------------------------------------
st.sidebar.header("Veri Kaynağı")
uploaded_file = st.sidebar.file_uploader("WhatsApp Excel'i Yükle", type=["xlsx", "xls"])
demo_mode = st.sidebar.checkbox("📂 Örnek Veri ile Dene (Demo)", value=False)

df = None

# Mantık: Dosya varsa dosyayı al, yoksa ve Demo seçiliyse Demoyu al.
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        # İsim Düzeltme (Fatih Sarı -> Numara)
        df = df.replace("Fatih Sarı", "+90 5XX XXX XX XX")
    except Exception as e:
        st.error(f"Dosya okunamadı: {e}")
elif demo_mode:
    df = demo_veri_olustur()
    st.toast("🧪 Demo Modu Aktif! Örnek veriler yüklendi.")

# ---------------------------------------------------------
# 4. ANALİZ VE GÖRSELLEŞTİRME
# ---------------------------------------------------------
if df is not None:
    # --- OTOMATİK SÜTUN TAHMİNİ ---
    tahmini_isim = next((c for c in df.columns if any(x in c.lower() for x in ['onderen','ender','author'])), df.columns[0])
    tahmini_tarih = next((c for c in df.columns if any(x in c.lower() for x in ['arih','date','ime'])), df.columns[1] if len(df.columns)>1 else df.columns[0])

    chat_df = df.iloc[::-1]
    text_data = ""
    for index, row in chat_df.iterrows():
        text_data += " | ".join([str(val) for val in row.values]) + "\n"

    tab1, tab2 = st.tabs(["📈 İstatistik Paneli", "💬 Yapay Zeka Asistanı"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        st.markdown("### 🚀 Genel Bakış")
        
        c1, c2 = st.columns(2)
        with c1:
            col_left = st.selectbox("Sol Grafik Verisi:", df.columns, index=df.columns.get_loc(tahmini_isim))
        with c2:
            col_right = st.selectbox("Sağ Grafik Verisi:", df.columns, index=df.columns.get_loc(tahmini_tarih))

        if col_left and col_right:
            total_msgs = len(df)
            uniq_left = df[col_left].nunique()
            top_left = df[col_left].mode()[0] if not df[col_left].mode().empty else "Yok"
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Satır", f"{total_msgs}")
            m2.metric(f"Benzersiz {col_left}", f"{uniq_left}")
            m3.metric(f"Lider", str(top_left)[:15]+"..." if len(str(top_left))>15 else str(top_left))
            
            st.divider()

            g1, g2 = st.columns(2)

            # --- SOL GRAFİK ---
            with g1:
                st.subheader(f"🏆 {col_left} Analizi")
                if df[col_left].nunique() > 1000:
                    st.warning(f"⚠️ Çok fazla çeşitlilik var, tablo gösteriliyor.")
                    st.dataframe(df[col_left].value_counts().head(10), use_container_width=True)
                else:
                    data_counts = df[col_left].value_counts().head(10).reset_index()
                    data_counts.columns = [col_left, "Adet"]
                    
                    chart = alt.Chart(data_counts).mark_bar().encode(
                        x=alt.X('Adet', title='Sayısı'),
                        y=alt.Y(col_left, sort='-x', title=None),
                        tooltip=[col_left, 'Adet'],
                        color=alt.value("#3182bd")
                    ).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)

            # --- SAĞ GRAFİK ---
            with g2:
                st.subheader(f"📊 {col_right} Dağılımı")
                
                is_date = False
                try:
                    parsed_dates = pd.to_datetime(df[col_right], dayfirst=True, errors='coerce')
                    valid_dates = parsed_dates.dropna()
                    if len(valid_dates) > len(df) * 0.5: is_date = True
                except: is_date = False

                is_time = "saat" in col_right.lower() or "time" in col_right.lower()

                if is_time:
                    time_counts = df[col_right].value_counts().head(24).reset_index()
                    time_counts.columns = [col_right, "Adet"]
                    time_counts = time_counts.sort_values(by=col_right)
                    
                    c_time = alt.Chart(time_counts).mark_bar().encode(
                        x=alt.X(col_right, title='Saat', sort=None),
                        y=alt.Y('Adet', title='Mesaj Sayısı'),
                        color=alt.value("orange"),
                        tooltip=[col_right, 'Adet']
                    ).properties(height=400)
                    st.altair_chart(c_time, use_container_width=True)

                elif is_date:
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
                    cat_counts = df[col_right].value_counts().head(10).reset_index()
                    cat_counts.columns = ["Kategori", "Adet"]
                    
                    base = alt.Chart(cat_counts).encode(theta=alt.Theta("Adet", stack=True))
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
        st.info("💡 İpucu: Demo modunda yapay zekaya 'Ayşe ne zaman toplantı istemiş?' veya 'Mehmet ne yemek istiyor?' diye sorabilirsin.")
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

else:
    # Karşılama Ekranı
    st.info("👈 Başlamak için sol menüden Excel yükleyin veya **Demo Modunu** açın.")