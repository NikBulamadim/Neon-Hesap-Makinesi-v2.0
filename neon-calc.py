#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import re
from decimal import Decimal, getcontext

if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    if os.path.exists("/usr/bin/Xwayland") or os.path.exists("/usr/bin/X"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QGridLayout, QTextEdit, QPushButton, QMenu, QHBoxLayout,
                             QSpacerItem, QSizePolicy, QDialog, QLabel, QScrollArea, QActionGroup)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor, QTextOption

getcontext().prec = 69

AYAR_DOSYASI = os.path.expanduser("~/.neon_calc_config")
GECMIS_DOSYASI = os.path.expanduser("~/.neon_calc_history")
AYARLAR_NEON_MOR = "#D500F9"

NEON_YESIL   = "#39FF14"
NEON_KIRMIZI = "#FF3131"
NEON_MAVI    = "#00D4FF"
NEON_MOR     = "#5800FF"
NEON_SARI    = "#FFF600"

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
        from PyQt5.QtWidgets import QFileDialog
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
        self.setFixedSize(340,575)
        ayarlar = self.hafizadan_yukle()
        self.renk_modu_karanlik = ayarlar[0]
        self.renk_modu_aydinlik = ayarlar[1]
        self.tema_modu = ayarlar[2]
        self.setWindowIcon(QtGui.QIcon("/usr/share/pixmaps/neon-calc.png"))
        self.matematik_ifadesi = ""
        self.font_name = "Liberation Sans"
        self.butonlar = {}
        self.gecmis_penceresi = None
        self.gecmis_listesi = self.gecmis_yukle_kalici()
        self.hassasiyet = self.hafizadan_hassasiyet_yukle()
        getcontext().prec = self.hassasiyet
        self.init_ui()
        self.tema_uygula()
        self.ekran.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ekran.customContextMenuRequested.connect(self.show_ekran_context_menu)

    def show_ekran_context_menu(self, position):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1A1A1A;
                color: white;
                border: 2px solid #D500F9;
                padding: 4px 0;
                font-family: 'Liberation Sans';
            }
            QMenu::item {
                padding: 8px 30px 8px 24px;
                color: white;
            }
            QMenu::item:selected {
                background-color: #D500F9;
                color: black;
            }
        """)
        copy_act = menu.addAction("Kopyala")
        select_all_act = menu.addAction("Tümünü Seç")
        copy_act.triggered.connect(self.ekran.copy)
        select_all_act.triggered.connect(self.ekran.selectAll)
        menu.exec_(self.ekran.mapToGlobal(position))

    def hafizadan_yukle(self):
        try:
            if os.path.exists(AYAR_DOSYASI):
                with open(AYAR_DOSYASI, "r") as f:
                    data = f.read().strip().split(',')
                    vals = [int(x) for x in data if x.strip()]
                    while len(vals) < 4:
                        if len(vals) == 0: vals.append(1)
                        elif len(vals) == 1: vals.append(1)
                        elif len(vals) == 2: vals.append(0)
                        else: vals.append(69)
                    if vals[0] < 1 or vals[0] > 5:
                        vals[0] = 1
                    return tuple(vals)
        except:
            pass
        return (1, 1, 0, 69)

    def hafizadan_hassasiyet_yukle(self):
        return self.hafizadan_yukle()[3]

    def hafizaya_kaydet(self):
        try:
            with open(AYAR_DOSYASI, "w") as f:
                f.write(f"{self.renk_modu_karanlik},{self.renk_modu_aydinlik},{self.tema_modu},{self.hassasiyet}")
        except:
            pass

    def hassasiyet_kaydet(self, yeni_hassasiyet):
        self.hassasiyet = yeni_hassasiyet
        getcontext().prec = yeni_hassasiyet
        self.hafizaya_kaydet()
        self.ekran_guncelle()

    def gecmis_yukle_kalici(self):
        try:
            if os.path.exists(GECMIS_DOSYASI):
                with open(GECMIS_DOSYASI, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f.readlines() if line.strip()]
        except:
            pass
        return []

    def gecmis_kaydet_kalici(self, satir):
        try:
            with open(GECMIS_DOSYASI, "a", encoding="utf-8") as f:
                f.write(satir + "\n")
        except:
            pass

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
        act_15.triggered.connect(lambda: self.hassasiyet_kaydet(15))
        act_22.triggered.connect(lambda: self.hassasiyet_kaydet(22))
        act_33.triggered.connect(lambda: self.hassasiyet_kaydet(33))
        act_69.triggered.connect(lambda: self.hassasiyet_kaydet(69))
        acts = {15: act_15, 22: act_22, 33: act_33, 69: act_69}
        if self.hassasiyet in acts:
            acts[self.hassasiyet].setChecked(True)
        self.menu.addSeparator()
        self.renk_degis_act = self.menu.addAction("Renk Değiştir (T)")
        self.settings_btn.setMenu(self.menu)
        self.light_tema_act.triggered.connect(lambda: self.tema_degistir(1))
        self.dark_tema_act.triggered.connect(lambda: self.tema_degistir(0))
        self.renk_degis_act.triggered.connect(self.renk_dongusu)
        self.gecmis_act.triggered.connect(self.gecmisi_goster)
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

    def butonlari_olustur(self):
        for sembol, satir, sutun, r_span, c_span in self.tus_haritasi:
            if sembol == "BACK":
                btn_text = "⌫"
            elif sembol == "√":
                btn_text = "√"
            else:
                btn_text = sembol
            btn = QPushButton(btn_text)
            if c_span == 1: w = 72
            elif c_span == 2: w = 152
            elif c_span == 3: w = 232
            else: w = 312
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
            self.renk_modu_karanlik = self.renk_modu_karanlik + 1 if self.renk_modu_karanlik < 5 else 1
        else:
            self.renk_modu_aydinlik = self.renk_modu_aydinlik + 1 if self.renk_modu_aydinlik < 3 else 1
        self.hafizaya_kaydet()
        self.tema_uygula()

    def get_current_neon_color(self):
        renk_modu = self.renk_modu_karanlik if self.tema_modu == 0 else self.renk_modu_aydinlik
        if renk_modu == 1: return "#39FF14"
        if renk_modu == 2: return "#00FFFF"
        if renk_modu == 3: return "#FF00FF"
        if renk_modu == 4: return NEON_MAVI
        if renk_modu == 5: return NEON_MOR
        return "#FF00FF"

    def tema_uygula(self):
        bg_color = "#000000" if self.tema_modu == 0 else "#F2F4F7"
        self.setStyleSheet(f"QWidget {{ background-color: {bg_color}; }}")
        self.menu.setStyleSheet(f"""
            QMenu {{ background-color: #1A1A1A; color: {AYARLAR_NEON_MOR}; border: 2px solid {AYARLAR_NEON_MOR}; padding: 6px; font-family: '{self.font_name}'; }}
            QMenu::item {{ padding: 10px 25px; }}
            QMenu::item:selected {{ background-color: {AYARLAR_NEON_MOR}; color: #000000; }}
        """)
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {AYARLAR_NEON_MOR}; border: 2px solid {AYARLAR_NEON_MOR}; border-radius: 8px; font-size: 20px; }}
            QPushButton:hover {{ background-color: {AYARLAR_NEON_MOR}; color: #000000; }}
            QPushButton::menu-indicator {{ image: none; }}
        """)
        self.ekran_stilini_guncelle()
        for sembol, btn in self.butonlar.items():
            btn.setStyleSheet(self.get_neon_style(sembol))

    def get_neon_style(self, sembol):
        renk_modu = self.renk_modu_karanlik if self.tema_modu == 0 else self.renk_modu_aydinlik
        if self.tema_modu == 1:
            if renk_modu == 1: btn_bg = "rgba(57, 255, 20, 0.12)"
            elif renk_modu == 2: btn_bg = "rgba(0, 180, 216, 0.12)"
            else: btn_bg = "rgba(213, 0, 249, 0.12)"
            border_width = "1.5px"
        else:
            btn_bg = "transparent"
            border_width = "1.5px"
        color = "#FFFFFF" if self.tema_modu == 0 else "#1A1A1A"
        if self.tema_modu == 0:
            if renk_modu == 4:
                if sembol.isdigit() or sembol == ".":
                    color = NEON_YESIL
                elif sembol in 'CBACK':
                    color = NEON_KIRMIZI
                elif sembol in '/*+-()=√':
                    color = NEON_MAVI
                else:
                    color = NEON_YESIL
            elif renk_modu == 5:
                if sembol.isdigit() or sembol == ".":
                    color = NEON_MOR
                elif sembol in 'CBACK':
                    color = NEON_KIRMIZI
                else:
                    color = NEON_SARI
            elif renk_modu == 1:
                if sembol in '/*+-()=√': color = "#00FFFF"
                if sembol in 'CBACK': color = "#FF3131"
                elif sembol == '=': color = "#39FF14"
            elif renk_modu == 2:
                if sembol in 'CBACK': color = "#C62828"
                elif sembol in '/*+-()=√': color = "#0077B6" if self.tema_modu == 1 else "#FFDB58"
                else: color = "#023E8A" if self.tema_modu == 1 else "#00FFFF"
            elif renk_modu == 3:
                color = "#7B1FA2" if self.tema_modu == 1 else "#FF00FF"
                if sembol in 'CBACK': color = "#C62828"
                elif sembol in '/*+-()=√': color = "#00838F" if self.tema_modu == 1 else "#00FFFF"
        if self.tema_modu == 1 and (sembol.isdigit() or sembol == "."):
            color = "#1A1A1A"
        return f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {color};
                border: {border_width} solid {color};
                border-radius: 10px;
                font-size: 18px;
                font-family: '{self.font_name}';
            }}
            QPushButton:hover, QPushButton:pressed {{
                background-color: {color};
                color: {'#FFFFFF' if self.tema_modu == 1 else '#000000'};
            }}
        """

    def ekran_stilini_guncelle(self):
        renk_modu = self.renk_modu_karanlik if self.tema_modu == 0 else self.renk_modu_aydinlik
        if self.tema_modu == 1:
            if renk_modu == 1: ekran_rengi = "#2E7D32"
            elif renk_modu == 2: ekran_rengi = "#0077B6"
            else: ekran_rengi = "#7B1FA2"
            bg_color = "rgba(0, 0, 0, 0.05)"
        else:
            ekran_rengi = self.get_current_neon_color()
            bg_color = "#000000"
        self.ekran.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {ekran_rengi};
                border: 3px solid {ekran_rengi};
                border-radius: 10px;
                padding-top: 25px;
                padding-left: 8px;
                padding-right: 12px;
                font-size: 22px;
                font-family: '{self.font_name}';
            }}
        """)

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
        elif key == Qt.Key_Plus: sembol = "+"
        elif key == Qt.Key_Minus: sembol = "-"
        elif key == Qt.Key_Asterisk: sembol = "*"
        elif key == Qt.Key_Slash: sembol = "/"
        elif key == Qt.Key_ParenLeft: sembol = "("
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
        """Karekök hesaplama fonksiyonu"""
        try:
            if deger < 0:
                return None
            return deger.sqrt()
        except:
            return None

    def ifadeyi_isle(self, ifade):
        """√ sembollerini işler ve hesaplar - KAPSAMLI ÇÖZÜM"""
        try:
            # Önce rakam√ ifadelerini rakam*√ formatına çevir
            ifade = re.sub(r'(\d)√', r'\1*√', ifade)
            # )√ ifadelerini )*√ formatına çevir
            ifade = re.sub(r'\)√', r')*√', ifade)
            
            max_iterations = 100
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                degisiklik = False
                
                # 1. ÖNCELİK: Basit √sayı formatını işle (parantez yok)
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
                
                # 2. ÖNCELİK: √ içinde parantezli ama içinde √ olmayan: √(25+10)
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
                
                # 3. ÖNCELİK: Normal parantez (√ olmayan ve içinde √ olmayan): (5*4)
                normal_paren = r'(?<!√)\(([^()√]*)\)'
                match = re.search(normal_paren, ifade)
                if match:
                    icerik = match.group(1)
                    try:
                        icerik_decimal = re.sub(r'(\d+\.?\d*|\.\d+)', r"Decimal('\1')", icerik)
                        sonuc = eval(icerik_decimal, {"Decimal": Decimal})
                        ifade = ifade[:match.start()] + str(sonuc) + ifade[match.end():]
                        degisiklik = True
                        continue
                    except:
                        pass
                
                # Hiçbir değişiklik yoksa dur
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
                
                # Eksik parantezleri kapat
                ap, kp = islem.count('('), islem.count(')')
                if ap > kp:
                    islem += ')' * (ap - kp)
                
                # √ işlemlerini çöz
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
                
                # Normal işlemleri çöz
                islem_islenmis = re.sub(r'(\d+\.?\d*|\.\d+)', r"Decimal('\1')", islem_islenmis)
                sonuc = eval(islem_islenmis, {"Decimal": Decimal}).normalize()
                
                # Yuvarlama hatası düzeltme
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
    app = QApplication(sys.argv)
    window = NeonHesapMakinesi()
    window.show()
    sys.exit(app.exec_())
