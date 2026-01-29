import streamlit as st
import google.generativeai as genai
import pandas as pd
import altair as alt
import os

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
# 2. DEMO VERİ OLUŞTURUCU
# ---------------------------------------------------------
def demo_veri_olustur():
    data = {
        'Tarih': ['01.01.2026', '01.01.2026', '02.01.2026', '02.01.2026', '03.01.2026', '03.01.2026', '04.01.2026', '04.01.2026'],
        'Saat': ['10:00', '10:05', '14:30', '15:00', '09:00', '12:00', '20:00', '21:00'],
        'Gönderen': ['Ayşe (Başkan)', 'Mehmet (Yazılım)', 'Ayşe (Başkan)', 'Mehmet (Yazılım)', 'Ali (Tasarım)', 'Mehmet (Yazılım)', 'Ayşe (Başkan)', 'Ali (Tasarım)'],
        'Mesaj': ['Proje ne durumda?', 'Backend bitti.', 'Tasarım nerede?', 'Veritabanı hazır.', 'Logo revizesi tamam.', 'Yemekhaneye giden?', 'Rapor yüklendi.', 'Eline sağlık.'],
        'Tip': ['Yazı', 'Yazı', 'Yazı', 'Yazı', 'Medya', 'Yazı', 'Yazı', 'Yazı']
    }
    return pd.DataFrame(data)

st.title("📊 MarmaraTOG Analiz Paneli")

# ---------------------------------------------------------
# 3. VERİ KAYNAĞI SEÇİMİ (YENİLENDİ) 🎛️
# ---------------------------------------------------------
st.sidebar.header("1. Veri Kaynağı Seçin")
secim = st.sidebar.radio(
    "Nasıl devam etmek istersiniz?",
    ["📂 Kendi Dosyamı Yükle", "📁 Hazır Veri Seti (Gerçek)", "🧪 Demo Modu (Sentetik)"]
)

df = None

# --- SENARYO 1: KULLANICI YÜKLER ---
if secim == "📂 Kendi Dosyamı Yükle":
    uploaded_file = st.sidebar.file_uploader("WhatsApp Excel'i Yükle", type=["xlsx", "xls"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Dosya okunamadı: {e}")

# --- SENARYO 2: HAZIR GERÇEK VERİ ---
elif secim == "📁 Hazır Veri Seti (Gerçek)":
    dosya_yolu = "ornek_veri.xlsx" # Klasördeki dosya adı
    if os.path.exists(dosya_yolu):
        try:
            df = pd.read_excel(dosya_yolu)
            st.sidebar.success(f"✅ Hazır veri seti yüklendi! ({len(df)} satır)")
        except Exception as e:
            st.error(f"Hazır dosya okunurken hata: {e}")
    else:
        st.sidebar.warning("⚠️ 'ornek_veri.xlsx' dosyası sunucuda bulunamadı.")

# --- SENARYO 3: DEMO MODU ---
elif secim == "🧪 Demo Modu (Sentetik)":
    df = demo_veri_olustur()
    st.sidebar.info("🧪 Demo veriler oluşturuldu.")

# ---------------------------------------------------------
# 4. ANALİZ VE GÖRSELLEŞTİRME
# ---------------------------------------------------------
if df is not None:
    # --- VERİ TEMİZLİĞİ ---
    # İsim maskeleme (Varsa Fatih Sarı'yı gizle)
    df = df.replace("Fatih Sarı", "+90 545 655 91 18")
    
    # --- OTOMATİK SÜTUN TAHMİNİ ---
    tahmini_isim = next((c for c in df.columns if any(x in c.lower() for x in ['onderen','ender','author'])), df.columns[0])
    tahmini_tarih = next((c for c in df.columns if any(x in c.lower() for x in ['arih','date','ime'])), df.columns[1] if len(df.columns)>1 else df.columns[0])

    chat_df = df.iloc[::-1]
    text_data = ""
    # Sadece son 3000 satırı alalım ki çok büyük dosyalarda prompt şişmesin
    for index, row in chat_df.head(3000).iterrows():
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

            with g1:
                st.subheader(f"🏆 {col_left} Analizi")
                if df[col_left].nunique() > 1000:
                    st.warning("⚠️ Çok fazla veri var, tablo gösteriliyor.")
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

            with g2:
                st.subheader(f"📊 {col_right} Dağılımı")
                is_time = "saat" in col_right.lower() or "time" in col_right.lower()
                is_date = False
                try:
                    parsed_dates = pd.to_datetime(df[col_right], dayfirst=True, errors='coerce')
                    if len(parsed_dates.dropna()) > len(df) * 0.5: is_date = True
                except: pass

                if is_time:
                    time_counts = df[col_right].value_counts().head(24).reset_index()
                    time_counts.columns = [col_right, "Adet"]
                    time_counts = time_counts.sort_values(by=col_right)
                    c_time = alt.Chart(time_counts).mark_bar().encode(
                        x=alt.X(col_right, title='Saat'),
                        y=alt.Y('Adet', title='Mesaj'),
                        color=alt.value("orange"),
                        tooltip=[col_right, 'Adet']
                    ).properties(height=400)
                    st.altair_chart(c_time, use_container_width=True)
                elif is_date:
                    daily = df.groupby(parsed_dates.dt.date).size().reset_index(name='Adet')
                    daily.columns = ['Tarih', 'Adet']
                    c_date = alt.Chart(daily).mark_area(
                        line={'color':'darkgreen'},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='darkgreen', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(
                        x=alt.X('Tarih:T', title='Zaman'),
                        y=alt.Y('Adet:Q', title='Aktivite'),
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
                    text = base.mark_text(radius=140).encode(text=alt.Text("Adet"), order=alt.Order("Adet", sort="descending"), color=alt.value("white"))
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

else:
    st.info("👈 Başlamak için sol menüden bir veri kaynağı seçin.")