# 🛸 Neon Hesap Makinesi (Neon Calculator)

<p align="center">
  <img src="1.png" alt="Neon Calculator Logo" width="600">
</p>

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/UI-PyQt5-green?style=for-the-badge&logo=qt)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

**Modern, estetik ve yüksek hassasiyetli hesaplamalar için tasarlanmış, Python ve PyQt5 tabanlı bir masaüstü hesap makinesi uygulaması.**

---

## ✨ Öne Çıkan Özellikler

* **🧪 Yüksek Hassasiyet:** `Decimal` modülü sayesinde 15 ile 69 basamak arasında değişen aşırı yüksek hassasiyetle işlem yapabilme.
* **📐 Gelişmiş Karekök Desteği:** İç içe geçmiş karekök ifadelerini ve parantezli karmaşık matematiksel yapıları doğru bir şekilde analiz edip çözebilen özel işlem motoru.
* **🌈 Dinamik Neon Temalar:**
    * **Karanlık & Aydınlık Mod:** Göz yormayan karanlık mod veya temiz bir görünüm sunan aydınlık mod seçeneği.
    * **Renk Döngüsü:** Kullanıcı zevkine göre ayarlanabilir neon renk seçenekleri.
* **📜 Akıllı İşlem Geçmişi:**
    * Yapılan tüm işlemler yerel olarak kaydedilir.
    * Geçmiş penceresinden eski işlemlere veya sonuçlara tek tıkla geri dönülebilir.
    * İşlem geçmişini `.txt` dosyası olarak dışa aktarma imkanı.
* **⌨️ Tam Klavye Desteği:** Sayılar, Operatörler, Enter, Backspace ve Esc ile tam entegrasyon.

---

## 🛠 Teknik Detaylar

| Bileşen | Detay |
| :--- | :--- |
| **Dil** | Python 3 |
| **Arayüz Kitaplığı** | PyQt5 |
| **Hassasiyet Yönetimi** | Python `decimal` kütüphanesi |
| **Yapılandırma** | `~/.neon_calc_config` dosyasında saklanır |

---

## 🚀 Kurulum ve Çalıştırma

Uygulamanın çalışması için sisteminizde `python3-pyqt5` bağımlılığı yüklü olmalıdır.

### 1. Bağımlılık Kurulumu
```bash
sudo apt update && sudo apt install python3-pyqt5 -y
