#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import re
import json
from decimal import Decimal, getcontext

if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    if os.path.exists("/usr/bin/Xwayland") or os.path.exists("/usr/bin/X"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QTextEdit, QPushButton,
    QMenu, QHBoxLayout, QSpacerItem, QSizePolicy, QDialog, QLabel,
    QScrollArea, QActionGroup, QColorDialog, QFileDialog, QSlider, QInputDialog,
    QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor, QTextOption, QColor

getcontext().prec = 69

AYAR_DOSYASI = os.path.expanduser("~/.neon_calc_config")
GECMIS_DOSYASI = os.path.expanduser("~/.neon_calc_history")
FAVORI_RENKLER_DOSYASI = os.path.expanduser("~/.neon_calc_favorite_colors")

AYARLAR_NEON_MOR = "#D500F9"

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
        scale = ana_pencere.window_scale
        self.setStyleSheet(f"""
            QLabel {{
                color: {yazi_rengi};
                background-color: rgba(0, 0, 0, 0.2);
                border: {1.1 * scale}px solid {yazi_rengi}66;
                border-radius: {int(8 * scale)}px;
                padding: {int(3 * scale)}px {int(6 * scale)}px;
                margin: {int(2 * scale)}px {int(4 * scale)}px;
                font-size: {int(13 * scale)}px;
                font-weight: 500;
            }}
            QLabel:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border: {1.5 * scale}px solid {yazi_rengi};
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
        self.temizle_btn.clicked.connect(self.gecmis_sil)

        self.disa_aktar_btn = QPushButton("Kaydet")
        self.disa_aktar_btn.setStyleSheet(btn_stil)
        self.disa_aktar_btn.clicked.connect(self.gecmisi_dosya_secerek_kaydet)

        self.kapat_btn = QPushButton("Kapat")
        self.kapat_btn.clicked.connect(self.accept)

        buton_layout.addWidget(self.temizle_btn)
        buton_layout.addWidget(self.kapat_btn)
        buton_layout.addWidget(self.disa_aktar_btn)

        layout.addLayout(buton_layout)
        self.setLayout(layout)
        
        self.olcekleme_uygula()

    def olcekleme_uygula(self):
        scale = self.ana_pencere.window_scale
        
        # Pencere boyutu
        self.setFixedSize(int(360 * scale), int(480 * scale))
        
        # Başlık font boyutu
        baslik_list = self.findChildren(QLabel)
        if baslik_list and len(baslik_list) > 0:
            baslik_list[0].setStyleSheet(f"color: {self.yazi_rengi}; font-weight: bold; border: none; font-size: {int(20 * scale)}px; padding: {int(10 * scale)}px; font-family: 'Liberation Sans'; background: transparent;")
        
        # Butonların stilini güncelle
        btn_stil = f"""
            QPushButton {{
                color: {self.yazi_rengi};
                background-color: {self.buton_bg};
                border: 2px solid {self.yazi_rengi};
                border-radius: {int(10 * scale)}px;
                padding: {int(10 * scale)}px;
                font-weight: bold;
                font-size: {int(13 * scale)}px;
                font-family: 'Liberation Sans';
            }}
            QPushButton:hover {{
                background-color: {self.yazi_rengi};
                color: {self.bg_color};
            }}
        """
        
        self.temizle_btn.setStyleSheet(btn_stil)
        self.disa_aktar_btn.setStyleSheet(btn_stil)
        self.kapat_btn.setStyleSheet(btn_stil)

    def showEvent(self, event):
        super().showEvent(event)
        self.olcekleme_uygula()
        self.liste_guncelle()
        
    def liste_guncelle(self):
        while self.liste_layout.count():
            child = self.liste_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.ana_pencere.gecmis_listesi:
            yok_label = QLabel("Kayıt Yok")
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

class FavoriRenklerPenceresi(QDialog):
    def __init__(self, ana_pencere):
        super().__init__(ana_pencere)
        self.ana_pencere = ana_pencere
        self.setWindowTitle("Favori Renk Düzenleri")
        
        # Renk tanımlamaları
        self.yazi_rengi = "#00d4ff"
        self.bg_color = "#1a1a2e"
        self.buton_bg = "#00d4ff"
        self.kenarlik = "#00d4ff"
        
        # Modern gradient arka plan
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border: 3px solid #00d4ff;
                border-radius: 25px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        baslik = QLabel("FAVORİ RENK DÜZENLERİ")
        baslik.setStyleSheet("""
            color: #00d4ff; 
            font-weight: bold; 
            border: none; 
            font-size: 15px; 
            padding: 10px; 
            font-family: 'Liberation Sans'; 
            background: transparent;
        """)
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)

        # Tema seçici
        tema_layout = QHBoxLayout()
        tema_label = QLabel("Tema:")
        tema_label.setStyleSheet("color: #00d4ff; font-size: 16px; background: transparent; border: none; font-weight: bold;")
        
        self.dark_radio = QPushButton(" ☾ Karanlık")
        self.dark_radio.setCheckable(True)
        self.dark_radio.setChecked(True)
        self.dark_radio.setFixedSize(int(140 * self.ana_pencere.window_scale), int(35 * self.ana_pencere.window_scale))
        
        self.light_radio = QPushButton("☀️ Aydınlık")
        self.light_radio.setCheckable(True)
        self.light_radio.setFixedSize(int(140 * self.ana_pencere.window_scale), int(35 * self.ana_pencere.window_scale))
        
        self.update_tema_buttons()
        
        self.dark_radio.clicked.connect(lambda: self.tema_secildi(0))
        self.light_radio.clicked.connect(lambda: self.tema_secildi(1))
        
        tema_layout.addWidget(tema_label)
        tema_layout.addWidget(self.dark_radio)
        tema_layout.addWidget(self.light_radio)
        tema_layout.addStretch()
        
        layout.addLayout(tema_layout)

        # Liste
        self.liste = QListWidget()
        self.liste.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2f;
                color: #ffffff;
                border: 2px solid #00d4ff;
                border-radius: 12px;
                padding: 8px;
                font-size: 15px;
                font-family: 'Liberation Sans';
            }
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QListWidget::item:selected {{
                background-color: {self.kenarlik};
            }}
        """)
        layout.addWidget(self.liste)

        # Butonlar
        buton_layout = QHBoxLayout()

        self.kaydet_btn = QPushButton("✅ Kaydet")        
        self.kaydet_btn.clicked.connect(self.renk_duzenini_kaydet)

        self.yukle_btn = QPushButton("▼  Yükle")      
        self.yukle_btn.clicked.connect(self.renk_duzenini_yukle)

        self.sil_btn = QPushButton("×  Sil")        
        self.sil_btn.clicked.connect(self.secili_favoryi_sil)

        self.kapat_btn = QPushButton("Kapat")        
        self.kapat_btn.clicked.connect(self.accept)

        buton_layout.addWidget(self.kaydet_btn)
        buton_layout.addWidget(self.yukle_btn)
        buton_layout.addWidget(self.sil_btn)
        buton_layout.addWidget(self.kapat_btn)

        layout.addLayout(buton_layout)
        self.setLayout(layout)
        
        self.secili_tema = self.ana_pencere.tema_modu
        self.dark_radio.setChecked(self.secili_tema == 0)
        self.light_radio.setChecked(self.secili_tema == 1)
        self.update_tema_buttons()
        self.olcekleme_uygula()

    def olcekleme_uygula(self):
        scale = self.ana_pencere.window_scale
        
        # Pencere boyutu
        self.setFixedSize(int(360 * scale), int(480 * scale))
        
        # Başlık ve tema label'larını ölçekle
        baslik_labels = self.findChildren(QLabel)
        for i, lbl in enumerate(baslik_labels):
            if i == 0:  # İlk label = Başlık
                lbl.setStyleSheet(f"""
                    color: #00d4ff; 
                    font-weight: bold; 
                    border: none; 
                    font-size: {int(15 * scale)}px; 
                    padding: {int(10 * scale)}px; 
                    font-family: 'Liberation Sans'; 
                    background: transparent;
                """)
            elif i == 1:  # İkinci label = Tema:
                lbl.setStyleSheet(f"color: #00d4ff; font-size: {int(16 * scale)}px; background: transparent; border: none; font-weight: bold;")
        
        # Buton boyutlarını güncelle (GENİŞLİK + YÜKSEKLİK)
        self.dark_radio.setFixedSize(int(140 * scale), int(35 * scale))
        self.light_radio.setFixedSize(int(140 * scale), int(35 * scale))
        
        # Tema butonlarını güncelle
        self.update_tema_buttons()
        
        # Liste stilini güncelle (font boyutu)
        self.liste.setStyleSheet(f"""
            QListWidget {{
                background-color: #1e1e2f;
                color: #ffffff;
                border: 2px solid #00d4ff;
                border-radius: {int(12 * scale)}px;
                padding: {int(8 * scale)}px;
                font-size: {int(15 * scale)}px;
                font-family: 'Liberation Sans';
            }}
            QListWidget::item {{
                padding: {int(8 * scale)}px;
                border-radius: {int(4 * scale)}px;
                margin: {int(2 * scale)}px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QListWidget::item:selected {{
                background-color: {self.kenarlik};
            }}
        """)
        
        # Alt butonları ölçekle
        btn_stil = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #0096c7);
                color: #000000;
                border: none;
                border-radius: {int(10 * scale)}px;
                padding: {int(12 * scale)}px;
                font-weight: bold;
                font-size: {int(12 * scale)}px;
                font-family: 'Liberation Sans';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00b4d8, stop:1 #0077b6);
            }}
            QPushButton:pressed {{
                background: #005f73;
            }}
        """
        
        self.kaydet_btn.setStyleSheet(btn_stil)
        self.yukle_btn.setStyleSheet(btn_stil)
        self.sil_btn.setStyleSheet(btn_stil)
        self.kapat_btn.setStyleSheet(btn_stil)

    def tema_secildi(self, tema):
        # Eğer zaten kilitli durumdaysa (sadece bir buton aktifse) değişiklik yapmayı engelle
        if not self.dark_radio.isEnabled() or not self.light_radio.isEnabled():
            # Mevcut seçili duruma geri dön (kilit bozulmasın)
            self.dark_radio.setChecked(self.secili_tema == 0)
            self.light_radio.setChecked(self.secili_tema == 1)
            return

        # Normal davranış: tema değiştir
        self.secili_tema = tema
        self.dark_radio.setChecked(tema == 0)
        self.light_radio.setChecked(tema == 1)
        self.update_tema_buttons()
        self.liste_guncelle()

    def update_tema_buttons(self):
        scale = self.ana_pencere.window_scale
        if self.dark_radio.isChecked():
            # Karanlık aktif
            self.dark_radio.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2F2F4F, stop:1 #27ae60);
                    color: white;
                    border: {int(2 * scale)}px solid #00d4ff;
                    border-radius: {int(8 * scale)}px;
                    font-weight: bold;
                    font-size: {int(14 * scale)}px;
                    padding: {int(8 * scale)}px;
                }}
            """)
            # Aydınlık pasif
            self.light_radio.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #00d4ff;
                    border: {int(2 * scale)}px solid #00d4ff;
                    border-radius: {int(8 * scale)}px;
                    font-size: {int(14 * scale)}px;
                    padding: {int(8 * scale)}px;
                    opacity: 0.65;
                }}
                QPushButton:hover {{
                    background: rgba(0, 212, 255, 0.15);
                    opacity: 0.85;
                }}
            """)
        else:
            # Aydınlık aktif
            self.light_radio.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2F2F4F, stop:1 #27ae60);
                    color: white;
                    border: {int(2 * scale)}px solid #00d4ff;
                    border-radius: {int(8 * scale)}px;
                    font-weight: bold;
                    font-size: {int(14 * scale)}px;
                    padding: {int(8 * scale)}px;
                }}
            """)
            # Karanlık pasif
            self.dark_radio.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #00d4ff;
                    border: {int(2 * scale)}px solid #00d4ff;
                    border-radius: {int(8 * scale)}px;
                    font-size: {int(14 * scale)}px;
                    padding: {int(8 * scale)}px;
                    opacity: 0.65;
                }}
                QPushButton:hover {{
                    background: rgba(0, 212, 255, 0.15);
                    opacity: 0.85;
                }}
            """)

    def showEvent(self, event):
        super().showEvent(event)
        self.olcekleme_uygula()
        self.liste_guncelle()

    def liste_guncelle(self):
        self.liste.clear()
        tema_key = "dark" if self.secili_tema == 0 else "light"
        
        if tema_key not in self.ana_pencere.favori_renkler or not self.ana_pencere.favori_renkler[tema_key]:
            item = QListWidgetItem(f"Kayıtlı {'karanlık' if self.secili_tema == 0 else 'aydınlık'} tema favorisi yok")
            item.setFlags(Qt.NoItemFlags)
            self.liste.addItem(item)
        else:
            for isim in self.ana_pencere.favori_renkler[tema_key].keys():
                self.liste.addItem(isim)


    def renk_duzenini_kaydet(self):
        scale = self.ana_pencere.window_scale
        
        # Input dialog için stil ayarla
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Favori İsmi")
        input_dialog.setLabelText("Bu renk düzenine bir isim verin:")
        
        # Tema'ya göre stil
        if self.secili_tema == 0:  # Karanlık tema
            input_dialog.setStyleSheet(f"""
                QInputDialog {{
                    background-color: #1e1e2f;
                }}
                QLabel {{
                    color: #00d4ff;
                    font-size: {int(14 * scale)}px;
                    font-weight: bold;
                    background: transparent;
                }}
                QLineEdit {{
                    background-color: #2d2d3d;
                    color: white;
                    border: {int(2 * scale)}px solid #00d4ff;
                    border-radius: {int(6 * scale)}px;
                    padding: {int(8 * scale)}px;
                    font-size: {int(14 * scale)}px;
                }}
                QPushButton {{
                    background-color: #00d4ff;
                    color: white;
                    border: none;
                    border-radius: {int(6 * scale)}px;
                    padding: {int(8 * scale)}px {int(20 * scale)}px;
                    font-weight: bold;
                    font-size: {int(13 * scale)}px;
                }}
                QPushButton:hover {{
                    background-color: #00b4d8;
                }}
            """)
        else:  # Aydınlık tema
            input_dialog.setStyleSheet(f"""
                QInputDialog {{
                    background-color: #f8f9fa;
                }}
                QLabel {{
                    color: #2F2F4F;
                    font-size: {int(14 * scale)}px;
                    font-weight: bold;
                    background: transparent;
                }}
                QLineEdit {{
                    background-color: white;
                    color: #000000;
                    border: {int(2 * scale)}px solid #00d4ff;
                    border-radius: {int(6 * scale)}px;
                    padding: {int(8 * scale)}px;
                    font-size: {int(14 * scale)}px;
                }}
                QPushButton {{
                    background-color: #00d4ff;
                    color: white;
                    border: none;
                    border-radius: {int(6 * scale)}px;
                    padding: {int(8 * scale)}px {int(20 * scale)}px;
                    font-weight: bold;
                    font-size: {int(13 * scale)}px;
                }}
                QPushButton:hover {{
                    background-color: #00b4d8;
                }}
            """)
        
        ok = input_dialog.exec_()
        isim = input_dialog.textValue()
        
        if ok and isim.strip():
            isim = isim.strip()
            tema_key = "dark" if self.secili_tema == 0 else "light"
            
            if tema_key not in self.ana_pencere.favori_renkler:
                self.ana_pencere.favori_renkler[tema_key] = {}
            
            if self.secili_tema == 0:
                colors_to_save = self.ana_pencere.dark_user_colors.copy()
            else:
                colors_to_save = self.ana_pencere.light_user_colors.copy()
            
            self.ana_pencere.favori_renkler[tema_key][isim] = colors_to_save
            self.ana_pencere.save_favorite_colors()
            self.liste_guncelle()
            
            msg = QMessageBox(self)
            msg.setWindowTitle("Başarılı")
            msg.setText(f"'{isim}' renk düzeni kaydedildi!")
            msg.setIcon(QMessageBox.Information)
            msg.setTextInteractionFlags(Qt.NoTextInteraction)
            
            if self.secili_tema == 0:
                msg.setStyleSheet(f"""
                    QMessageBox {{ background-color: #1e1e2f; }}
                    QLabel {{ color: #00d4ff; font-size: {int(14 * scale)}px; background: transparent; }}
                    QPushButton {{ background-color: #00d4ff; color: white; border: none; 
                                  border-radius: {int(6 * scale)}px; padding: {int(8 * scale)}px {int(20 * scale)}px; 
                                  font-weight: bold; min-width: {int(80 * scale)}px; font-size: {int(13 * scale)}px; }}
                    QPushButton:hover {{ background-color: #00b4d8; }}
                """)
            else:
                msg.setStyleSheet(f"""
                    QMessageBox {{ background-color: #f8f9fa; }}
                    QLabel {{ color: #2F2F4F; font-size: {int(14 * scale)}px; background: transparent; }}
                    QPushButton {{ background-color: #00d4ff; color: white; border: none; 
                                  border-radius: {int(6 * scale)}px; padding: {int(8 * scale)}px {int(20 * scale)}px; 
                                  font-weight: bold; min-width: {int(80 * scale)}px; font-size: {int(13 * scale)}px; }}
                    QPushButton:hover {{ background-color: #00b4d8; }}
                """)
            msg.exec_()

    def renk_duzenini_yukle(self):
        scale = self.ana_pencere.window_scale
        
        secili = self.liste.currentItem()
        if not secili or secili.flags() == Qt.NoItemFlags:
            msg = QMessageBox(self)
            msg.setWindowTitle("Uyarı")
            msg.setText("Lütfen bir favori seçin!")
            msg.setIcon(QMessageBox.Warning)
            msg.setTextInteractionFlags(Qt.NoTextInteraction)
            
            msg.setStyleSheet(f"""
                QMessageBox {{ background-color: #2a2a3a; }}
                QLabel {{ color: #00d4ff; font-size: {int(14 * scale)}px; background: transparent; }}
                QPushButton {{
                    background-color: #00d4ff;
                    color: #000000;
                    border: none;
                    border-radius: {int(6 * scale)}px;
                    padding: {int(8 * scale)}px {int(20 * scale)}px;
                    font-weight: bold;
                    min-width: {int(80 * scale)}px;
                    font-size: {int(13 * scale)}px;
                }}
                QPushButton:hover {{
                    background-color: #00b4d8;
                }}
            """)
            msg.exec_()
            return
        
        isim = secili.text()
        tema_key = "dark" if self.secili_tema == 0 else "light"
        
        if tema_key in self.ana_pencere.favori_renkler and isim in self.ana_pencere.favori_renkler[tema_key]:
            yuklenecek_renkler = self.ana_pencere.favori_renkler[tema_key][isim]
            
            # Renkleri ana pencereye yükle
            if tema_key == "dark":
                self.ana_pencere.dark_user_colors = yuklenecek_renkler.copy()
            else:
                self.ana_pencere.light_user_colors = yuklenecek_renkler.copy()
            
            # Ayarları kaydet
            self.ana_pencere.hafizaya_kaydet()
            
            # Tüm arayüzü yenile
            self.ana_pencere.tema_uygula()
            self.ana_pencere.ekran_guncelle()
            
            # Başarılı mesajı
            msg = QMessageBox(self)
            msg.setWindowTitle("Başarılı")
            msg.setText(f"'{isim}' renk düzeni yüklendi!")
            msg.setIcon(QMessageBox.Information)
            msg.setTextInteractionFlags(Qt.NoTextInteraction)
            
            msg.setStyleSheet(f"""
                QMessageBox {{ background-color: #2a2a3a; }}
                QLabel {{ color: #00d4ff; font-size: {int(14 * scale)}px; background: transparent; }}
                QPushButton {{
                    background-color: #00d4ff;
                    color: #000000;
                    border: none;
                    border-radius: {int(6 * scale)}px;
                    padding: {int(8 * scale)}px {int(20 * scale)}px;
                    font-weight: bold;
                    min-width: {int(80 * scale)}px;
                    font-size: {int(13 * scale)}px;
                }}
                QPushButton:hover {{
                    background-color: #00b4d8;
                }}
            """)
            msg.exec_()
            
            # Liste görünümünü güncelle
            self.liste_guncelle()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Hata")
            msg.setText("Seçilen favori bulunamadı!")
            msg.setIcon(QMessageBox.Critical)
            msg.setTextInteractionFlags(Qt.NoTextInteraction)
            msg.setStyleSheet(f"""
                QMessageBox {{ background-color: #2a2a3a; }}
                QLabel {{ color: #ff4d4d; font-size: {int(14 * scale)}px; background: transparent; }}
                QPushButton {{
                    background-color: #ff4d4d;
                    color: #ffffff;
                    border: none;
                    border-radius: {int(6 * scale)}px;
                    padding: {int(8 * scale)}px {int(20 * scale)}px;
                    font-weight: bold;
                }}
            """)
            msg.exec_()
            return

    def secili_favoryi_sil(self):
        scale = self.ana_pencere.window_scale
        
        secili = self.liste.currentItem()
        if not secili or secili.flags() == Qt.NoItemFlags:
            msg = QMessageBox(self)
            msg.setWindowTitle("Uyarı")
            msg.setText("Lütfen bir favori seçin!")
            msg.setIcon(QMessageBox.Warning)
            msg.setTextInteractionFlags(Qt.NoTextInteraction)
            
            # Butonu programatik yakala ve stil ver (siyah yazı sorunu çözülür)
            msg.setStandardButtons(QMessageBox.Ok)
            ok_button = msg.button(QMessageBox.Ok)
            if ok_button:
                ok_button.setText("Tamam")  # Türkçe olsun diye (isteğe bağlı)
                ok_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #00d4ff;
                        color: #000000;
                        border: none;
                        border-radius: {int(6 * scale)}px;
                        padding: {int(8 * scale)}px {int(20 * scale)}px;
                        font-weight: bold;
                        min-width: {int(80 * scale)}px;
                        font-size: {int(13 * scale)}px;
                    }}
                    QPushButton:hover {{
                        background-color: #00b4d8;
                    }}
                """)
            
            # Pencere arka planını da biraz aç (isteğe bağlı, ama daha net olur)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: #2a2a3a;
                }}
                QLabel {{
                    color: #00d4ff;
                    font-size: {int(14 * scale)}px;
                    background: transparent;
                }}
            """)
            
            msg.exec_()
            return
        
        isim = secili.text()
        tema_key = "dark" if self.secili_tema == 0 else "light"
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Onay")
        msg.setText(f"'{isim}' favorisini silmek istediğinize emin misiniz?")
        msg.setIcon(QMessageBox.Question)
        msg.setTextInteractionFlags(Qt.NoTextInteraction)
        
        # Önce butonları ekle (setStandardButtons önce)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)  # Güvenlik için No varsayılan
        
        # Sonra butonları yakala ve stil ver (timing sorunu önlenir)
        yes_button = msg.button(QMessageBox.Yes)
        no_button = msg.button(QMessageBox.No)
        
        button_style = f"""
            QPushButton {{
                background-color: #00d4ff;
                color: #000000;
                border: none;
                border-radius: {int(6 * scale)}px;
                padding: {int(8 * scale)}px {int(20 * scale)}px;
                font-weight: bold;
                min-width: {int(80 * scale)}px;
                font-size: {int(13 * scale)}px;
            }}
            QPushButton:hover {{
                background-color: #00b4d8;
            }}
        """
        
        if yes_button:
            yes_button.setText("Evet")   # Türkçe olsun diye (isteğe göre değiştir)
            yes_button.setStyleSheet(button_style)
        if no_button:
            no_button.setText("Hayır")
            no_button.setStyleSheet(button_style)
        
        # Pencere arka planını da zorla (önceki karanlık kalmasın)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: #2a2a3a;  /* Hafif açık koyu, okunaklı */
            }}
            QLabel {{
                color: #00d4ff;
                font-size: {int(14 * scale)}px;
                background: transparent;
            }}
        """)
        
        reply = msg.exec_()
        
        # Reply kontrolü (PyQt5'te int döner, enum.value ile karşılaştır)
        if reply == QMessageBox.Yes:
            if tema_key in self.ana_pencere.favori_renkler and isim in self.ana_pencere.favori_renkler[tema_key]:
                del self.ana_pencere.favori_renkler[tema_key][isim]
                self.ana_pencere.save_favorite_colors()
                self.liste_guncelle()
                
                success_msg = QMessageBox(self)
                success_msg.setWindowTitle("Başarılı")
                success_msg.setText(f"'{isim}' favorisi silindi!")
                success_msg.setIcon(QMessageBox.Information)
                success_msg.setTextInteractionFlags(Qt.NoTextInteraction)
                
                success_msg.setStandardButtons(QMessageBox.Ok)
                ok_button = success_msg.button(QMessageBox.Ok)
                if ok_button:
                    ok_button.setStyleSheet(button_style)
                
                success_msg.setStyleSheet(msg.styleSheet())  # Aynı arka plan
                success_msg.exec_()
        # Hayır basılırsa veya Esc vs. hiçbir şey yapma

class NeonHesapMakinesi(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neon Hesap Makinesi")
        
        # Temel boyutlar
        self.base_width = 340
        self.base_height = 575
        
        ayarlar = self.hafizadan_yukle()
        self.tema_modu = ayarlar[0]
        self.hassasiyet = ayarlar[1]
        self.window_scale = ayarlar[2]
        self.border_radius_value = ayarlar[3]

        self.dark_user_colors = DARK_USER_COLORS_DEFAULT.copy()
        self.light_user_colors = LIGHT_USER_COLORS_DEFAULT.copy()

        self.load_user_colors()
        self.favori_renkler = self.load_favorite_colors()
        self.setWindowIcon(QtGui.QIcon("/usr/share/pixmaps/neon-calc.png"))

        self.matematik_ifadesi = ""
        self.butonlar = {}
        self.gecmis_penceresi = None
        self.favori_renkler_penceresi = None

        self.gecmis_listesi = self.gecmis_yukle_kalici()

        getcontext().prec = self.hassasiyet

        self.init_ui()
        self.apply_window_scale()
        self.tema_uygula()

        self.ekran.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ekran.customContextMenuRequested.connect(self.show_ekran_context_menu)

    def apply_window_scale(self):
        w = int(self.base_width * self.window_scale)
        h = int(self.base_height * self.window_scale)
        self.setFixedSize(w, h)

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
            
    def load_favorite_colors(self):
        """Favori renk düzenlerini dosyadan yükle"""
        try:
            if os.path.exists(FAVORI_RENKLER_DOSYASI):
                with open(FAVORI_RENKLER_DOSYASI, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Favori renkler yükleme hatası: {e}")
        return {}
    
    def save_favorite_colors(self):
        """Favori renk düzenlerini dosyaya kaydet"""
        try:
            with open(FAVORI_RENKLER_DOSYASI, "w", encoding="utf-8") as f:
                json.dump(self.favori_renkler, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Favori renkler kaydetme hatası: {e}")

    def save_user_colors(self):
        self.hafizaya_kaydet()

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

                    tema = int(data.get("tema_modu", 0))

                    hass_str = data.get("hassasiyet", "69")
                    try:
                        hass = int(hass_str)
                        if hass not in [15, 22, 33, 69]:
                            hass = 69
                    except:
                        hass = 69

                    scale_str = data.get("window_scale", "1.0")
                    try:
                        scale = float(scale_str)
                        if scale < 0.6 or scale > 2.0:
                            scale = 1.0
                    except:
                        scale = 1.0

                    border_str = data.get("border_radius", "27")
                    try:
                        border = int(border_str)
                        if border < 1 or border > 36:
                            border = 27
                    except:
                        border = 27

                    return (tema, hass, scale, border)
        except Exception as e:
            print(f"Ayar yükleme hatası: {e}")

        return (0, 69, 1.0, 27)

    def hafizaya_kaydet(self):
        try:
            with open(AYAR_DOSYASI, "w", encoding="utf-8") as f:
                f.write(f"hassasiyet={self.hassasiyet}\n")
                f.write(f"tema_modu={self.tema_modu}\n")
                f.write(f"window_scale={self.window_scale}\n")
                f.write(f"border_radius={self.border_radius_value}\n")
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
        layout.setContentsMargins(
            int(12 * self.window_scale),
            int(10 * self.window_scale),
            int(12 * self.window_scale),
            int(15 * self.window_scale)
        )
        layout.setSpacing(int(8 * self.window_scale))

        ust_bar = QHBoxLayout()
        ust_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(
            int(40 * self.window_scale),
            int(30 * self.window_scale)
        )
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFocusPolicy(Qt.NoFocus)

        self.menu = QMenu(self)
        self.gecmis_act = self.menu.addAction("İşlem Geçmişi")
        self.favori_renkler_act = self.menu.addAction("Favori Renkler")
        self.menu.addSeparator()
        self.ayarlar_act = self.menu.addAction("Ayarlar...")
        self.hakkinda_act = self.menu.addAction("Hakkında")
        self.hakkinda_act.triggered.connect(self.show_about_dialog)
        
        self.settings_btn.setMenu(self.menu)

        self.gecmis_act.triggered.connect(self.gecmisi_goster)
        self.favori_renkler_act.triggered.connect(self.favori_renkleri_goster)
        self.ayarlar_act.triggered.connect(self.show_modern_settings_dialog)

        ust_bar.addWidget(self.settings_btn)
        layout.addLayout(ust_bar)

        self.ekran = QTextEdit()
        self.ekran.setReadOnly(True)
        self.ekran.setFocusPolicy(Qt.NoFocus)
        self.ekran.setWordWrapMode(QTextOption.WrapAnywhere)
        self.ekran.setFixedHeight(int(100 * self.window_scale))
        self.ekran.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ekran.setText("0")
        self.ekran.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.ekran)

        self.grid = QGridLayout()
        spacing_map = {
               0.6: 4, 0.7: 5, 0.8: 5, 0.9: 6, 1.0: 6,
               1.1: 7, 1.2: 7, 1.3: 8, 1.4: 8, 1.5: 8,
               1.6: 9, 1.7: 9, 1.8: 10, 1.9: 10, 2.0: 11
        }
        scale_rounded = round(self.window_scale, 1)
        spacing = spacing_map.get(scale_rounded, 8)
        self.grid.setSpacing(int(spacing * self.window_scale))

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

    def butonlari_sil(self):
        """Tüm butonları sil"""
        for sembol in list(self.butonlar.keys()):
            btn = self.butonlar[sembol]
            self.grid.removeWidget(btn)
            btn.deleteLater()
        self.butonlar.clear()
        
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
        dialog.setMinimumWidth(int(500 * self.window_scale))


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
        layout.setContentsMargins(
            int(20 * self.window_scale),
            int(20 * self.window_scale),
            int(20 * self.window_scale),
            int(20 * self.window_scale)
        )
        layout.setSpacing(int(20 * self.window_scale))

        title = QLabel("Renkleri Özelleştir")
        title.setStyleSheet(f"font-size: {int(18 * self.window_scale)}px; font-weight: bold; color: #3498db;")
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
                    min-width: {int(120 * self.window_scale)}px;
                    padding: {int(10 * self.window_scale)}px;
                    border: {int(1 * self.window_scale)}px solid #6c757d;
                    border-radius: {int(6 * self.window_scale)}px;
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

        create_picker("numbers", "Sayı tuşları (0-9, .)")
        create_picker("operators", "İşlem tuşları (+ - * / = () √)")
        create_picker("danger", "Temizle & Geri (C ⌫)")
        create_picker("screen", "Ekran yazı rengi")
        create_picker("screen_border", "Ekran çerçeve rengi")

        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                padding: {int(10 * self.window_scale)}px {int(30 * self.window_scale)}px;
                border: none;
                border-radius: {int(6 * self.window_scale)}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec_()
        self.tema_uygula()
        
    def show_custom_colors_dialog_temp(self, tema_modu, dark_colors, light_colors):
        """Geçici renk düzenleme - sadece kaydet butonuna basınca kalıcı olur"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Renk Özelleştir ({'Aydınlık' if tema_modu == 1 else 'Karanlık'} Tema)")
        dialog.setMinimumWidth(int(500 * self.window_scale))

        
        if tema_modu == 1:
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
        layout.setContentsMargins(
            int(20 * self.window_scale),
            int(20 * self.window_scale),
            int(20 * self.window_scale),
            int(20 * self.window_scale)
        )
        layout.setSpacing(int(20 * self.window_scale))
        
        title = QLabel("Renkleri Özelleştir")
        title.setStyleSheet(f"font-size: {int(18 * self.window_scale)}px; font-weight: bold; color: #3498db;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        current_colors = light_colors if tema_modu == 1 else dark_colors
        
        def create_picker(key, title_text):
            row = QHBoxLayout()
            row.setSpacing(15)
            
            lbl = QLabel(title_text)
            lbl.setStyleSheet(f"""
                color: {'#212529' if tema_modu == 1 else '#e0e0e0'};
                font-size: {int(14 * self.window_scale)}px;
                background: transparent;
                padding: {int(6 * self.window_scale)}px 0;
            """)
            lbl.setMinimumWidth(int(320 * self.window_scale))
            
            current = current_colors.get(key, "#ffffff")
            btn = QPushButton("Seç")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {current};
                    color: {'#000000' if self.is_light_color(current) else '#ffffff'};
                    min-width: {int(120 * self.window_scale)}px;
                    padding: {int(10 * self.window_scale)}px;
                    border: {int(1 * self.window_scale)}px solid #6c757d;
                    border-radius: {int(6 * self.window_scale)}px;
                }}
            """)
            
            def pick():
                nonlocal current
                col = QColorDialog.getColor(QColor(current), dialog)
                if col.isValid():
                    hex_val = col.name()
                    current = hex_val
                    current_colors[key] = hex_val
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {hex_val};
                            color: {'#000000' if self.is_light_color(hex_val) else '#ffffff'};
                            min-width: {int(120 * self.window_scale)}px;
                            padding: {int(10 * self.window_scale)}px;
                            border: {int(1 * self.window_scale)}px solid #6c757d;
                            border-radius: {int(6 * self.window_scale)}px;
                        }}
                    """)
            
            btn.clicked.connect(pick)
            
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(btn)
            layout.addLayout(row)
        
        create_picker("numbers", "Sayı tuşları (0-9, .)")
        create_picker("operators", "İşlem tuşları (+ - * / = () √)")
        create_picker("danger", "Temizle & Geri (C ⌫)")
        create_picker("screen", "Ekran yazı rengi")
        create_picker("screen_border", "Ekran çerçeve rengi")
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                padding: {int(10 * self.window_scale)}px {int(30 * self.window_scale)}px;
                border: none;
                border-radius: {int(6 * self.window_scale)}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
    def show_modern_settings_dialog(self):
        """Modern ve şık ayarlar penceresi"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ayarlar")
        dialog.setFixedSize(int(430 * self.window_scale), int(575 * self.window_scale))
        
        # Geçici değişkenler - kullanıcı değiştirdikçe bunlar güncellenir
        temp_tema = self.tema_modu
        temp_hassasiyet = self.hassasiyet
        temp_dark_colors = self.dark_user_colors.copy()
        temp_light_colors = self.light_user_colors.copy()
        
        # Tema renklerini belirle
        if self.tema_modu == 1:
            bg_color = "#f8f9fa"
            text_color = "#212529"
            card_bg = "#ffffff"
            border_color = "#dee2e6"
        else:
            bg_color = "#1a1a1a"
            text_color = "#e0e0e0"
            card_bg = "#2d2d2d"
            border_color = "#404040"
        
        dialog.setStyleSheet(f"""
            QDialog {{ 
                background-color: {bg_color}; 
                color: {text_color}; 
            }}
            QLabel {{ 
                color: {text_color}; 
                background: transparent; 
            }}
            QPushButton {{ 
                background-color: #3498db; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 8px; 
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ 
                background-color: #2980b9; 
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Başlık bölümü
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2F2F4F);
                border-radius: 0px;
            }}
        """)
        header.setFixedHeight(int(100 * self.window_scale))
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        # Sol taraf - Başlık ve alt başlık
        title_container = QVBoxLayout()
        title_container.setSpacing(3)
        
        title = QLabel("⚙ Ayarlar")
        title.setStyleSheet(f"font-size: {int(20 * self.window_scale)}px; font-weight: bold; color: white; background: transparent; line-height: 1.5;")
        title_container.addWidget(title)
        
        subtitle = QLabel("Hesap makinesini özelleştirin")
        subtitle.setStyleSheet(f"font-size: {int(14 * self.window_scale)}px; color: rgba(255,255,255,0.9); background: transparent; line-height: 1.5;")
        title_container.addWidget(subtitle)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        # Sağ taraf - Kaydet butonu
        apply_btn = QPushButton("✅ Kaydet")
        apply_btn.setFixedSize(int(120 * self.window_scale), int(45 * self.window_scale))
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2F2F4F, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: {int(8 * self.window_scale)}px;
                font-size: {int(14 * self.window_scale)}px;
                font-weight: bold;
                padding: 0 {int(20 * self.window_scale)}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #020ef2, stop:1 #27ae60);
            }}
        """)
        header_layout.addWidget(apply_btn)
                # Buton fonksiyonu daha sonra bağlanacak
        
        main_layout.addWidget(header)

        # İçerik alanı
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {bg_color};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {bg_color};
                width: {int(10 * self.window_scale)}px;
                border-radius: {int(5 * self.window_scale)}px;
            }}
            QScrollBar::handle:vertical {{
                background: #3498db;
                border-radius: {int(5 * self.window_scale)}px;
                min-height: {int(20 * self.window_scale)}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #2980b9;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background: {bg_color};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(
            int(8 * self.window_scale),
            int(10 * self.window_scale),
            int(25 * self.window_scale),
            int(10 * self.window_scale)
        )
        content_layout.setSpacing(int(20 * self.window_scale))

        # 1. SIRA - Ekran Ölçeği kartı
        scale_card = self.create_settings_card(
            "⛶   Pencere Ölçeği", 
            f"Mevcut: %{int(self.window_scale * 100)}",
            card_bg, border_color, text_color
        )
        scale_card_layout = scale_card.layout()
        
        scale_slider = QSlider(Qt.Horizontal)
        scale_slider.setMinimum(60)
        scale_slider.setMaximum(200)
        scale_slider.setFocusPolicy(Qt.StrongFocus)
        scale_slider.wheelEvent = lambda event: None
        scale_slider.setValue(int(self.window_scale * 100))
        scale_slider.setFixedHeight(int(40 * self.window_scale))
        scale_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: {int(8 * self.window_scale)}px;
                background: {border_color};
                border-radius: {int(4 * self.window_scale)}px;
            }}
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border: none;
                width: 20px;
                margin: -6px 0;
                border-radius: 50%;
            }}
            QSlider::handle:horizontal:hover {{
                background: #2980b9;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: {int(4 * self.window_scale)}px;
            }}
            QSlider::add-page:horizontal {{
                background: {border_color};
                border-radius: {int(4 * self.window_scale)}px;
            }}
        """)
        
        scale_value_label = QLabel(f"%{int(self.window_scale * 100)}")
        scale_value_label.setAlignment(Qt.AlignCenter)
        scale_value_label.setStyleSheet(f"""
            font-size: {int(16 * self.window_scale)}px; 
            font-weight: bold; 
            color: #3498db; 
            background: {border_color}; 
            padding: {int(8 * self.window_scale)}px; 
            border-radius: {int(6 * self.window_scale)}px;
            min-width: {int(60 * self.window_scale)}px;
        """)
        
        def update_scale_display(value):
            scale_value_label.setText(f"%{value}")
            for i in range(scale_card.layout().count()):
                widget = scale_card.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and "Mevcut:" in widget.text():
                    widget.setText(f"Mevcut: %{value}")
        
        scale_slider.valueChanged.connect(update_scale_display)
        
        scale_control = QHBoxLayout()
        scale_control.addWidget(scale_slider)
        scale_control.addWidget(scale_value_label)
        scale_card_layout.addLayout(scale_control)
                
        content_layout.addWidget(scale_card)

        # 2. SIRA - Tuş Biçimi kartı
        border_card = self.create_settings_card(
            "⌨️   Tuş Biçimi", 
            f"Yuvarlaklık: {self.border_radius_value}",
            card_bg, border_color, text_color
        )
        border_card_layout = border_card.layout()
        
        border_slider = QSlider(Qt.Horizontal)
        border_slider.setMinimum(1)
        border_slider.setMaximum(36)
        border_slider.setFocusPolicy(Qt.StrongFocus)
        border_slider.wheelEvent = lambda event: None
        border_slider.setValue(self.border_radius_value)
        border_slider.setFixedHeight(int(40 * self.window_scale))
        border_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: {int(8 * self.window_scale)}px;
                background: {border_color};
                border-radius: {int(4 * self.window_scale)}px;
            }}
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e74c3c, stop:1 #c0392b);
                border: none;
                width: 20px;
                margin: -6px 0;
                border-radius: 50%;
            }}
            QSlider::handle:horizontal:hover {{
                background: #c0392b;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e74c3c, stop:1 #c0392b);
                border-radius: {int(4 * self.window_scale)}px;
            }}
            QSlider::add-page:horizontal {{
                background: {border_color};
                border-radius: {int(4 * self.window_scale)}px;
            }}
        """)
        
        border_value_label = QLabel(str(self.border_radius_value))
        border_value_label.setAlignment(Qt.AlignCenter)
        border_value_label.setStyleSheet(f"""
            font-size: {int(16 * self.window_scale)}px;
            font-weight: bold;
            color: #e74c3c; 
            background: {border_color}; 
            padding: {int(8 * self.window_scale)}px;
            border-radius: {int(6 * self.window_scale)}px;
            min-width: {int(60 * self.window_scale)}px;
        """)
        
        def update_border_display(value):
            border_value_label.setText(str(value))
            for i in range(border_card.layout().count()):
                widget = border_card.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and "Yuvarlaklık:" in widget.text():
                    widget.setText(f"Yuvarlaklık: {value}")
        
        border_slider.valueChanged.connect(update_border_display)
        
        border_control = QHBoxLayout()
        border_control.addWidget(border_slider)
        border_control.addWidget(border_value_label)
        border_card_layout.addLayout(border_control)
               
        content_layout.addWidget(border_card)

        # 3. SIRA - Tema kartı
        tema_card = self.create_settings_card(
            "🎛️   Tema", 
            "Arayüz görünümünü seçin",
            card_bg, border_color, text_color
        )
        tema_card_layout = tema_card.layout()
        
        tema_buttons = QHBoxLayout()
        tema_buttons.setSpacing(10)
        
        dark_btn = QPushButton(" ☾  Karanlık")
        dark_btn.setFixedHeight(int(45 * self.window_scale))
        dark_btn.setCheckable(True)
        dark_btn.setChecked(self.tema_modu == 0)
        
        light_btn = QPushButton("☀   Aydınlık")
        light_btn.setFixedHeight(int(45 * self.window_scale))
        light_btn.setCheckable(True)
        light_btn.setChecked(self.tema_modu == 1)
        
        def tema_sec(mod):
            nonlocal temp_tema
            temp_tema = mod
            
            if temp_tema == 0:
                dark_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2F2F4F, stop:1 #27ae60);
                        color: white;
                        border: {int(2 * self.window_scale)}px solid #020ef2;
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(14 * self.window_scale)}px;
                        font-weight: bold;
                        padding: {int(8 * self.window_scale)}px;
                    }}
                """)
                light_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: #7f8c8d;
                        border: {int(2 * self.window_scale)}px solid #bdc3c7;
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(14 * self.window_scale)}px;
                        padding: {int(8 * self.window_scale)}px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #020ef2, stop:1 #27ae60);
                        color: white;
                    }}
                """)
            else:
                light_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2F2F4F, stop:1 #27ae60);
                        color: white;
                        border: {int(2 * self.window_scale)}px solid #020ef2;
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(14 * self.window_scale)}px;
                        font-weight: bold;
                        padding: {int(8 * self.window_scale)}px;
                    }}
                """)
                dark_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: #7f8c8d;
                        border: {int(2 * self.window_scale)}px solid #bdc3c7;
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(14 * self.window_scale)}px;
                        padding: {int(8 * self.window_scale)}px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #020ef2, stop:1 #27ae60);
                        color: white;
                    }}
                """)
        
        dark_btn.clicked.connect(lambda: tema_sec(0))
        light_btn.clicked.connect(lambda: tema_sec(1))
        
        tema_sec(temp_tema) 
        
        tema_buttons.addWidget(dark_btn)
        tema_buttons.addWidget(light_btn)
        tema_card_layout.addLayout(tema_buttons)
        
        content_layout.addWidget(tema_card)

        # 4. SIRA - Renkler kartı
        colors_card = self.create_settings_card(
            "🖼️   Renk Özelleştirme", 
            "Tuş ve ekran renklerini düzenleyin",
            card_bg, border_color, text_color
        )
        colors_card_layout = colors_card.layout()
        
        colors_btn = QPushButton("Renkleri Düzenle")
        colors_btn.setFixedHeight(int(45 * self.window_scale))
        colors_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2F2F4F, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: {int(8 * self.window_scale)}px;
                font-size: {int(14 * self.window_scale)}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27ae60, stop:1 #020ef2);
            }}
        """)
        
        def renk_sec():
            self.show_custom_colors_dialog_temp(temp_tema, temp_dark_colors, temp_light_colors)
        
        colors_btn.clicked.connect(renk_sec)
        colors_card_layout.addWidget(colors_btn)
        
        content_layout.addWidget(colors_card)

        # 5. SIRA - Hassasiyet kartı
        hass_card = self.create_settings_card(
            "📊   Hassasiyet/Basamak", 
            f"Mevcut: {self.hassasiyet} basamak",
            card_bg, border_color, text_color
        )
        hass_card_layout = hass_card.layout()
        
        hass_buttons = QHBoxLayout()
        hass_buttons.setSpacing(3)
        
        def hass_sec(v, b):
            nonlocal temp_hassasiyet
            temp_hassasiyet = v
            for btn in hass_btn_group:
                if btn == b:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #2F2F4F, stop:1 #229954);
                            color: white;
                            border: {int(2 * self.window_scale)}px solid #27ae60;
                            border-radius: {int(8 * self.window_scale)}px;
                            font-size: {int(15 * self.window_scale)}px;
                            font-weight: bold;
                        }}
                    """)
                    btn.setChecked(True)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {card_bg};
                            color: {text_color};
                            border: {int(2 * self.window_scale)}px solid {border_color};
                            border-radius: {int(8 * self.window_scale)}px;
                            font-size: {int(15 * self.window_scale)}px;
                        }}
                        QPushButton:hover {{
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #27ae60, stop:1 #020ef2);
                        }}
                    """)
                    btn.setChecked(False)
        
        hass_btn_group = []
        for val in [15, 22, 33, 69]:
            btn = QPushButton(str(val))
            # İki haneli sayılar için daha geniş buton
            btn_width = int(92 * self.window_scale) if val >= 33 else int(85 * self.window_scale)
            btn.setFixedSize(btn_width, int(50 * self.window_scale))
            btn.setCheckable(True)
            btn.setChecked(self.hassasiyet == val)
            btn.setProperty("hass_value", val)
            
            if self.hassasiyet == val:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #2F2F4F, stop:1 #229954);
                        color: white;
                        border: {int(2 * self.window_scale)}px solid #27ae60;
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(14 * self.window_scale)}px;
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {card_bg};
                        color: {text_color};
                        border: {int(2 * self.window_scale)}px solid {border_color};
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(15 * self.window_scale)}px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #020ef2, stop:1 #27ae60);
                    }}
                """)
            
            btn.clicked.connect(lambda checked, v=val, b=btn: hass_sec(v, b))
            hass_btn_group.append(btn)
            hass_buttons.addWidget(btn)
        
            hass_card_layout.addLayout(hass_buttons)
        content_layout.addWidget(hass_card)

        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        def apply_and_close():
            # Tema kaydediliyor
            self.tema_modu = temp_tema
            
            # Hassasiyet kaydediliyor
            self.hassasiyet = temp_hassasiyet
            getcontext().prec = temp_hassasiyet
            
            # Renkler kaydediliyor
            self.dark_user_colors = temp_dark_colors.copy()
            self.light_user_colors = temp_light_colors.copy()
            
            # Pencere ölçeği ve tuş biçimi kaydediliyor
            new_scale = scale_slider.value() / 100.0
            new_border = border_slider.value()
            
            self.window_scale = new_scale
            self.border_radius_value = new_border
            
            # Tüm ayarları dosyaya kaydet
            self.hafizaya_kaydet()
            
            # UI'yi güncelle
            mevcut_ifade = self.matematik_ifadesi
            self.apply_window_scale()
            self.ekran.setFixedHeight(int(100 * self.window_scale))
            self.butonlari_sil()
            
            spacing_map = {
                0.6: 4, 0.7: 5, 0.8: 5, 0.9: 6, 1.0: 6,
                1.1: 7, 1.2: 7, 1.3: 8, 1.4: 8, 1.5: 8,
                1.6: 9, 1.7: 9, 1.8: 10, 1.9: 10, 2.0: 11
            }
            scale_rounded = round(self.window_scale, 1)
            spacing = spacing_map.get(scale_rounded, 8)
            self.grid.setSpacing(int(spacing * self.window_scale))
            
            self.layout().setContentsMargins(
                int(12 * self.window_scale),
                int(10 * self.window_scale),
                int(12 * self.window_scale),
                int(15 * self.window_scale)
            )
            self.layout().setSpacing(int(8 * self.window_scale))
            
            self.settings_btn.setFixedSize(
                int(40 * self.window_scale),
                int(30 * self.window_scale)
            )
            
            self.butonlari_olustur()
            self.tema_uygula()
            
            self.matematik_ifadesi = mevcut_ifade
            self.ekran_guncelle()
            
            # Favori Renkler güncelle
            if self.favori_renkler_penceresi and self.favori_renkler_penceresi.isVisible():
                self.favori_renkler_penceresi.secili_tema = self.tema_modu
                self.favori_renkler_penceresi.dark_radio.setChecked(self.tema_modu == 0)
                self.favori_renkler_penceresi.light_radio.setChecked(self.tema_modu == 1)
                self.favori_renkler_penceresi.update_tema_buttons()
                self.favori_renkler_penceresi.dark_radio.setEnabled(self.tema_modu == 0)
                self.favori_renkler_penceresi.light_radio.setEnabled(self.tema_modu == 1)
                self.favori_renkler_penceresi.liste_guncelle()

            dialog.accept()

        # Kaydet butonunu fonksiyona bağla
        apply_btn.clicked.connect(apply_and_close)
        
        dialog.setLayout(main_layout)
        dialog.exec_()
  
    def create_settings_card(self, title, subtitle, bg_color, border_color, text_color):
        """Ayar kartı oluştur"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {int(12 * self.window_scale)}px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            int(20 * self.window_scale),
            int(15 * self.window_scale),
            int(20 * self.window_scale),
            int(15 * self.window_scale)
        )
        card_layout.setSpacing(int(12 * self.window_scale))
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: {int(16 * self.window_scale)}px; font-weight: bold; color: {text_color}; background: transparent; border: none;")
        card_layout.addWidget(title_label)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"font-size: {int(12 * self.window_scale)}px; color: {text_color}; opacity: 0.7; background: transparent; border: none;")

        card_layout.addWidget(subtitle_label)
        
        return card

    def tema_degistir_ve_guncelle(self, mod, active_btn, inactive_btn):
        """Tema değiştir ve butonları güncelle"""
        self.tema_modu = mod
        self.hafizaya_kaydet()
        self.tema_uygula()
        self.update_tema_buttons_style(active_btn if mod == 0 else inactive_btn, 
                                       inactive_btn if mod == 0 else active_btn)

    def update_tema_buttons_style(self, dark_btn, light_btn):
        """Tema butonlarının stilini güncelle"""
        if self.tema_modu == 0:
            # Karanlık seçili
            dark_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2F2F4F, stop:1 #34495e);
                    color: white;
                    border: 2px solid #020ef2;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3a3a5f, stop:1 #415b76);
                }
            """)
            # Aydınlık seçili değil
            light_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #7f8c8d;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #020ef2, stop:1 #27ae60);
                    color: white;
                    border-color: #020ef2;
                }
            """)
        else:
            # Aydınlık seçili
            light_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #27ae60, stop:1 #2F2F4F);
                    color: white;
                    border: 2px solid #f39c12;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f5ab35, stop:1 #ec8c3a);
                }
            """)
            # Karanlık seçili değil
            dark_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #7f8c8d;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #020ef2, stop:1 #27ae60);
                    color: white;
                    border-color: #020ef2;
                }
            """)

    def update_hassasiyet_selection(self, value, clicked_btn, all_buttons, card_bg, border_color, text_color):
        """Hassasiyet seçimini güncelle"""
        self.hassasiyet_kaydet(value)
        
        for btn in all_buttons:
            if btn == clicked_btn:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #2F2F4F, stop:1 #229954);
                        color: white;
                        border: {int(2 * self.window_scale)}px solid #27ae60;
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(14 * self.window_scale)}px;
                        font-weight: bold;
                    }}
                """)
                btn.setChecked(True)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {card_bg};
                        color: {text_color};
                        border: {int(2 * self.window_scale)}px solid {border_color};
                        border-radius: {int(8 * self.window_scale)}px;
                        font-size: {int(14 * self.window_scale)}px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                             stop:0 #27ae60, stop:1 #020ef2);
                    }}
                """)
                btn.setChecked(False)

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

            if c_span == 1:   w = int(72 * self.window_scale)
            elif c_span == 2: w = int(152 * self.window_scale)
            elif c_span == 3: w = int(232 * self.window_scale)
            else:             w = int(312 * self.window_scale)

            h = int(60 * self.window_scale) if r_span == 1 else int(128 * self.window_scale)
            btn.setFixedSize(w, h)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda _, s=sembol: self.aksiyon(s))

            self.grid.addWidget(btn, satir, sutun, r_span, c_span)
            self.butonlar[sembol] = btn

    def tema_uygula(self):
        bg_color = "#000000" if self.tema_modu == 0 else "#f8f9fa"
        self.setStyleSheet(f"QWidget {{ background-color: {bg_color}; }}")

        self.menu.setStyleSheet(f"""
            QMenu {{ background-color: #1e1e1e; color: #e0e0e0; border: 2px solid #444444; padding: 6px; }}
            QMenu::item {{ padding: 10px 25px; }}
            QMenu::item:selected {{ background-color: #3498db; color: white; }}
        """)

        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: transparent; 
                color: #3498db; 
                border: none; 
                border-radius: 8px; 
                font-size: 20px; 
            }}
            QPushButton:hover {{ 
                background-color: rgba(52, 152, 219, 0.2); 
                color: #3498db; 
            }}
        """)

        self.ekran_stilini_guncelle()

        for sembol, btn in self.butonlar.items():
            btn.setStyleSheet(self.get_neon_style(sembol))

    def ekran_stilini_guncelle(self):
        current_colors = self.light_user_colors if self.tema_modu == 1 else self.dark_user_colors
        ekran_yazi = current_colors["screen"]
        ekran_cerceve = current_colors.get("screen_border", "#444444")
        bg_color = "#ffffff" if self.tema_modu == 1 else "#000000"
        
        font_size = int(22 * self.window_scale)
        padding_top = int(25 * self.window_scale)
        padding_left = int(8 * self.window_scale)
        padding_right = int(12 * self.window_scale)
        border_width = int(3 * self.window_scale)
        border_radius = int(10 * self.window_scale)

        self.ekran.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {ekran_yazi};
                border: {border_width}px solid {ekran_cerceve};
                border-radius: {border_radius}px;
                padding-top: {padding_top}px;
                padding-left: {padding_left}px;
                padding-right: {padding_right}px;
                font-size: {font_size}px;
                font-family: 'Liberation Sans';
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
            user_color = current_colors["operators"]

        border_width = 2
        border_radius = int(self.border_radius_value * self.window_scale)
        font_size = int(35 * self.window_scale)

        return f"""
            QPushButton {{
                background-color: transparent;
                color: {user_color};
                border: {border_width}px solid {user_color};
                border-radius: {border_radius}px;
                font-size: {font_size}px;
                font-family: 'Liberation Sans';
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
                    tam_kisim, ondalik_kisim = p.split('.', 1)
                    try:
                        tam_formatli = f"{int(tam_kisim or 0):,}".replace(',', '.')
                    except:
                        tam_formatli = tam_kisim or "0"
                    res += f"{tam_formatli},{ondalik_kisim}"
                else:
                    try:
                        res += f"{int(p):,}".replace(',', '.')
                    except:
                        res += p
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
                    parts = p.split('.', 1)
                    tam = parts[0]
                    ond = parts[1]
                    res += f"{tam}.{ond}"
                else:
                    res += p
            else:
                res += p
        return res

    def keyPressEvent(self, event):
        key = event.key()

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
            ifade = re.sub(r'\)(\d)', r')*\1', ifade)
            ifade = re.sub(r'(\d)\(', r'\1*(', ifade)
            ifade = re.sub(r'(\d)√', r'\1*√', ifade)
            ifade = re.sub(r'\)√', r')*√', ifade)

            max_iterations = 100
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                degisiklik = False

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

                normal_paren = r'(?<!√)\(([^()√]*)\)'
                match = re.search(normal_paren, ifade)
                if match:
                    icerik = match.group(1)
                    try:
                        icerik_decimal = re.sub(r'(\d+\.?\d*|\.\d+)', r"Decimal('\1')", icerik)
                        sonuc = eval(icerik_decimal, {"Decimal": Decimal})
                        
                        bas = match.start()
                        son = match.end()
                        
                        sonuc_str = str(sonuc)
                        
                        oncesi_rakam = bas > 0 and ifade[bas-1].isdigit()
                        sonrasi_rakam = son < len(ifade) and ifade[son].isdigit()
                        
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
                    gecmis_satir = f"{self.format_gecmis(ham_islem)} = ERROR"
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
            
            # ERROR'u geçmişe kaydet
            if sembol == '=' and self.matematik_ifadesi:
                ham_islem = self.matematik_ifadesi
                gecmis_satir = f"{self.format_gecmis(ham_islem)} = ERROR"
                self.gecmis_listesi.append(gecmis_satir)
                self.gecmis_kaydet_kalici(gecmis_satir)
                
                if self.gecmis_penceresi and self.gecmis_penceresi.isVisible():
                    self.gecmis_penceresi.liste_guncelle()
            
            self.matematik_ifadesi = "ERROR"
            self.ekran.setPlainText("ERROR")

    def ekran_guncelle(self):
        gorunum = self.format_gosterim(self.matematik_ifadesi) if self.matematik_ifadesi else "0"
        self.ekran.setPlainText(gorunum)
        self.ekran.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        padding_top_big = int(25 * self.window_scale)
        padding_top_small = int(6 * self.window_scale)

        if len(gorunum) >= 28:
            new_style = self.ekran.styleSheet().replace(f"padding-top: {padding_top_big}px;", f"padding-top: {padding_top_small}px;")
        else:
            new_style = self.ekran.styleSheet().replace(f"padding-top: {padding_top_small}px;", f"padding-top: {padding_top_big}px;")

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

    def favori_renkleri_goster(self):
        if not self.favori_renkler_penceresi:
            self.favori_renkler_penceresi = FavoriRenklerPenceresi(self)
        
        fav = self.favori_renkler_penceresi
        
        # Ana pencerenin temasını Favori penceresine aktar + kilitle
        fav.secili_tema = self.tema_modu
        fav.dark_radio.setChecked(self.tema_modu == 0)
        fav.light_radio.setChecked(self.tema_modu == 1)
        
        fav.update_tema_buttons()
        
        # ★★★ EN ÖNEMLİ KISIM: Diğer temayı pasif yap ★★★
        fav.dark_radio.setEnabled(self.tema_modu == 0)
        fav.light_radio.setEnabled(self.tema_modu == 1)
        
        fav.liste_guncelle()
        
        rect = self.geometry()
        fav.move(rect.right(), rect.top())
        fav.show()

    def show_about_dialog(self):
        """Hakkında penceresini tamamen çift renkli gradient temasına taşır"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Hakkında")
        dialog.setFixedSize(int(345 * self.window_scale), int(250 * self.window_scale))
        
        # Tema renkleri (Metinler için)
        is_dark = self.tema_modu == 0
        arka_plan = "#1a1a1a" if is_dark else "#f8f9fa"
        
        # Ana Pencere Çerçevesi
        dialog.setStyleSheet(f"QDialog {{ background-color: {arka_plan}; border: 2px solid {AYARLAR_NEON_MOR}; border-radius: {int(15 * self.window_scale)}px; }}")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(
            int(15 * self.window_scale),
            int(15 * self.window_scale),
            int(15 * self.window_scale),
            int(15 * self.window_scale)
        )
        layout.setSpacing(int(10 * self.window_scale))

        
        # Başlık
        baslik = QLabel("Hakkında")
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet(f"font-size: {int(22 * self.window_scale)}px; font-weight: bold; color: {AYARLAR_NEON_MOR}; background: transparent; border: none;")
        
        # İçerik Metni Kutusu (Lacivert -> Yeşil Geçişli)
        icerik = QLabel(
            f"<div style='text-align: center; color: #6302e2;'>" 
            f"<p style='font-size: {int(18 * self.window_scale)}px;'><b>Neon Hesap Makinesi v2.0</b></p>"
            f"<p style='font-size: {int(16 * self.window_scale)}px;'>Ahmet (NikBulamadim)</p>"
            f"<p style='font-size: {int(14 * self.window_scale)}px; opacity: 0.8;'>Copyright © 2026 NikBulamadim</p>"
            "</div>"
        )
        icerik.setAlignment(Qt.AlignCenter)
        icerik.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 #2F2F4F, 
                            stop:1 #27ae60);
                border-radius: {int(12 * self.window_scale)}px;
                padding: {int(15 * self.window_scale)}px;
                border: none;
            }}
        """)

        # Kapat Butonu
        kapat_btn = QPushButton("Kapat")
        kapat_btn.setCursor(Qt.PointingHandCursor)
        kapat_btn.clicked.connect(dialog.accept)
        kapat_btn.setFixedSize(int(110 * self.window_scale), int(35 * self.window_scale))
        
        # BUTONUN HER İKİ HALİ DE ÇİFT RENKLİ:
        kapat_btn.setStyleSheet(f"""
            QPushButton {{ 
                /* Normal duruş: Mor -> Koyu Yeşil Geçişi */
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 {AYARLAR_NEON_MOR}, 
                            stop:1 #1e8449); 
                color: white; 
                border-radius: 8px; 
                font-weight: bold; 
                border: none;
            }}
            /* Üzerine gelince (Hover): Daha parlak Mor -> Daha canlı Yeşil Geçişi */
            QPushButton:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #9b59b6, 
                            stop:1 #27ae60); 
            }}
        """)

        layout.addWidget(baslik)
        layout.addWidget(icerik)
        layout.addWidget(kapat_btn, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeonHesapMakinesi()
    window.show()
    sys.exit(app.exec_())
