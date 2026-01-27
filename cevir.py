import pandas as pd
import re

# Dosya isimleri
GIRIS_DOSYASI = "chat.txt"
CIKIS_DOSYASI = "yuklenecek_veri.xlsx"

try:
    # 1. Metin dosyasını oku
    with open(GIRIS_DOSYASI, 'r', encoding='utf-8') as f:
        data = f.read()

    # 2. WhatsApp formatına göre parçala
    # (Tarih - Saat - İsim - Mesaj)
    pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})\s(\d{1,2}:\d{2})\s-\s(.*?):\s(.*)'
    mesajlar = re.findall(pattern, data)

    # 3. Tabloya çevir
    df = pd.DataFrame(mesajlar, columns=['Tarih', 'Saat', 'Gonderen', 'Mesaj'])
    
    # 4. "Tip" sütunu ekle (Herkesi 'Kullanıcı' varsayıyoruz)
    df['Tip'] = 'Kullanıcı'

    # 5. Excel olarak kaydet
    df.to_excel(CIKIS_DOSYASI, index=False)
    
    print(f"✅ BAŞARILI! '{CIKIS_DOSYASI}' dosyası oluşturuldu.")
    print("Şimdi bu dosyayı siteye yükleyebilirsin.")

except Exception as e:
    print(f"❌ Hata oluştu: {e}")
    