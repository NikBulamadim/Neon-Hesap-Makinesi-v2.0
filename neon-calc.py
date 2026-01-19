# this neon calc open source

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Geliştirme Notları:
#
# Kodu okudum ve kodu az da olsa anlayabildim.
# PyQt kütüphanesini unutmuş olsamda eski deneyimlerim var.
# Ölçeklendirme sorununu çözdüm ve hakkında sayfası ekledim.
# Ve rastgele sayı ekleme özelliği de ekledim, bence eğlenceli bir özellik.
# Bu benim için eğlenceli bir deneyim oldu. Gerçekten düzenli yazılmış.
# Ayrıca R tuşuna da fonksiyon atadım, En zevfkli yeri orsıydı. 
# - github.com/YigitC7 - yigitc7.com.tr

import sys
import os
import re
from decimal import Decimal, getcontext
from random import randint 

if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    if os.path.exists("/usr/bin/Xwayland") or os.path.exists("/usr/bin/X"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    # Yüksek DPI desteği
    # YigitC7 Tarafından eklendi :)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QTextEdit, QPushButton,
    QMenu, QHBoxLayout, QSpacerItem, QSizePolicy, QDialog, QLabel,
    QScrollArea, QActionGroup, QColorDialog, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor, QTextOption, QColor

getcontext().prec = 69

AYAR_DOSYASI = os.path.expanduser("~/.neon_calc_config")
GECMIS_DOSYASI = os.path.expanduser("~/.neon_calc_history")

AYARLAR_NEON_MOR = "#D500F9"
NEON_YESIL = "#39FF14"
NEON_KIRMIZI = "#FF3131"
NEON_MAVI = "#00D4FF"
NEON_MOR = "#5800FF"
NEON_SARI = "#FFF600"

InfoWindowCss = ("""
            QWidget {
                background-color: #121212;
            }
            QLabel {
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #Baslik {
                color: #00ADB5; 
                font-size: 20px;
                font-weight: bold;
                padding-bottom: 5px;
            }
            #Icerik {
                font-size: 15px;
                background-color: #1E1E1E;
                border-radius: 10px;
                padding: 15px;
            }
            #AltBilgi {
                color: #666666;
                font-size: 11px;
            }
    """)

DARK_USER_COLORS_DEFAULT = {
    "numbers": "#00ff9d",
    "operators": "#00c2ff",
    "danger": "#ff4d4d",
    "screen": "#e0e0e0",
    "screen_border": "#444444"
}

LIGHT_USER_COLORS_DEFAULT = {
    "numbers": "#2c3e50",
    "operators": "#34495e",
    "danger": "#c0392b",
    "screen": "#000000",
    "screen_border": "#666666"
}

class ClickableLabel(QLabel):
    def __init__(self, text, ana_pencere, yazi_rengi):
        super().__init__(text)
        self.ana_pencere = ana_pencere
        self.tam_metin = text
        self.setWordWrap(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QLabel {{
                color: {yazi_rengi};
                background-color: rgba(0, 0, 0, 0.2);
                border: 1.1px solid {yazi_rengi}66;
                border-radius: 8px;
                padding: 3px 6px;
                margin: 2px 4px;
                font-size: 13px;
                font-weight: 500;
            }}
            QLabel:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1.5px solid {yazi_rengi};
            }}
        """)

    def mousePressEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #1A1A1A;
                color: {AYARLAR_NEON_MOR};
                border: 2px solid {AYARLAR_NEON_MOR};
                font-family: 'Liberation Sans';
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {AYARLAR_NEON_MOR};
            }}
            QMenu::item:selected {{
                background-color: {AYARLAR_NEON_MOR};
                color: #000000;
            }}
        """)

        if self.tam_metin.startswith("HATA: "):
            islem_kismi = self.tam_metin.replace("HATA: ", "")
            act_islem = menu.addAction("Hatalı İşlemi Geri Al ve Düzelt")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == act_islem:
                self.ana_pencere.matematik_ifadesi = islem_kismi
                self.ana_pencere.ekran_guncelle()
            return

        parts = self.tam_metin.split(" = ")
        islem_kismi = parts[0] if len(parts) > 0 else ""
        sonuc_kismi = parts[1] if len(parts) > 1 else ""

        act_islem = menu.addAction("İşlemi Geri Al")
        act_sonuc = menu.addAction("Sonucu Geri Al")
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action:
            if action == act_islem:
                self.ana_pencere.matematik_ifadesi = islem_kismi
            elif action == act_sonuc:
                self.ana_pencere.matematik_ifadesi = sonuc_kismi
            self.ana_pencere.ekran_guncelle()


class GecmisPenceresi(QDialog):
    def __init__(self, ana_pencere):
        super().__init__(ana_pencere)
        self.ana_pencere = ana_pencere
        self.setWindowTitle("İşlem Geçmişi")
        self.setFixedSize(320, 480)

        self.bg_color = "#00E5FF"
        self.yazi_rengi = "#000000"
        self.kenarlik = "#00838F"
        self.buton_bg = "#00B8D4"

        self.setStyleSheet(f"QDialog {{ background-color: {self.bg_color}; border: 2px solid {self.kenarlik}; }}")

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        baslik = QLabel("İŞLEM GEÇMİŞİ")
        baslik.setStyleSheet(f"color: {self.yazi_rengi}; font-weight: bold; border: none; font-size: 20px; padding: 10px; font-family: 'Liberation Sans'; background: transparent;")
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setAttribute(Qt.WA_TranslucentBackground)
        self.scroll.viewport().setStyleSheet("background: transparent;")

        self.liste_container = QWidget()
        self.liste_container.setAttribute(Qt.WA_TranslucentBackground)
        self.liste_container.setStyleSheet("background: transparent;")

        self.liste_layout = QVBoxLayout(self.liste_container)
        self.liste_layout.setAlignment(Qt.AlignTop)
        self.liste_layout.setSpacing(2)

        self.scroll.setWidget(self.liste_container)
        layout.addWidget(self.scroll)

        buton_layout = QHBoxLayout()
        btn_stil = f"""
            QPushButton {{
                color: {self.yazi_rengi};
                background-color: {self.buton_bg};
                border: 2px solid {self.yazi_rengi};
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Liberation Sans';
            }}
            QPushButton:hover {{
                background-color: {self.yazi_rengi};
                color: {self.bg_color};
            }}
        """

        self.temizle_btn = QPushButton("Temizle")
        self.temizle_btn.setStyleSheet(btn_stil)
        self.temizle_btn.clicked.connect(self.gecmis_sil)

        self.disa_aktar_btn = QPushButton("Kaydet")
        self.disa_aktar_btn.setStyleSheet(btn_stil)
        self.disa_aktar_btn.clicked.connect(self.gecmisi_dosya_secerek_kaydet)

        self.kapat_btn = QPushButton("Kapat")
        self.kapat_btn.setStyleSheet(btn_stil)
        self.kapat_btn.clicked.connect(self.accept)

        buton_layout.addWidget(self.temizle_btn)
        buton_layout.addWidget(self.kapat_btn)
        buton_layout.addWidget(self.disa_aktar_btn)

        layout.addLayout(buton_layout)
        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.liste_guncelle()

    def liste_guncelle(self):
        while self.liste_layout.count():
            child = self.liste_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.ana_pencere.gecmis_listesi:
            yok_label = QLabel("Kayıtlı işlem bulunmuyor.")
            yok_label.setStyleSheet(f"color: {self.yazi_rengi}; border: none; font-style: italic; padding: 40px; font-size: 15px; background: transparent;")
            yok_label.setAlignment(Qt.AlignCenter)
            self.liste_layout.addWidget(yok_label)
        else:
            for islem in reversed(self.ana_pencere.gecmis_listesi):
                lbl = ClickableLabel(islem, self.ana_pencere, self.yazi_rengi)
                self.liste_layout.addWidget(lbl)

    def gecmis_sil(self):
        self.ana_pencere.gecmis_temizle_kalici()
        self.liste_guncelle()

    def gecmisi_dosya_secerek_kaydet(self):
        dosya_yolu, _ = QFileDialog.getSaveFileName(
            self, "Geçmişi Kaydet", "hesap_gecmisi.txt", "Metin Dosyaları (*.txt)"
        )
        if dosya_yolu:
            try:
                with open(dosya_yolu, "w", encoding="utf-8") as dosya:
                    dosya.write("--- NEON HESAP MAKİNESİ GEÇMİŞİ ---\n")
                    for islem in self.ana_pencere.gecmis_listesi:
                        dosya.write(islem + "\n")
                self.disa_aktar_btn.setText("Kaydedildi!")
                QTimer.singleShot(2000, lambda: self.disa_aktar_btn.setText("Kaydet"))
            except Exception as e:
                print(f"Hata: {e}")


class NeonHesapMakinesi(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neon Hesap Makinesi")
        self.setFixedSize(340, 575)

        ayarlar = self.hafizadan_yukle()
        self.renk_modu_karanlik = ayarlar[0]
        self.renk_modu_aydinlik = ayarlar[1]
        self.tema_modu = ayarlar[2]
        self.hassasiyet = ayarlar[3]

        self.dark_user_colors = DARK_USER_COLORS_DEFAULT.copy()
        self.light_user_colors = LIGHT_USER_COLORS_DEFAULT.copy()

        self.load_user_colors()

        self.setWindowIcon(QtGui.QIcon("/usr/share/pixmaps/neon-calc.png"))

        self.matematik_ifadesi = ""
        self.font_name = "Liberation Sans"
        self.butonlar = {}
        self.gecmis_penceresi = None
        self.gecmis_listesi = self.gecmis_yukle_kalici()

        getcontext().prec = self.hassasiyet

        self.init_ui()
        self.tema_uygula()

        self.ekran.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ekran.customContextMenuRequested.connect(self.show_ekran_context_menu)

    def load_user_colors(self):
        try:
            if os.path.exists(AYAR_DOSYASI):
                with open(AYAR_DOSYASI, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("dark_user_color_"):
                            key = line.split("=", 1)[0].replace("dark_user_color_", "")
                            value = line.split("=", 1)[1]
                            if key in self.dark_user_colors:
                                self.dark_user_colors[key] = value
                        elif line.startswith("light_user_color_"):
                            key = line.split("=", 1)[0].replace("light_user_color_", "")
                            value = line.split("=", 1)[1]
                            if key in self.light_user_colors:
                                self.light_user_colors[key] = value
        except:
            pass

    def save_user_colors(self):
        try:
            lines = []
            if os.path.exists(AYAR_DOSYASI):
                with open(AYAR_DOSYASI, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip().startswith(("dark_user_color_", "light_user_color_", "hassasiyet=", "renk_modu_", "tema_modu=")):
                            lines.append(line + "\n")

            with open(AYAR_DOSYASI, "w", encoding="utf-8") as f:
                f.writelines(lines)
                f.write(f"hassasiyet={self.hassasiyet}\n")
                f.write(f"renk_modu_karanlik={self.renk_modu_karanlik}\n")
                f.write(f"renk_modu_aydinlik={self.renk_modu_aydinlik}\n")
                f.write(f"tema_modu={self.tema_modu}\n")
                for k, v in self.dark_user_colors.items():
                    f.write(f"dark_user_color_{k}={v}\n")
                for k, v in self.light_user_colors.items():
                    f.write(f"light_user_color_{k}={v}\n")
        except Exception as e:
            print("Ayar kaydetme hatası:", e)

    def hafizadan_yukle(self):
        try:
            if os.path.exists(AYAR_DOSYASI):
                with open(AYAR_DOSYASI, "r", encoding="utf-8") as f:
                    data = {}
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split("=", 1)
                            data[key] = value

                    renk_karanlik = int(data.get("renk_modu_karanlik", 1))
                    renk_aydinlik = int(data.get("renk_modu_aydinlik", 1))
                    tema = int(data.get("tema_modu", 0))

                    hass_str = data.get("hassasiyet", "69")
                    try:
                        hass = int(hass_str)
                        if hass not in [15, 22, 33, 69]:
                            hass = 69
                    except:
                        hass = 69

                    return (renk_karanlik, renk_aydinlik, tema, hass)
        except Exception as e:
            print(f"Ayar yükleme hatası: {e}")

        return (1, 1, 0, 69)

    def hafizaya_kaydet(self):
        try:
            with open(AYAR_DOSYASI, "w", encoding="utf-8") as f:
                f.write(f"hassasiyet={self.hassasiyet}\n")
                f.write(f"renk_modu_karanlik={self.renk_modu_karanlik}\n")
                f.write(f"renk_modu_aydinlik={self.renk_modu_aydinlik}\n")
                f.write(f"tema_modu={self.tema_modu}\n")
                for k, v in self.dark_user_colors.items():
                    f.write(f"dark_user_color_{k}={v}\n")
                for k, v in self.light_user_colors.items():
                    f.write(f"light_user_color_{k}={v}\n")
        except Exception as e:
            print("Ayar kaydetme hatası:", e)

    def gecmis_yukle_kalici(self):
        try:
            if os.path.exists(GECMIS_DOSYASI):
                with open(GECMIS_DOSYASI, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"Geçmiş yükleme hatası: {e}")
        return []

    def gecmis_kaydet_kalici(self, satir):
        try:
            with open(GECMIS_DOSYASI, "a", encoding="utf-8") as f:
                f.write(satir + "\n")
        except Exception as e:
            print(f"Geçmiş kaydetme hatası: {e}")

    def gecmis_temizle_kalici(self):
        self.gecmis_listesi = []
        try:
            if os.path.exists(GECMIS_DOSYASI):
                os.remove(GECMIS_DOSYASI)
        except:
            pass
            
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 15)
        layout.setSpacing(8)

        ust_bar = QHBoxLayout()
        ust_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(40, 30)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFocusPolicy(Qt.NoFocus)

        # Benim(Yiğit) Eklediğim iki buton:
        self.info_btn = QPushButton("Hakkında")
        self.info_btn.setFixedSize(87, 30)
        self.info_btn.setStyleSheet("QPushButton{color:white;}")
        self.info_btn.setCursor(Qt.PointingHandCursor)
        self.info_btn.setFocusPolicy(Qt.NoFocus)

        self.random_btn = QPushButton("Rastgele sayı")
        self.random_btn.setFixedSize(117, 30)
        self.random_btn.setStyleSheet("QPushButton{color:white;}")
        self.random_btn.setCursor(Qt.PointingHandCursor)
        self.random_btn.setFocusPolicy(Qt.NoFocus)


        self.menu = QMenu(self)
        self.gecmis_act = self.menu.addAction("İşlem Geçmişi")
        self.menu.addSeparator()
        self.light_tema_act = self.menu.addAction("Aydınlık Tema")
        self.dark_tema_act = self.menu.addAction("Karanlık Tema")
        self.menu.addSeparator()

        hassasiyet_menu = self.menu.addMenu("Hassasiyet (Basamak)")
        hassasiyet_group = QActionGroup(self)
        hassasiyet_group.setExclusive(True)

        act_15 = hassasiyet_menu.addAction("15 Basamaklı Sonuç")
        act_22 = hassasiyet_menu.addAction("22 Basamaklı Sonuç")
        act_33 = hassasiyet_menu.addAction("33 Basamaklı Sonuç")
        act_69 = hassasiyet_menu.addAction("69 Basamaklı Sonuç")

        for act in [act_15, act_22, act_33, act_69]:
            act.setCheckable(True)
            hassasiyet_group.addAction(act)

        act_15.triggered.connect(lambda checked=False: self.hassasiyet_kaydet(15))
        act_22.triggered.connect(lambda checked=False: self.hassasiyet_kaydet(22))
        act_33.triggered.connect(lambda checked=False: self.hassasiyet_kaydet(33))
        act_69.triggered.connect(lambda checked=False: self.hassasiyet_kaydet(69))

        acts = {15: act_15, 22: act_22, 33: act_33, 69: act_69}
        current_hass = self.hassasiyet
        if current_hass in acts:
            acts[current_hass].setChecked(True)

        
        self.custom_colors_act = self.menu.addAction("Renkleri Özelleştir...")
        self.custom_colors_act.triggered.connect(self.show_custom_colors_dialog)

        self.settings_btn.setMenu(self.menu)
        self.info_btn.clicked.connect(self.Info_Window)
        self.random_btn.clicked.connect(lambda: self.aksiyon( sembol=str(randint(1,9))))

        self.light_tema_act.triggered.connect(lambda: self.tema_degistir(1))
        self.dark_tema_act.triggered.connect(lambda: self.tema_degistir(0))       
        self.gecmis_act.triggered.connect(self.gecmisi_goster)

        ust_bar.addWidget(self.random_btn)
        ust_bar.addWidget(self.info_btn)
        ust_bar.addWidget(self.settings_btn)
        
        layout.addLayout(ust_bar)

        self.ekran = QTextEdit()
        self.ekran.setReadOnly(True)
        self.ekran.setFocusPolicy(Qt.NoFocus)
        self.ekran.setWordWrapMode(QTextOption.WrapAnywhere)
        self.ekran.setFixedHeight(100)
        self.ekran.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ekran.setText("0")
        self.ekran.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.ekran)

        self.grid = QGridLayout()
        self.grid.setSpacing(5)

        self.tus_haritasi = [
            ('C', 0, 0, 1, 1), ('(', 0, 1, 1, 1), (')', 0, 2, 1, 1), ('/', 0, 3, 1, 1),
            ('7', 1, 0, 1, 1), ('8', 1, 1, 1, 1), ('9', 1, 2, 1, 1), ('*', 1, 3, 1, 1),
            ('4', 2, 0, 1, 1), ('5', 2, 1, 1, 1), ('6', 2, 2, 1, 1), ('-', 2, 3, 1, 1),
            ('1', 3, 0, 1, 1), ('2', 3, 1, 1, 1), ('3', 3, 2, 1, 1), ('+', 3, 3, 1, 1),
            ('0', 4, 0, 1, 2), ('.', 4, 2, 1, 1), ('=', 4, 3, 2, 1),
            ('BACK', 5, 0, 1, 2), ('√', 5, 2, 1, 1)
        ]

        self.butonlari_olustur()
        layout.addLayout(self.grid)

        self.setLayout(layout)

   # 1. Hatanın sebebi olan eksik fonksiyonu ekliyoruz
    def show_custom_colors_dialog(self):
        """Hata veren kısım: Buraya renk seçici veya ilgili ayarı ekleyebilirsin"""
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            print("Seçilen Renk:", color.name())
            # Burada hesap makinesinin renklerini değiştirecek kodları yazabilirsin

    # İşte Benim Ekldiğim Hakkında Penceresi.
    # Biraz uğraştırdı. ama güzel oldu
    def Info_Window(self):
        self.InfoWin = QWidget()
        self.InfoWin.setWindowTitle("Geliştirici Bilgileri")
        self.InfoWin.setFixedSize(400, 320)

        self.InfoWin.setStyleSheet(InfoWindowCss)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        baslik = QLabel("NEON HESAP MAKİNESİ")
        baslik.setObjectName("Baslik")
        baslik.setAlignment(Qt.AlignCenter)

        info = QLabel(
            "<div style='text-align: center;'>"
            "<a href='https://github.com/NikBulamadim'><b>Berkay Çınar Başpınar</b></a><br>"
            "<span style='color: #888;'>Yapımcı & Baş Geliştirici</span><br><br>"
            "<a href='https://github.com/yigitc7'><b>Yiğit Çıtak</b></a><br>"
            "<span style='color: #888;'>Geliştirici</span>"
            "</div>"
        )
        info.setObjectName("Icerik")
        info.setWordWrap(True)
        info.setOpenExternalLinks(True)
        info.setTextInteractionFlags(Qt.LinksAccessibleByMouse)

        alt_bilgi = QLabel("v2 | 2026 Neon Calc")
        alt_bilgi.setObjectName("AltBilgi")
        alt_bilgi.setAlignment(Qt.AlignCenter)

        layout.addWidget(baslik)
        layout.addWidget(info)
        layout.addStretch()
        layout.addWidget(alt_bilgi)

        self.InfoWin.setLayout(layout)
        self.InfoWin.show()

    def hassasiyet_kaydet(self, yeni_hassasiyet):
        try:
            if isinstance(yeni_hassasiyet, str):
                yeni_hassasiyet = int(yeni_hassasiyet.strip())

            if yeni_hassasiyet not in [15, 22, 33, 69]:
                yeni_hassasiyet = 69

            self.hassasiyet = yeni_hassasiyet
            getcontext().prec = yeni_hassasiyet
            self.hafizaya_kaydet()
            self.ekran_guncelle()
        except Exception as e:
            print(f"Hassasiyet ayarlama hatası: {e}")
            self.hassasiyet = 69
            getcontext().prec = 69
            self.hafizaya_kaydet()
            self.ekran_guncelle()

    def show_custom_colors_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Renk Özelleştir ({'Aydınlık' if self.tema_modu == 1 else 'Karanlık'} Tema)")
        dialog.setMinimumWidth(500)

        if self.tema_modu == 1:
            dialog.setStyleSheet("""
                QDialog { background-color: #f8f9fa; color: #212529; }
                QLabel { color: #212529; }
                QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 6px; }
                QPushButton:hover { background-color: #2980b9; }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog { background-color: #1e1e1e; color: #e0e0e0; }
                QLabel { color: #e0e0e0; }
                QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 6px; }
                QPushButton:hover { background-color: #2980b9; }
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Renkleri Özelleştir")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        current_colors = self.light_user_colors if self.tema_modu == 1 else self.dark_user_colors

        def create_picker(key, title_text):
            row = QHBoxLayout()
            row.setSpacing(15)

            lbl = QLabel(title_text)
            lbl.setStyleSheet(f"""
                color: {'#212529' if self.tema_modu == 1 else '#e0e0e0'};
                font-size: 14px;
                background: transparent;
                padding: 6px 0;
            """)
            lbl.setMinimumWidth(320)

            current = current_colors.get(key, "#ffffff")
            btn = QPushButton("Seç")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {current};
                    color: {'#000000' if self.is_light_color(current) else '#ffffff'};
                    min-width: 120px;
                    padding: 10px;
                    border: 1px solid #6c757d;
                    border-radius: 6px;
                }}
            """)

            def pick():
                col = QColorDialog.getColor(QColor(current), dialog)
                if col.isValid():
                    hex_val = col.name()
                    current_colors[key] = hex_val
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {hex_val};
                            color: {'#000000' if self.is_light_color(hex_val) else '#ffffff'};
                            min-width: 120px;
                            padding: 10px;
                            border: 1px solid #6c757d;
                            border-radius: 6px;
                        }}
                    """)
                    self.save_user_colors()
                    self.tema_uygula()

            btn.clicked.connect(pick)

            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(btn)
            layout.addLayout(row)

        create_picker("numbers",      "Sayı tuşları (0-9, .)")
        create_picker("operators",    "İşlem tuşları (+ - * / = () √)")
        create_picker("danger",       "Temizle & Geri (C ⌫)")
        create_picker("screen",       "Ekran yazı rengi")
        create_picker("screen_border","Ekran çerçeve rengi")

        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 30px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec_()
        self.tema_uygula()

    def is_light_color(self, hex_color):
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness > 165
        except:
            return False

    def butonlari_olustur(self):
        for sembol, satir, sutun, r_span, c_span in self.tus_haritasi:
            if sembol == "BACK":
                btn_text = "⌫"
            elif sembol == "√":
                btn_text = "√"
            else:
                btn_text = sembol

            btn = QPushButton(btn_text)

            if c_span == 1:   w = 72
            elif c_span == 2: w = 152
            elif c_span == 3: w = 232
            else:             w = 312

            h = 60 if r_span == 1 else 128
            btn.setFixedSize(w, h)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda _, s=sembol: self.aksiyon(s))

            self.grid.addWidget(btn, satir, sutun, r_span, c_span)
            self.butonlar[sembol] = btn

    def tema_degistir(self, mod):
        self.tema_modu = mod
        self.hafizaya_kaydet()
        self.tema_uygula()

    def renk_dongusu(self):
        if self.tema_modu == 0:
            self.renk_modu_karanlik = (self.renk_modu_karanlik % 5) + 1
        else:
            self.renk_modu_aydinlik = (self.renk_modu_aydinlik % 3) + 1
        self.hafizaya_kaydet()
        self.tema_uygula()

    def tema_uygula(self):
        bg_color = "#000000" if self.tema_modu == 0 else "#f8f9fa"
        self.setStyleSheet(f"QWidget {{ background-color: {bg_color}; }}")

        self.menu.setStyleSheet(f"""
            QMenu {{ background-color: #1e1e1e; color: #e0e0e0; border: 2px solid #444444; padding: 6px; }}
            QMenu::item {{ padding: 10px 25px; }}
            QMenu::item:selected {{ background-color: #3498db; color: white; }}
        """)

        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: #3498db; border: 2px solid #444444; border-radius: 8px; font-size: 20px; }}
            QPushButton:hover {{ background-color: #3498db; color: white; }}
        """)

        self.ekran_stilini_guncelle()

        for sembol, btn in self.butonlar.items():
            btn.setStyleSheet(self.get_neon_style(sembol))

    def ekran_stilini_guncelle(self):
        current_colors = self.light_user_colors if self.tema_modu == 1 else self.dark_user_colors
        ekran_yazi = current_colors["screen"]
        ekran_cerceve = current_colors.get("screen_border", "#444444")
        bg_color = "#ffffff" if self.tema_modu == 1 else "#000000"

        self.ekran.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {ekran_yazi};
                border: 3px solid {ekran_cerceve};
                border-radius: 10px;
                padding-top: 25px;
                padding-left: 8px;
                padding-right: 12px;
                font-size: 22px;
                font-family: '{self.font_name}';
            }}
        """)

    def get_neon_style(self, sembol):
        current_colors = self.light_user_colors if self.tema_modu == 1 else self.dark_user_colors

        if sembol.isdigit() or sembol == ".":
            user_color = current_colors["numbers"]
        elif sembol in '/*+-()=√':
            user_color = current_colors["operators"]
        elif sembol in 'CBACK':
            user_color = current_colors["danger"]
        else:
            user_color = NEON_YESIL

        return f"""
            QPushButton {{
                background-color: transparent;
                color: {user_color};
                border: 1.5px solid {user_color};
                border-radius: 10px;
                font-size: 18px;
                font-family: '{self.font_name}';
            }}
            QPushButton:hover {{
                background-color: {user_color};
                color: {'#000000' if self.is_light_color(user_color) else '#ffffff'};
            }}
            QPushButton:pressed {{
                background-color: {user_color};
                color: {'#000000' if self.is_light_color(user_color) else '#ffffff'};
            }}
        """

    def show_ekran_context_menu(self, position):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 2px solid #444444;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        copy_act = menu.addAction("Kopyala")
        select_all_act = menu.addAction("Tümünü Seç")

        copy_act.triggered.connect(self.ekran.copy)
        select_all_act.triggered.connect(self.ekran.selectAll)

        menu.exec_(self.ekran.mapToGlobal(position))

    def format_gosterim(self, ifade):
        if not ifade or ifade in ["ERROR", "TANIMSIZ"]:
            return ifade or "0"

        parcalar = re.split(r'([+\-*/()√])', ifade)
        res = ""
        for p in parcalar:
            if p in "+-*/()√":
                res += p
            elif p:
                if '.' in p:
                    t, o = p.split('.', 1)
                    try: res += f"{int(t or 0):,}.{o}".replace(',', '.')
                    except: res += p
                else:
                    try: res += f"{int(p):,}".replace(',', '.')
                    except: res += p
        return res

    def format_gecmis(self, ifade):
        if not ifade or ifade in ["ERROR", "TANIMSIZ"]:
            return ifade or "0"

        parcalar = re.split(r'([+\-*/()√])', ifade)
        res = ""
        for p in parcalar:
            if p in "+-*/()√":
                res += p
            elif p.strip():
                if '.' in p:
                    parts = p.rsplit('.', 1)
                    tam = parts[0].replace('.', '')
                    ond = parts[1]
                    res += f"{tam}.{ond}"
                else:
                    res += p.replace('.', '')
            else:
                res += p
        return res

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_T:
            self.renk_dongusu()
            return

        sembol = None
        if Qt.Key_0 <= key <= Qt.Key_9:
            sembol = event.text()
        elif key == Qt.Key_Plus:    sembol = "+"
        elif key == Qt.Key_Minus:   sembol = "-"
        elif key == Qt.Key_Asterisk: sembol = "*"
        elif key == Qt.Key_Slash:   sembol = "/"
        elif key == Qt.Key_ParenLeft:  sembol = "("
        elif key == Qt.Key_ParenRight: sembol = ")"
        elif key in [Qt.Key_Comma, Qt.Key_Period]: sembol = "."
        elif key in [Qt.Key_Enter, Qt.Key_Return]: sembol = "="
        elif key == Qt.Key_Backspace: sembol = "BACK"
        elif key in [Qt.Key_Delete, Qt.Key_Escape]: sembol = "C"
        elif key in [Qt.Key_R]: sembol = str(randint(1,9))

        if sembol and sembol in self.butonlar:
            btn = self.butonlar[sembol]
            btn.setDown(True)
            btn.setStyleSheet(self.get_neon_style(sembol))
            QTimer.singleShot(120, lambda b=btn: b.setDown(False))
            self.aksiyon(sembol)

    def karekoku_hesapla(self, deger):
        try:
            if deger < 0:
                return None
            return deger.sqrt()
        except:
            return None

    def ifadeyi_isle(self, ifade):
        try:
            # ÖNEMLİ: Parantez işlemlerinden ÖNCE çarpma kurallarını uygula
            # 1. Parantez sonrası rakam: )2 → )*2
            ifade = re.sub(r'\)(\d)', r')*\1', ifade)
            
            # 2. Rakam sonrası parantez: 2( → 2*(
            ifade = re.sub(r'(\d)\(', r'\1*(', ifade)
            
            # 3. Rakam sonrası √: 2√ → 2*√
            ifade = re.sub(r'(\d)√', r'\1*√', ifade)
            
            # 4. Parantez sonrası √: )√ → )*√
            ifade = re.sub(r'\)√', r')*√', ifade)

            max_iterations = 100
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                degisiklik = False

                # √ ile basit sayı: √9 → 3
                sqrt_simple = r'√(\d+\.?\d*)'
                match = re.search(sqrt_simple, ifade)
                if match:
                    sayi = Decimal(match.group(1))
                    if sayi < 0:
                        return None
                    sonuc = sayi.sqrt()
                    ifade = ifade[:match.start()] + str(sonuc) + ifade[match.end():]
                    degisiklik = True
                    continue

                # √ ile parantez (içinde √ yok): √(4+5) → 3
                sqrt_no_inner_sqrt = r'√\(([^()√]*)\)'
                match = re.search(sqrt_no_inner_sqrt, ifade)
                if match:
                    icerik = match.group(1)
                    icerik_decimal = re.sub(r'(\d+\.?\d*|\.\d+)', r"Decimal('\1')", icerik)
                    deger = eval(icerik_decimal, {"Decimal": Decimal})
                    if deger < 0:
                        return None
                    sonuc = deger.sqrt()
                    ifade = ifade[:match.start()] + str(sonuc) + ifade[match.end():]
                    degisiklik = True
                    continue

                # Normal parantez (√ ile başlamayan): (2+2) → 4
                # ÖNEMLİ: Burada sonucu parantez içine alarak yan yana rakam oluşmasını önle
                normal_paren = r'(?<!√)\(([^()√]*)\)'
                match = re.search(normal_paren, ifade)
                if match:
                    icerik = match.group(1)
                    try:
                        icerik_decimal = re.sub(r'(\d+\.?\d*|\.\d+)', r"Decimal('\1')", icerik)
                        sonuc = eval(icerik_decimal, {"Decimal": Decimal})
                        
                        # Parantez sonucunu kontrol et - eğer öncesinde veya sonrasında rakam varsa
                        # sonucu parantez içinde tut veya çarpma ekle
                        bas = match.start()
                        son = match.end()
                        
                        # Sonucu string'e çevir
                        sonuc_str = str(sonuc)
                        
                        # Öncesinde rakam var mı kontrol et
                        oncesi_rakam = bas > 0 and ifade[bas-1].isdigit()
                        # Sonrasında rakam var mı kontrol et
                        sonrasi_rakam = son < len(ifade) and ifade[son].isdigit()
                        
                        # Eğer öncesi veya sonrası rakam ise çarpma ekle
                        if oncesi_rakam:
                            ifade = ifade[:bas] + '*' + sonuc_str + ifade[son:]
                        elif sonrasi_rakam:
                            ifade = ifade[:bas] + sonuc_str + '*' + ifade[son:]
                        else:
                            ifade = ifade[:bas] + sonuc_str + ifade[son:]
                        
                        degisiklik = True
                        continue
                    except:
                        pass

                if not degisiklik:
                    break

            return ifade
        except Exception as e:
            print(f"ifadeyi_isle hatası: {e}")
            return None

    def aksiyon(self, sembol):
        try:
            if self.ekran.toPlainText() in ["ERROR", "TANIMSIZ"]:
                self.matematik_ifadesi = ""

            if sembol == 'C':
                self.matematik_ifadesi = ""

            elif sembol == 'BACK':
                if self.matematik_ifadesi:
                    self.matematik_ifadesi = self.matematik_ifadesi[:-1]

            elif sembol == '√':
                self.matematik_ifadesi += "√"

            elif sembol == '=':
                if not self.matematik_ifadesi or self.matematik_ifadesi[-1] in "+-*/(":
                    return

                ham_islem = self.matematik_ifadesi
                islem = ham_islem

                ap, kp = islem.count('('), islem.count(')')
                if ap > kp:
                    islem += ')' * (ap - kp)

                islem_islenmis = self.ifadeyi_isle(islem)

                if islem_islenmis is None:
                    self.matematik_ifadesi = "ERROR"
                    self.ekran.setPlainText("ERROR")
                    gecmis_satir = f"HATA: {self.format_gecmis(ham_islem)}"
                    if gecmis_satir not in self.gecmis_listesi:
                        self.gecmis_listesi.append(gecmis_satir)
                        self.gecmis_kaydet_kalici(gecmis_satir)
                    if self.gecmis_penceresi and self.gecmis_penceresi.isVisible():
                        self.gecmis_penceresi.liste_guncelle()
                    return

                islem_islenmis = re.sub(r'(\d+\.?\d*|\.\d+)', r"Decimal('\1')", islem_islenmis)
                sonuc = eval(islem_islenmis, {"Decimal": Decimal}).normalize()

                sonuc_str_temp = str(sonuc)

                try:
                    if '.' in sonuc_str_temp:
                        tam, ondalik = sonuc_str_temp.split('.')
                        if len(ondalik) > 10 and ondalik.count('9') > len(ondalik) * 0.9:
                            sonuc = Decimal(int(tam) + 1)
                        elif len(ondalik) > 10 and ondalik.count('0') > len(ondalik) * 0.9:
                            sonuc = Decimal(int(tam))
                except:
                    pass

                sonuc_str = format(sonuc, 'f')

                gecmis_satir = f"{self.format_gecmis(ham_islem)} = {sonuc_str}"
                if gecmis_satir not in self.gecmis_listesi:
                    self.gecmis_listesi.append(gecmis_satir)
                    self.gecmis_kaydet_kalici(gecmis_satir)

                if self.gecmis_penceresi and self.gecmis_penceresi.isVisible():
                    self.gecmis_penceresi.liste_guncelle()

                self.matematik_ifadesi = sonuc_str

            elif sembol in "+-*/":
                if self.matematik_ifadesi and self.matematik_ifadesi[-1] in "+-*/":
                    self.matematik_ifadesi = self.matematik_ifadesi[:-1] + sembol
                else:
                    self.matematik_ifadesi += sembol

            elif sembol == ".":
                parcalar = re.split(r'[+\-*/()√]', self.matematik_ifadesi)
                if "." not in parcalar[-1]:
                    self.matematik_ifadesi += "." if self.matematik_ifadesi else "0."

            else:
                if self.matematik_ifadesi == "0":
                    self.matematik_ifadesi = sembol
                else:
                    self.matematik_ifadesi += sembol

            self.ekran_guncelle()

        except Exception as e:
            print(f"Hata yakalandı: {e}")
            self.matematik_ifadesi = "ERROR"
            self.ekran.setPlainText("ERROR")

    def ekran_guncelle(self):
        gorunum = self.format_gosterim(self.matematik_ifadesi) if self.matematik_ifadesi else "0"
        self.ekran.setPlainText(gorunum)
        self.ekran.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        if len(gorunum) >= 28:
            new_style = self.ekran.styleSheet().replace("padding-top: 25px;", "padding-top: 6px;")
        else:
            new_style = self.ekran.styleSheet().replace("padding-top: 6px;", "padding-top: 25px;")

        self.ekran.setStyleSheet(new_style)

        cursor = self.ekran.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ekran.setTextCursor(cursor)

    def gecmisi_goster(self):
        if not self.gecmis_penceresi:
            self.gecmis_penceresi = GecmisPenceresi(self)

        rect = self.geometry()
        self.gecmis_penceresi.move(rect.right(), rect.top())
        self.gecmis_penceresi.show()
        self.gecmis_penceresi.liste_guncelle()


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    window = NeonHesapMakinesi()
    window.show()
    sys.exit(app.exec_())
