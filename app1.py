import sys
import os
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QFormLayout, QComboBox, QHBoxLayout, QSizePolicy, 
    QCheckBox, QMessageBox, QFrame, QGridLayout
)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor, QFontDatabase
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from datetime import datetime
from collections import defaultdict


CACHE_FILE = "weather_cache.json"


def get_weather_icon(icon_code):
    cache_dir = "icon_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    icon_path = os.path.join(cache_dir, f"{icon_code}.png")

    if os.path.exists(icon_path):
        return icon_path

    url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(icon_path, "wb") as file:
                file.write(response.content)
            return icon_path
    except Exception as e:
        print(f"Erreur lors du téléchargement de l'icône : {e}")
    return None


def save_to_cache(data):
    with open(CACHE_FILE, "w") as file:
        json.dump(data, file)


def load_from_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    return None


class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._scale_factor = 1.0
        self._animation = QPropertyAnimation(self, b"scale_factor")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    @pyqtProperty(float)
    def scale_factor(self):
        return self._scale_factor

    @scale_factor.setter
    def scale_factor(self, value):
        self._scale_factor = value
        self.update()

    def enterEvent(self, event):
        self._animation.setStartValue(self._scale_factor)
        self._animation.setEndValue(1.05)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.setStartValue(self._scale_factor)
        self._animation.setEndValue(1.0)
        self._animation.start()
        super().leaveEvent(event)


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌤️ Application Météo Avancée")
        self.setMinimumSize(450, 700)
        
        # Variables de configuration
        self.language = "fr"
        self.units = "metric"
        self.auto_geo_enabled = False
        self.is_dark_theme = False
        self.current_city = ""
        self.current_weather_data = None

        # Dictionnaire des traductions complet
        self.translations = {
            "fr": {
                "language": "Langue",
                "units": "Unités",
                "search": "Rechercher",
                "theme": "Changer de Thème",
                "auto_geo": "Géolocalisation automatique",
                "enter_city": "Entrez le nom de la ville",
                "sunrise": "Lever du soleil",
                "sunset": "Coucher du soleil",
                "weather_not_found": "Ville non trouvée ou erreur API.",
                "geo_failed": "Impossible de détecter l'emplacement.",
                "geo_error": "Erreur de géolocalisation",
                "no_cache": "Aucune donnée en cache disponible.",
                "weather_for": "Prévisions pour le",
                "temp": "Température",
                "description": "Description",
                "humidity": "Humidité",
                "pressure": "Pression",
                "wind": "Vent",
                "location": "Lieu",
                "forecast": "Prévisions",
                "current_weather": "Météo actuelle",
                "please_enter_city": "Veuillez entrer une ville ou activer la géolocalisation.",
                "geo_success": "Géolocalisation réussie",
                "your_city": "Votre ville détectée est"
            },
            "en": {
                "language": "Language",
                "units": "Units",
                "search": "Search",
                "theme": "Switch Theme",
                "auto_geo": "Auto geolocation",
                "enter_city": "Enter city name",
                "sunrise": "Sunrise",
                "sunset": "Sunset",
                "weather_not_found": "City not found or API error.",
                "geo_failed": "Unable to detect location.",
                "geo_error": "Geolocation error",
                "no_cache": "No cached data available.",
                "weather_for": "Forecast for",
                "temp": "Temperature",
                "description": "Description",
                "humidity": "Humidity",
                "pressure": "Pressure",
                "wind": "Wind",
                "location": "Location",
                "forecast": "Forecast",
                "current_weather": "Current weather",
                "please_enter_city": "Please enter a city or enable geolocation.",
                "geo_success": "Geolocation successful",
                "your_city": "Your detected city is"
            },
            "ar": {
                "language": "اللغة",
                "units": "الوحدات",
                "search": "بحث",
                "theme": "تغيير السمة",
                "auto_geo": "تحديد الموقع التلقائي",
                "enter_city": "أدخل اسم المدينة",
                "sunrise": "شروق الشمس",
                "sunset": "غروب الشمس",
                "weather_not_found": "المدينة غير موجودة أو خطأ في API.",
                "geo_failed": "غير قادر على تحديد الموقع.",
                "geo_error": "خطأ في تحديد الموقع",
                "no_cache": "لا توجد بيانات مخزنة متاحة.",
                "weather_for": "توقعات لـ",
                "temp": "درجة الحرارة",
                "description": "الوصف",
                "humidity": "الرطوبة",
                "pressure": "الضغط",
                "wind": "الرياح",
                "location": "الموقع",
                "forecast": "التوقعات",
                "current_weather": "الطقس الحالي",
                "please_enter_city": "الرجاء إدخال مدينة أو تمكين تحديد الموقع.",
                "geo_success": "تم تحديد الموقع بنجاح",
                "your_city": "المدينة المكتشفة هي"
            }
        }

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        """Initialise l'interface utilisateur avec un style moderne"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # En-tête avec dégradé
        header_label = QLabel("🌤️ Application Météo")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setObjectName("headerLabel")
        main_layout.addWidget(header_label)

        # Section de configuration avec carte moderne
        config_frame = QFrame()
        config_frame.setObjectName("configFrame")
        config_layout = QGridLayout()
        config_layout.setVerticalSpacing(12)
        config_layout.setHorizontalSpacing(20)

        # Sélecteur de langue
        config_layout.addWidget(QLabel(self._tr("language") + ":"), 0, 0)
        self.language_selector = QComboBox()
        self.language_selector.addItems(["Français", "English", "العربية"])
        self.language_selector.setCurrentText("Français")
        self.language_selector.currentTextChanged.connect(self.change_language)
        config_layout.addWidget(self.language_selector, 0, 1)

        # Sélecteur d'unités
        config_layout.addWidget(QLabel(self._tr("units") + ":"), 1, 0)
        self.units_selector = QComboBox()
        self.units_selector.addItems(["°C (Métrique)", "°F (Impérial)"])
        self.units_selector.currentTextChanged.connect(self.change_units)
        config_layout.addWidget(self.units_selector, 1, 1)

        config_frame.setLayout(config_layout)
        main_layout.addWidget(config_frame)

        # Géolocalisation automatique avec style moderne
        self.geo_checkbox = QCheckBox(self._tr("auto_geo"))
        self.geo_checkbox.setObjectName("geoCheckbox")
        self.geo_checkbox.stateChanged.connect(self.toggle_geo)
        main_layout.addWidget(self.geo_checkbox)

        # Recherche de ville avec style moderne
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText(self._tr("enter_city"))
        self.city_input.setObjectName("cityInput")
        self.city_input.returnPressed.connect(self.fetch_weather)
        search_layout.addWidget(self.city_input)

        self.search_button = AnimatedButton(self._tr("search"))
        self.search_button.setObjectName("searchButton")
        self.search_button.clicked.connect(self.fetch_weather)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # Bouton thème avec animation
        self.theme_button = AnimatedButton(self._tr("theme"))
        self.theme_button.setObjectName("themeButton")
        self.theme_button.clicked.connect(self.toggle_theme)
        main_layout.addWidget(self.theme_button)

        # Zone de défilement pour les prévisions
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setObjectName("scrollArea")
        
        self.forecast_widget = QWidget()
        self.forecast_widget.setObjectName("forecastWidget")
        self.forecast_layout = QVBoxLayout()
        self.forecast_layout.setSpacing(20)
        self.forecast_layout.setAlignment(Qt.AlignTop)
        self.forecast_layout.setContentsMargins(5, 5, 5, 5)
        self.forecast_widget.setLayout(self.forecast_layout)
        self.scroll_area.setWidget(self.forecast_widget)
        
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

    def _tr(self, key):
        """Helper method for translation"""
        return self.translations[self.language].get(key, key)

    def change_language(self, lang_text):
        """Change la langue de l'application"""
        lang_map = {"Français": "fr", "English": "en", "العربية": "ar"}
        self.language = lang_map.get(lang_text, "fr")
        self.update_ui()
        # Rafraîchir l'affichage si des données sont déjà chargées
        if self.current_weather_data:
            self.refresh_display()

    def change_units(self, units_text):
        """Change les unités de température"""
        self.units = "metric" if "°C" in units_text else "imperial"
        if self.current_city:
            self.get_weather_data(self.current_city)

    def toggle_geo(self, state):
        """Active/désactive la géolocalisation automatique"""
        self.auto_geo_enabled = state == Qt.Checked
        if self.auto_geo_enabled:
            self.fetch_weather_by_location()

    def toggle_theme(self):
        """Bascule entre le thème sombre et clair"""
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()
        # Rafraîchir l'affichage après changement de thème
        if self.current_weather_data:
            self.refresh_display()

    def apply_theme(self):
        """Applique un thème moderne avec dégradés et animations"""
        if self.is_dark_theme:
            # Thème sombre moderne
            self.setStyleSheet("""
                /* Thème Sombre Moderne */
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1a1a2e, stop:1 #16213e);
                    color: #e6e6e6;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                    font-size: 14px;
                }

                #headerLabel {
                    font-size: 28px;
                    font-weight: bold;
                    color: #667eea;
                    padding: 10px;
                    margin-bottom: 10px;
                    background: transparent;
                }

                #configFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(58, 12, 163, 0.3), stop:1 rgba(114, 9, 183, 0.3));
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 20px;
                }

                QComboBox {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4a4a4a, stop:1 #2d2d2d);
                    border: 2px solid #555;
                    border-radius: 12px;
                    padding: 10px 15px;
                    color: #ffffff;
                    font-weight: 500;
                    min-width: 120px;
                }

                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }

                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #ffffff;
                    width: 0px;
                    height: 0px;
                }

                QComboBox:hover {
                    border: 2px solid #667eea;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5a5a5a, stop:1 #3d3d3d);
                }

                QComboBox QAbstractItemView {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2d2d2d, stop:1 #4a4a4a);
                    border: 1px solid #667eea;
                    border-radius: 8px;
                    color: white;
                    selection-background-color: #667eea;
                }

                #cityInput {
                    background: rgba(255, 255, 255, 0.1);
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    border-radius: 14px;
                    padding: 12px 18px;
                    color: white;
                    font-size: 14px;
                    selection-background-color: #667eea;
                }

                #cityInput:focus {
                    border: 2px solid #667eea;
                    background: rgba(255, 255, 255, 0.15);
                }

                #cityInput::placeholder {
                    color: rgba(255, 255, 255, 0.5);
                }

                #searchButton, #themeButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border: none;
                    border-radius: 14px;
                    padding: 12px 25px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }

                #searchButton:hover, #themeButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #764ba2, stop:1 #667eea);
                }

                #searchButton:pressed, #themeButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5a67d8, stop:1 #6b46c1);
                }

                #geoCheckbox {
                    color: #e6e6e6;
                    font-weight: 500;
                    spacing: 8px;
                }

                #geoCheckbox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #667eea;
                    border-radius: 6px;
                    background: transparent;
                }

                #geoCheckbox::indicator:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border: 2px solid #667eea;
                }

                #scrollArea {
                    border: none;
                    background: transparent;
                }

                #forecastWidget {
                    background: transparent;
                }

                QLabel {
                    background: transparent;
                }

                /* Styles pour les cartes météo en thème sombre */
                #cityFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(102, 126, 234, 0.2), stop:1 rgba(118, 75, 162, 0.2));
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 20px;
                }

                #dayFrame {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    margin: 10px 0px;
                }

                #forecastFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(102, 126, 234, 0.15), stop:1 rgba(118, 75, 162, 0.15));
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    margin: 5px 0px;
                }

                #forecastFrame:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(102, 126, 234, 0.2), stop:1 rgba(118, 75, 162, 0.2));
                    border: 1px solid rgba(102, 126, 234, 0.4);
                }
            """)
        else:
            # Thème clair moderne
            self.setStyleSheet("""
                /* Thème Clair Moderne */
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f5f7fa, stop:1 #c3cfe2);
                    color: #2d3748;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                    font-size: 14px;
                }

                #headerLabel {
                    font-size: 28px;
                    font-weight: bold;
                    color: #667eea;
                    padding: 10px;
                    margin-bottom: 10px;
                    background: transparent;
                }

                #configFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(102, 126, 234, 0.1), stop:1 rgba(118, 75, 162, 0.1));
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.5);
                    padding: 20px;
                }

                QComboBox {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f7fafc);
                    border: 2px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 10px 15px;
                    color: #2d3748;
                    font-weight: 500;
                    min-width: 120px;
                }

                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }

                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #667eea;
                    width: 0px;
                    height: 0px;
                }

                QComboBox:hover {
                    border: 2px solid #667eea;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #edf2f7);
                }

                QComboBox QAbstractItemView {
                    background: white;
                    border: 1px solid #667eea;
                    border-radius: 8px;
                    color: #2d3748;
                    selection-background-color: #667eea;
                    selection-color: white;
                }

                #cityInput {
                    background: rgba(255, 255, 255, 0.8);
                    border: 2px solid #e2e8f0;
                    border-radius: 14px;
                    padding: 12px 18px;
                    color: #2d3748;
                    font-size: 14px;
                    selection-background-color: #667eea;
                    selection-color: white;
                }

                #cityInput:focus {
                    border: 2px solid #667eea;
                    background: rgba(255, 255, 255, 0.95);
                }

                #cityInput::placeholder {
                    color: #a0aec0;
                }

                #searchButton, #themeButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border: none;
                    border-radius: 14px;
                    padding: 12px 25px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }

                #searchButton:hover, #themeButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #764ba2, stop:1 #667eea);
                }

                #searchButton:pressed, #themeButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5a67d8, stop:1 #6b46c1);
                }

                #geoCheckbox {
                    color: #2d3748;
                    font-weight: 500;
                    spacing: 8px;
                }

                #geoCheckbox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #667eea;
                    border-radius: 6px;
                    background: transparent;
                }

                #geoCheckbox::indicator:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border: 2px solid #667eea;
                }

                #scrollArea {
                    border: none;
                    background: transparent;
                }

                #forecastWidget {
                    background: transparent;
                }

                QLabel {
                    background: transparent;
                }

                /* Styles pour les cartes météo en thème clair */
                #cityFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(102, 126, 234, 0.15), stop:1 rgba(118, 75, 162, 0.15));
                    border-radius: 16px;
                    border: 1px solid rgba(102, 126, 234, 0.3);
                    padding: 20px;
                }

                #dayFrame {
                    background: rgba(255, 255, 255, 0.6);
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.8);
                    padding: 15px;
                    margin: 10px 0px;
                }

                #forecastFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(102, 126, 234, 0.08), stop:1 rgba(118, 75, 162, 0.08));
                    border-radius: 12px;
                    border: 1px solid rgba(102, 126, 234, 0.2);
                    padding: 15px;
                    margin: 5px 0px;
                }

                #forecastFrame:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(102, 126, 234, 0.12), stop:1 rgba(118, 75, 162, 0.12));
                    border: 1px solid rgba(102, 126, 234, 0.4);
                }
            """)

    def refresh_display(self):
        """Rafraîchit l'affichage avec les données actuelles"""
        if self.current_weather_data and self.current_city:
            self.display_forecast(self.current_weather_data, self.current_city)

    def update_ui(self):
        """Met à jour tous les textes de l'interface"""
        self.geo_checkbox.setText(self._tr("auto_geo"))
        self.city_input.setPlaceholderText(self._tr("enter_city"))
        self.search_button.setText(self._tr("search"))
        self.theme_button.setText(self._tr("theme"))
        
        config_widget = self.layout().itemAt(1).widget()
        config_layout = config_widget.layout()
        config_layout.itemAtPosition(0, 0).widget().setText(self._tr("language") + ":")
        config_layout.itemAtPosition(1, 0).widget().setText(self._tr("units") + ":")
        
        # Rafraîchir l'affichage si des données sont déjà chargées
        if self.current_weather_data:
            self.refresh_display()

    def fetch_weather(self):
        """Récupère les données météo"""
        city = self.city_input.text().strip()
        self.current_city = city
        
        if not city and not self.auto_geo_enabled:
            self.clear_forecast()
            self.show_message(self._tr("please_enter_city"))
            return

        if self.auto_geo_enabled:
            self.fetch_weather_by_location()
        else:
            self.get_weather_data(city)

    def fetch_weather_by_location(self):
        """Récupère la météo par géolocalisation"""
        try:
            location_response = requests.get("http://ip-api.com/json")
            location_data = location_response.json()
            if location_data["status"] == "success":
                city = location_data["city"]
                self.current_city = city
                self.city_input.setText(city)
                QMessageBox.information(self, self._tr("geo_success"), 
                                      f"{self._tr('your_city')}: {city}")
                self.get_weather_data(city)
            else:
                self.show_message(self._tr("geo_failed"))
        except Exception as e:
            self.show_message(f"{self._tr('geo_error')}: {str(e)}")

    def get_weather_data(self, city):
        """Récupère les données météo depuis l'API"""
        API_KEY = "51bebaba0b3d81cf65f16ee8f5394b74"
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units={self.units}&lang={self.language}"

        try:
            response = requests.get(url)
            data = response.json()

            if data.get("cod") != "200":
                self.show_message(self._tr("weather_not_found"))
                return

            save_to_cache(data)
            self.current_weather_data = data
            self.display_forecast(data, city)

        except Exception as e:
            print(f"Erreur API: {e}")
            self.display_cached_weather()

    def display_forecast(self, data, city):
        """Affiche les prévisions météo avec un style moderne"""
        self.clear_forecast()
        daily_forecasts = defaultdict(list)

        # Informations de la ville
        city_info = data["city"]
        sunrise = city_info["sunrise"]
        sunset = city_info["sunset"]
        timezone_offset = city_info["timezone"]
        
        sunrise_local = datetime.utcfromtimestamp(sunrise + timezone_offset).strftime("%H:%M")
        sunset_local = datetime.utcfromtimestamp(sunset + timezone_offset).strftime("%H:%M")

        # En-tête des informations de la ville avec style moderne
        city_frame = QFrame()
        city_frame.setObjectName("cityFrame")
        
        city_layout = QGridLayout()
        city_layout.setVerticalSpacing(10)
        city_layout.setHorizontalSpacing(20)
        
        location_label = QLabel(f"📍 {self._tr('location')}: {city}")
        location_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #667eea;")
        
        sunrise_label = QLabel(f"🌅 {self._tr('sunrise')}: {sunrise_local}")
        sunrise_label.setStyleSheet("color: #f6ad55; font-weight: 500;")
        
        sunset_label = QLabel(f"🌇 {self._tr('sunset')}: {sunset_local}")
        sunset_label.setStyleSheet("color: #ed8936; font-weight: 500;")
        
        city_layout.addWidget(location_label, 0, 0, 1, 2)
        city_layout.addWidget(sunrise_label, 1, 0)
        city_layout.addWidget(sunset_label, 1, 1)
        city_frame.setLayout(city_layout)
        self.forecast_layout.addWidget(city_frame)

        # Grouper les prévisions par jour
        for forecast in data.get("list", []):
            dt_txt = forecast.get("dt_txt", "")
            date_str = dt_txt.split(" ")[0]
            daily_forecasts[date_str].append(forecast)

        # Afficher les prévisions par jour
        for date_str, forecasts in daily_forecasts.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%d/%m/%Y")
            
            day_frame = QFrame()
            day_frame.setObjectName("dayFrame")
            
            day_layout = QVBoxLayout()
            day_layout.setSpacing(15)
            
            # En-tête du jour
            day_header = QLabel(f"📅 {self._tr('weather_for')} {date_formatted}")
            day_header.setStyleSheet("""
                font-weight: 700;
                font-size: 18px;
                color: #667eea;
                margin: 5px 0px;
                padding: 5px;
                border-bottom: 2px solid #667eea;
            """)
            day_header.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(day_header)

            # Prévisions pour ce jour
            for forecast in forecasts:
                time = forecast["dt_txt"].split(" ")[1][:5]
                temp = forecast["main"].get("temp", "N/A")
                description = forecast["weather"][0].get("description", "").capitalize()
                humidity = forecast["main"].get("humidity", "N/A")
                pressure = forecast["main"].get("pressure", "N/A")
                wind_speed = forecast["wind"].get("speed", "N/A")
                icon_code = forecast["weather"][0].get("icon", "")
                icon_path = get_weather_icon(icon_code)

                # Créer un frame pour chaque prévision
                forecast_frame = QFrame()
                forecast_frame.setObjectName("forecastFrame")
                
                forecast_layout = QHBoxLayout()
                forecast_layout.setSpacing(15)
                
                # Icône météo
                icon_label = QLabel()
                if icon_path and os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path).scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon_label.setPixmap(pixmap)
                else:
                    icon_label.setText("🌤️")
                    icon_label.setStyleSheet("font-size: 24px;")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(80, 70)
                
                forecast_layout.addWidget(icon_label)

                # Informations météo
                info_layout = QVBoxLayout()
                info_layout.setSpacing(4)
                
                time_label = QLabel(f"🕒 {time}")
                time_label.setStyleSheet("font-weight: bold; color: #667eea; font-size: 14px;")
                
                temp_label = QLabel(f"🌡️ {self._tr('temp')}: {temp}°{'C' if self.units == 'metric' else 'F'}")
                temp_label.setStyleSheet("font-weight: 500;")
                
                desc_label = QLabel(f"📝 {self._tr('description')}: {description}")
                humidity_label = QLabel(f"💧 {self._tr('humidity')}: {humidity}%")
                pressure_label = QLabel(f"📊 {self._tr('pressure')}: {pressure} hPa")
                wind_label = QLabel(f"💨 {self._tr('wind')}: {wind_speed} m/s")
                
                # Appliquer les couleurs selon le thème
                text_color = "#718096" if not self.is_dark_theme else "#cbd5e0"
                for label in [temp_label, desc_label, humidity_label, pressure_label, wind_label]:
                    label.setStyleSheet(f"font-size: 12px; color: {text_color};")
                    label.setWordWrap(True)
                    info_layout.addWidget(label)
                
                # Ajouter le temps en premier
                info_layout.insertWidget(0, time_label)
                forecast_layout.addLayout(info_layout)
                forecast_frame.setLayout(forecast_layout)
                day_layout.addWidget(forecast_frame)

            day_frame.setLayout(day_layout)
            self.forecast_layout.addWidget(day_frame)

    def display_cached_weather(self):
        """Affiche les données en cache"""
        cached_data = load_from_cache()
        if cached_data:
            city = cached_data["city"]["name"]
            self.current_weather_data = cached_data
            self.display_forecast(cached_data, city)
            self.show_message("📡 Données en cache affichées (pas de connexion Internet)")
        else:
            self.show_message(self._tr("no_cache"))

    def clear_forecast(self):
        """Efface toutes les prévisions affichées"""
        for i in reversed(range(self.forecast_layout.count())):
            item = self.forecast_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

    def show_message(self, message):
        """Affiche un message dans la zone de prévisions"""
        self.clear_forecast()
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_color = "#718096" if not self.is_dark_theme else "#cbd5e0"
        bg_color = "rgba(255, 255, 255, 0.1)" if not self.is_dark_theme else "rgba(255, 255, 255, 0.05)"
        message_label.setStyleSheet(f"""
            color: {message_color}; 
            font-style: italic; 
            padding: 40px; 
            font-size: 16px;
            background: {bg_color};
            border-radius: 12px;
            margin: 20px;
        """)
        self.forecast_layout.addWidget(message_label)


if __name__ == "__main__":
    # Configuration doit être faite AVANT de créer QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style moderne par défaut
    
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec_())
