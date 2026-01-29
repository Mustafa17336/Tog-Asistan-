import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import altair as alt
import os
import emoji
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re

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
        'Tarih': ['01.01.2026']*4 + ['02.01.2026']*4,
        'Saat': ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'],
        'Gönderen': ['+90 532 100 20 30']*4 + ['Ayşe']*4,
        'Mesaj': ['Selam proje harika 🥳', 'Naber? Toplantı ne zaman? 👍🏻', 'Harika iş çıkardık! 🔥', 'Görüşürüz yarın 👋', 'Toplantı iptal mi?', 'Proje bitti mi?', 'Evet bitti 👍🏻', 'Kutlama yapalım 🥳'],
        'Tip': ['Yazı']*8
    }
    return pd.DataFrame(data)

def emojileri_ayikla(text):
    emoji_listesi = emoji.emoji_list(str(text))
    return [item['emoji'] for item in emoji_listesi]

def kelime_bulutu_olustur(df, mesaj_sutunu):
    agresif_yasaklar = {
        "bir", "iki", "üç", "ve", "ile", "de", "da", "bu", "şu", "o", "ben", "sen", "biz", "siz", 
        "onlar", "bana", "sana", "bize", "size", "benim", "senin", "bizim", "sizin", "bende", 
        "sende", "bizde", "sizde", "bunu", "şunu", "onu", "buna", "şuna", "ona", "böyle", "şöyle",
        "öyle", "var", "yok", "için", "gibi", "kadar", "diye", "ise", "ki", "mu", "mi", "mı",
        "ama", "fakat", "lakin", "ancak", "veya", "ya", "hem", "eğer", "zaten", "hani", "işte",
        "yani", "dolayı", "ötürü", "üzere", "rağmen", "karşı", "kendi", "kendine", "kendim","icin","çünkü",
        "konuda","halde","icin",
        "mesaj", "silindi", "medya", "dahil", "edilmedi", "görüntü", "video", "ses", "dosya",
        "kişisi", "tarafından", "eklendi", "ayrıldı", "katıldı", "grup", "gruba", "bağlantısıyla",
        "davet", "link", "https", "http", "www", "com", "tr", "android", "iphone", "web",
        "evet", "hayır", "tamam", "peki", "olur", "olmaz", "şey", "çok", "daha", "en", "biraz",
        "az", "fazla", "kadar", "sadece", "tek", "bence", "sence", "galiba", "sanırım", "belki",
        "keşke", "neyse", "tabi", "tabii", "aynen", "kesinlikle", "mutlaka", "lütfen", "rica",
        "teşekkürler", "sağol", "selam", "merhaba", "günaydın", "iyi", "güzel", 
        "kötü", "hoş", "falan", "filan", "ne", "nasıl", "neden", "niye", "hangi", "kim", "kimse",
        "her", "herkes", "hiç", "hep", "tüm", "bütün", "zaman", "şimdi", "sonra", "önce", "bugün",
        "yarın", "dün", "sabah", "akşam", "gece", "saat", "gün", "hafta", "ay", "yıl",
        "olan", "olarak", "oldu", "olmuş", "olacak", "olsun", "olursa", "olduğu", "olmak",
        "yapalım", "yaparız", "yaptım", "yapmak", "yapıyor", "geldi", "gitti", "geliyor", "gidiyor",
        "tekrar", "devam", "başka", "yine", "farklı", "lazım", "gerek", "isteyen",
        "arkadaşlar", "arkadaşlarr", "selammm", "orada", "burada", "şuan", "varsa", "yoksa", "hemen",
        "uygun", "müsait", "katılmak", "düşünüyorum", "yardımcı", "bilmiyorum","değil", "çok", "cok", "arada", "yer", "aynı", "ilk", "bile", 
        "artık", "buna", "bunu", "şeyler", "diğer", "aslında", "hadi",
        "olmasın", "herkese", "belli", "başka", "süper", "onun", "bizi",
        "kabul", "yüzden", "yeni", "son", "göre", "kısmı", "türlü",
        "düzenlendi", "gerçekten", "zaten", "herhangi", "farklı","yaa","valla","yaaa","miyiz","beni","orda","ederim","dpdndşdnd",
        "arası","şekilde","dedim","istiyorum","isterim","isteyenler","projesi","olması","olurum","aaa","günü","oluyor","olabilir",
        "iletişime","adına","okula"
    }

    def metni_temizle(text):
        text = str(text).lower() 
        text = re.sub(r'http\S+', '', text) 
        text = re.sub(r'www\S+', '', text)
        text = text.replace("bu mesaj silindi", "") 
        text = text.replace("<medya dahil edilmedi>", "")
        text = re.sub(r'[^\w\s]', '', text) 
        return text

    temiz_seri = df[mesaj_sutunu].dropna().apply(metni_temizle)
    text = " ".join(temiz_seri.tolist())
    
    if not text.strip(): return None

    wordcloud = WordCloud(
        width=1600, 
        height=800, 
        background_color='#0E1117',
        colormap='viridis',
        stopwords=agresif_yasaklar,
        min_font_size=10,
        min_word_length=3,
        collocations=False,
        max_words=100
    ).generate(text)
    
    return wordcloud

# ---------------------------------------------------------
# 3. ARAYÜZ
# ---------------------------------------------------------
st.title("📊 Sohbet Analiz Paneli")
st.sidebar.header("1. Veri Kaynağı Seçin")

secim = st.sidebar.radio("Seçenekler:", ["📂 Kendi Dosyamı Yükle", "🧪 Demo Modu (Sentetik)"])

df = None

if secim == "📂 Kendi Dosyamı Yükle":
    uploaded_file = st.sidebar.file_uploader("WhatsApp Excel'i Yükle", type=["xlsx", "xls"])
    if uploaded_file:
        try: df = pd.read_excel(uploaded_file)
        except Exception as e: st.error(f"Hata: {e}")

elif secim == "🧪 Demo Modu (Sentetik)":
    df = demo_veri_olustur()
    st.sidebar.info("🧪 Demo modu aktif.")

# --- İMZA ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍💻 Geliştirici")
st.sidebar.caption("Bu proje **Gemini 2.5 Flash** altyapısı kullanılarak geliştirilmiştir.")
st.sidebar.info("**Fatih Sarı**\nMarmara Üniv. İstatistik 📉")

# ---------------------------------------------------------
# 4. ANALİZ MOTORU
# ---------------------------------------------------------
if df is not None:
    cols = df.columns
    col_isim = next((c for c in cols if any(x in c.lower() for x in ['onderen','ender','author','sender'])), cols[0])
    col_tarih = next((c for c in cols if any(x in c.lower() for x in ['arih','date','ime'])), cols[1] if len(cols)>1 else cols[0])
    col_mesaj = next((c for c in cols if any(x in c.lower() for x in ['mesaj','message','icerik','text'])), cols[-1])

    chat_df = df.iloc[::-1]
    text_data = ""
    for index, row in chat_df.head(3000).iterrows():
        text_data += " | ".join([str(val) for val in row.values]) + "\n"

    tab1, tab2 = st.tabs(["📈 İstatistik Paneli", "💬 Yapay Zeka Asistanı"])

    with tab1:
        st.markdown("### 🚀 Genel Bakış")
        c1, c2 = st.columns(2)
        with c1: selected_user_col = st.selectbox("Kişi Sütunu:", cols, index=cols.get_loc(col_isim))
        with c2: selected_date_col = st.selectbox("Zaman Sütunu:", cols, index=cols.get_loc(col_tarih))

        if selected_user_col and selected_date_col:
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Mesaj", len(df))
            m2.metric("Aktif Kişi", df[selected_user_col].nunique())
            m3.metric("Lider", str(df[selected_user_col].mode()[0])[:15]+"...")
            st.divider()

            g1, g2 = st.columns(2)
            
            # --- GRAFİK 1: EN ÇOK YAZANLAR (ALTAIR - SOL GRAFİK) ---
            with g1:
                st.subheader("🏆 En Çok Yazanlar")
                try:
                    uc = df[selected_user_col].value_counts().head(10).reset_index()
                    uc.columns = ["Deger", "Adet"] 
                    
                    chart = alt.Chart(uc).mark_bar().encode(
                        x=alt.X('Adet', title='Mesaj Sayısı'), 
                        y=alt.Y('Deger', sort='-x', title=selected_user_col),
                        color=alt.value("#3182bd"),
                        tooltip=['Deger', 'Adet']
                    ).properties(height=350)
                    
                    st.altair_chart(chart, use_container_width=True)
                except Exception as e: st.warning(f"Grafik hatası: {e}")

            # --- GRAFİK 2: ZAMAN ANALİZİ (PLOTLY - SAĞ GRAFİK - TAMİR EDİLDİ) ---
            with g2:
                st.subheader("📊 Zaman Analizi")
                try:
                    # Senaryo A: Eğer sütun "Saat" içeriyorsa -> Sadece Saati (00-23) al
                    if any(x in selected_date_col.lower() for x in ['saat','time','hour']):
                        # Saatleri temizle (Sadece ilk 2 haneyi al: "14:39" -> "14")
                        df['TempSaat'] = df[selected_date_col].astype(str).str[:2]
                        tc = df['TempSaat'].value_counts().reset_index()
                        tc.columns = ["Saat", "Adet"]
                        tc = tc.sort_values("Saat")
                        
                        fig_time = px.bar(tc, x='Saat', y='Adet', color='Adet', color_continuous_scale='Oranges')
                        fig_time.update_layout(xaxis_title="Saat Dilimi (00-23)", yaxis_title="Mesaj Sayısı")
                        st.plotly_chart(fig_time, use_container_width=True)
                    
                    # Senaryo B: Tarih ise
                    else:
                        d = pd.to_datetime(df[selected_date_col], dayfirst=True, errors='coerce').dropna()
                        if d.empty:
                            st.warning("⚠️ Seçilen sütunda tarih verisi okunamadı. Lütfen 'Tarih' sütununu seçin.")
                        else:
                            dc = df.groupby(d.dt.date).size().reset_index(name='GunlukMesaj')
                            dc.columns = ['Tarih', 'GunlukMesaj']
                            fig_date = px.area(dc, x='Tarih', y='GunlukMesaj', color_discrete_sequence=['#2ecc71'])
                            st.plotly_chart(fig_date, use_container_width=True)
                            
                except Exception as e: st.error(f"Zaman grafiği hatası: {e}")

            st.divider()

            # --- KELİME BULUTU ---
            st.markdown("### ☁️ Kelime Bulutu")
            if col_mesaj and col_mesaj in df.columns:
                try:
                    wc = kelime_bulutu_olustur(df, col_mesaj)
                    if wc:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        fig.patch.set_facecolor('#0E1117') 
                        ax.imshow(wc, interpolation='bilinear')
                        ax.axis("off")
                        st.pyplot(fig)
                    else: st.info("Veri yok.")
                except Exception as e: st.error(f"Hata: {e}")
            
            st.divider()

            # --- EMOJİ ANALİZİ ---
            st.markdown("### 🤩 Emoji Analizi")
            if col_mesaj and col_mesaj in df.columns:
                try:
                    all_text = " ".join(df[col_mesaj].dropna().astype(str).tolist())
                    found_emojis = emojileri_ayikla(all_text)

                    if found_emojis:
                        from collections import Counter
                        emoji_counts = Counter(found_emojis).most_common(10)
                        emoji_df = pd.DataFrame(emoji_counts, columns=['Emoji', 'Adet'])
                        
                        e1, e2 = st.columns([2, 1])
                        with e1:
                            st.subheader("En Çok Kullanılan Emojiler")
                            fig = px.bar(emoji_df, x='Emoji', y='Adet', text='Adet', color='Adet', color_continuous_scale='Viridis')
                            fig.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False, height=400)
                            fig.update_xaxes(tickfont=dict(size=24))
                            st.plotly_chart(fig, use_container_width=True)
                        with e2:
                            top_emoji = emoji_df.iloc[0]['Emoji']
                            top_count = emoji_df.iloc[0]['Adet']
                            st.subheader("Lider Emoji 👑")
                            st.markdown(f"<div style='text-align: center; background-color: #1E1E1E; padding: 20px; border-radius: 10px;'><h1 style='font-size: 100px; margin: 0;'>{top_emoji}</h1><p style='font-size: 20px; margin-top: 10px;'>{top_count} kez kullanıldı</p></div>", unsafe_allow_html=True)
                    else: st.info("Emoji bulunamadı.")
                except Exception as e: st.error(f"Emoji hatası: {e}")

    with tab2:
        st.subheader("💬 Yapay Zeka Asistanı")
        with st.expander("💡 Örnek Sorular", expanded=True):
            st.markdown("""
            - 🧐 Grup hakkında bana neler söyleyebilirsin?
            - 🧠 Grubun genel kişilik analizini çıkarabilir misin?
            - 🕵️‍♂️ Grubun gizli lideri kim?
            - 🤝 Kimler birbiriyle daha iyi anlaşıyor?
            - 📅 Yakın zamanda planlanan bir etkinlik var mı?
            - 🍂 Kasım ayında neler yapılmış?
            """)

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
                    except Exception as e: st.error(f"Hata: {e}")