import streamlit as st
import google.generativeai as genai
import pandas as pd
import altair as alt
import plotly.express as px  # <-- YENİ OYUNCU: Plotly
import os
import re
from collections import Counter

# ---------------------------------------------------------
# 1. AYARLAR
# ---------------------------------------------------------
st.set_page_config(page_title="Sohbet Analiz Paneli", page_icon="📊", layout="wide")

def gemini_ayarla():
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("models/gemini-2.5-flash-preview-09-2025")
    st.error("🚨 API Anahtarı Eksik!")
    st.stop()

model = gemini_ayarla()

# ---------------------------------------------------------
# 2. YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------
def demo_veri_olustur():
    data = {
        'Tarih': ['01.01.2026', '01.01.2026', '02.01.2026', '02.01.2026', '03.01.2026', '03.01.2026', '04.01.2026', '04.01.2026'],
        'Saat': ['10:00', '10:05', '14:30', '15:00', '09:00', '12:00', '20:00', '21:00'],
        'Gönderen': ['Ayşe (Başkan)', 'Mehmet (Yazılım)', 'Ayşe (Başkan)', 'Mehmet (Yazılım)', 'Ali (Tasarım)', 'Mehmet (Yazılım)', 'Ayşe (Başkan)', 'Ali (Tasarım)'],
        'Mesaj': ['Proje ne durumda? 🤔', 'Backend bitti. 🔥', 'Tasarım nerede? 🧐', 'Veritabanı hazır. 👍', 'Logo revizesi tamam. 🎨', 'Yemekhaneye giden? 🍔', 'Rapor yüklendi. 📄', 'Eline sağlık. 👏'],
        'Tip': ['Yazı', 'Yazı', 'Yazı', 'Yazı', 'Medya', 'Yazı', 'Yazı', 'Yazı']
    }
    return pd.DataFrame(data)

def emojileri_ayikla(text):
    emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]', flags=re.UNICODE)
    found = emoji_pattern.findall(str(text))
    # Yasaklı listesi (Bozuk karakterler)
    yasakli_liste = ['🏻', '🏼', '🏽', '🏾', '🏿', '♂️', '♀️', '⃣', '️', '⃣', '〰', '▪', '▫', '▶', '◀', '◻', '◼', '◾', '◽']
    temiz_emojiler = [e for e in found if e not in yasakli_liste]
    return temiz_emojiler

# ---------------------------------------------------------
# 3. ARAYÜZ
# ---------------------------------------------------------
st.title("📊 Sohbet Analiz Paneli")
st.sidebar.header("1. Veri Kaynağı Seçin")
secim = st.sidebar.radio("Seçenekler:", ["📂 Kendi Dosyamı Yükle", "📁 Hazır Veri Seti (Gerçek)", "🧪 Demo Modu (Sentetik)"])

df = None

if secim == "📂 Kendi Dosyamı Yükle":
    uploaded_file = st.sidebar.file_uploader("WhatsApp Excel'i Yükle", type=["xlsx", "xls"])
    if uploaded_file:
        try: df = pd.read_excel(uploaded_file)
        except Exception as e: st.error(f"Hata: {e}")

elif secim == "📁 Hazır Veri Seti (Gerçek)":
    dosya_yolu = "ornek_veri.xlsx"
    if os.path.exists(dosya_yolu):
        try:
            df = pd.read_excel(dosya_yolu)
            st.sidebar.success(f"✅ Hazır veri seti yüklendi!")
        except Exception as e: st.error(f"Hata: {e}")
    else: st.sidebar.warning("⚠️ Hazır dosya bulunamadı.")

elif secim == "🧪 Demo Modu (Sentetik)":
    df = demo_veri_olustur()
    st.sidebar.info("🧪 Demo veriler yüklendi.")

# ---------------------------------------------------------
# 4. ANALİZ MOTORU
# ---------------------------------------------------------
if df is not None:
    df = df.replace("Fatih Sarı", "+90 5XX XXX XX XX")
    
    cols = df.columns
    col_isim = next((c for c in cols if any(x in c.lower() for x in ['onderen','ender','author'])), cols[0])
    col_tarih = next((c for c in cols if any(x in c.lower() for x in ['arih','date','ime'])), cols[1] if len(cols)>1 else cols[0])
    col_mesaj = next((c for c in cols if any(x in c.lower() for x in ['mesaj','message','icerik','text'])), cols[-1])

    chat_df = df.iloc[::-1]
    text_data = ""
    for index, row in chat_df.head(3000).iterrows():
        text_data += " | ".join([str(val) for val in row.values]) + "\n"

    tab1, tab2 = st.tabs(["📈 İstatistik Paneli", "💬 Yapay Zeka Asistanı"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        st.markdown("### 🚀 Genel Bakış")
        c1, c2 = st.columns(2)
        with c1: selected_user_col = st.selectbox("Kişi Sütunu:", cols, index=cols.get_loc(col_isim))
        with c2: selected_date_col = st.selectbox("Zaman Sütunu:", cols, index=cols.get_loc(col_tarih))

        if selected_user_col and selected_date_col:
            total_msgs = len(df)
            top_user = df[selected_user_col].mode()[0] if not df[selected_user_col].mode().empty else "Yok"
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Mesaj", f"{total_msgs}")
            m2.metric("Aktif Kişi", f"{df[selected_user_col].nunique()}")
            m3.metric("Lider", str(top_user)[:15]+"...")
            
            st.divider()

            g1, g2 = st.columns(2)
            
            with g1:
                st.subheader(f"🏆 En Çok Yazanlar")
                user_counts = df[selected_user_col].value_counts().head(10).reset_index()
                user_counts.columns = ["Kişi", "Mesaj"]
                st.altair_chart(alt.Chart(user_counts).mark_bar().encode(
                    x='Mesaj', y=alt.Y('Kişi', sort='-x'), color=alt.value("#3182bd"), tooltip=['Kişi', 'Mesaj']
                ).properties(height=350), use_container_width=True)

            with g2:
                st.subheader(f"📊 Zaman Analizi")
                try:
                    is_time = any(x in selected_date_col.lower() for x in ['saat','time'])
                    if is_time:
                        t_counts = df[selected_date_col].value_counts().head(24).reset_index()
                        t_counts.columns = ["Saat", "Mesaj"]
                        t_counts = t_counts.sort_values("Saat")
                        st.altair_chart(alt.Chart(t_counts).mark_bar().encode(
                            x='Saat', y='Mesaj', color=alt.value("orange"), tooltip=['Saat', 'Mesaj']
                        ).properties(height=350), use_container_width=True)
                    else:
                        dates = pd.to_datetime(df[selected_date_col], dayfirst=True, errors='coerce').dropna()
                        if not dates.empty:
                            d_counts = df.groupby(dates.dt.date).size().reset_index(name='Mesaj')
                            d_counts.columns = ['Tarih', 'Mesaj']
                            st.altair_chart(alt.Chart(d_counts).mark_area(
                                line={'color':'darkgreen'},
                                color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='darkgreen', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                            ).encode(x='Tarih:T', y='Mesaj:Q', tooltip=['Tarih:T', 'Mesaj']).properties(height=350), use_container_width=True)
                        else: st.warning("Tarih verisi ayrıştırılamadı.")
                except: st.warning("Grafik oluşturulamadı.")

            st.divider()

            # --- EMOJİ ANALİZİ (PLOTLY İLE GÜÇLENDİRİLDİ) ---
            st.markdown("### 🤩 Emoji Analizi")
            
            if col_mesaj and col_mesaj in df.columns:
                all_text = " ".join(df[col_mesaj].dropna().astype(str).tolist())
                found_emojis = emojileri_ayikla(all_text)

                if found_emojis:
                    emoji_counts = Counter(found_emojis).most_common(10)
                    emoji_df = pd.DataFrame(emoji_counts, columns=['Emoji', 'Adet'])
                    
                    e1, e2 = st.columns([2, 1])
                    
                    with e1:
                        st.subheader("En Çok Kullanılan Emojiler")
                        # PLOTLY İLE ÇİZİYORUZ (RENKLİ OLSUN DİYE)
                        fig = px.bar(
                            emoji_df, 
                            x='Emoji', 
                            y='Adet',
                            text='Adet',
                            color='Adet', # Renklendirme sayıya göre olsun
                            color_continuous_scale='Viridis' # Güzel bir renk paleti
                        )
                        fig.update_layout(
                            xaxis_title=None, 
                            yaxis_title=None,
                            showlegend=False,
                            height=400
                        )
                        # Emojilerin font büyüklüğünü artır
                        fig.update_xaxes(tickfont=dict(size=24))
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with e2:
                        st.subheader("Lider Emoji 👑")
                        top_emoji = emoji_df.iloc[0]['Emoji']
                        top_count = emoji_df.iloc[0]['Adet']
                        st.markdown(
                            f"""
                            <div style='text-align: center; background-color: #1E1E1E; padding: 20px; border-radius: 10px;'>
                                <h1 style='font-size: 100px; margin: 0;'>{top_emoji}</h1>
                                <p style='font-size: 20px; margin-top: 10px;'>{top_count} kez kullanıldı</p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                else:
                    st.info("Bu sohbette hiç emoji bulunamadı. 😐")
            else:
                st.warning("Mesaj sütunu otomatik tespit edilemedi.")

    with tab2:
        st.subheader("💬 Yapay Zeka Asistanı")
        with st.expander("💡 Örnek Sorular", expanded=True):
            st.markdown("- 🧐 Bu grubun genel amacı ne?\n- 🔥 En hararetli tartışma neydi?\n- 😂 En komik anları özetle.\n- 🏆 Grubun 'gizli lideri' kim?")
        
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages: st.chat_message(m["role"]).markdown(m["content"])
        if prompt := st.chat_input("Sorunuzu yazın..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Analiz ediliyor..."):
                    try:
                        response = model.generate_content(f"Veri:\n{text_data}\n\nSoru: {prompt}")
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e: st.error(f"Hata: {e}")