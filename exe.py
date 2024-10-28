import requests
import tkinter as tk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import json
import os
from PIL import Image, ImageTk
import time
import websocket
import threading
import psutil  
import platform

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

CRYPTOCURRENCIES = [
    {"id": "bitcoin", "symbol": "BTC"},
    {"id": "ethereum", "symbol": "ETH"},
    {"id": "solana", "symbol": "SOL"},
    {"id": "cardano", "symbol": "ADA"},
    {"id": "ripple", "symbol": "XRP"},
]

LANGUAGES = {
    "🇬🇧 English": "en",
    "🇹🇷 Türkçe": "tr",
    "🇫🇷 Français": "fr",
    "🇩🇪 Deutsch": "de",
    "🇪🇸 Español": "es",
    "🇷🇺 Русский": "ru",
}

CURRENCIES = {
    "USD": ["en", "es"],
    "TRY": ["tr"],
    "EUR": ["fr", "de"],
    "RUB": ["ru"],
}

API_KEYS_FILE = "api_keys.json"

class CryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Trading Dashboard")
        self.root.geometry("1600x900")  
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.selected_crypto = tk.StringVar(value=CRYPTOCURRENCIES[0]["id"])
        self.selected_crypto_symbol = tk.StringVar(value=CRYPTOCURRENCIES[0]["symbol"])
        self.investment_amount = tk.StringVar(value="1000.0")
        self.purchase_price = tk.StringVar(value="0.0")  
        self.stop_price = tk.StringVar(value="0.0")      
        self.crypto_data = {}
        self.price_history = []
        self.news_items = []
        self.comments_items = []
        self.news_source = ""
        self.comments_source = ""
        self.selected_language = tk.StringVar(value="🇬🇧 English")
        self.selected_currency = tk.StringVar(value="USD")  
        self.price = tk.DoubleVar(value=0.0)
        self.profit_status = tk.StringVar(value="")  
        self.api_keys = {}
        self.load_api_keys()
        self.build_gui()
        self.start_websocket()
        self.update_static_data()
        self.update_system_resources()

    def load_api_keys(self):
        if os.path.exists(API_KEYS_FILE):
            with open(API_KEYS_FILE, "r") as f:
                self.api_keys = json.load(f)
            if not self.api_keys.get('newsapi') or not self.api_keys.get('cryptocompare'):
                print("API keys are missing. Please run 'baslat.bat' and enter your API keys.")
                exit()
        else:
            print("API keys not found. Please run 'baslat.bat' and enter your API keys.")
            exit()

    def build_gui(self):
        top_frame = ctk.CTkFrame(self.root)
        top_frame.pack(pady=10, fill="x")
        controls_frame = ctk.CTkFrame(top_frame)
        controls_frame.pack(expand=True)
        self.language_label = ctk.CTkLabel(controls_frame, text="")
        self.language_label.grid(row=0, column=0, padx=5, pady=5)
        self.language_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=list(LANGUAGES.keys()),
            command=self.on_language_change,
            variable=self.selected_language
        )
        self.language_menu.grid(row=0, column=1, padx=5, pady=5)
        self.currency_label = ctk.CTkLabel(controls_frame, text="")
        self.currency_label.grid(row=0, column=2, padx=5, pady=5)
        self.currency_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=list(CURRENCIES.keys()),
            command=self.on_currency_change,
            variable=self.selected_currency
        )
        self.currency_menu.grid(row=0, column=3, padx=5, pady=5)
        self.crypto_label = ctk.CTkLabel(controls_frame, text="")
        self.crypto_label.grid(row=0, column=4, padx=5, pady=5)
        self.crypto_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=[c["symbol"] for c in CRYPTOCURRENCIES],
            command=self.on_crypto_change,
            variable=self.selected_crypto_symbol
        )
        self.crypto_menu.grid(row=0, column=5, padx=5, pady=5)
        self.investment_label = ctk.CTkLabel(controls_frame, text="")
        self.investment_label.grid(row=1, column=0, padx=5, pady=5)
        investment_entry = ctk.CTkEntry(controls_frame, textvariable=self.investment_amount)
        investment_entry.grid(row=1, column=1, padx=5, pady=5)
        self.purchase_label = ctk.CTkLabel(controls_frame, text="")
        self.purchase_label.grid(row=1, column=2, padx=5, pady=5)
        purchase_entry = ctk.CTkEntry(controls_frame, textvariable=self.purchase_price)
        purchase_entry.grid(row=1, column=3, padx=5, pady=5)
        self.stop_label = ctk.CTkLabel(controls_frame, text="")
        self.stop_label.grid(row=1, column=4, padx=5, pady=5)
        stop_entry = ctk.CTkEntry(controls_frame, textvariable=self.stop_price)
        stop_entry.grid(row=1, column=5, padx=5, pady=5)
        self.profit_status_label = ctk.CTkLabel(controls_frame, textvariable=self.profit_status, font=("Arial", 16))
        self.profit_status_label.grid(row=2, column=0, columnspan=6, padx=5, pady=5)
        for i in range(6):
            controls_frame.grid_columnconfigure(i, weight=1)
        system_frame = ctk.CTkFrame(self.root, fg_color="#1F1F1F")
        system_frame.pack(side="left", padx=10, pady=10, fill="y")
        self.cpu_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.cpu_label.pack(pady=(10, 2), padx=10, fill="x")
        self.cpu_progress = ctk.CTkProgressBar(system_frame, width=200)
        self.cpu_progress.pack(pady=2, padx=10, fill="x")
        self.ram_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.ram_label.pack(pady=(10, 2), padx=10, fill="x")
        self.ram_progress = ctk.CTkProgressBar(system_frame, width=200)
        self.ram_progress.pack(pady=2, padx=10, fill="x")
        self.disk_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.disk_label.pack(pady=(10, 2), padx=10, fill="x")
        self.disk_progress = ctk.CTkProgressBar(system_frame, width=200)
        self.disk_progress.pack(pady=2, padx=10, fill="x")
        self.cpu_freq_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.cpu_freq_label.pack(pady=(10, 2), padx=10, fill="x")
        self.net_sent_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.net_sent_label.pack(pady=(10, 2), padx=10, fill="x")
        self.net_received_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.net_received_label.pack(pady=(2, 10), padx=10, fill="x")
        self.battery_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.battery_label.pack(pady=(10, 2), padx=10, fill="x")
        self.platform_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.platform_label.pack(pady=(10, 2), padx=10, fill="x")
        self.cpu_temp_label = ctk.CTkLabel(system_frame, text="", anchor="w")
        self.cpu_temp_label.pack(pady=(10, 2), padx=10, fill="x")
        self.market_data_frame = ctk.CTkFrame(self.root)
        self.market_data_frame.pack(pady=10, fill="x", expand=True)
        self.price_label = ctk.CTkLabel(self.market_data_frame, text="", font=("Arial", 20))
        self.price_label.pack(pady=5)
        self.change_label = ctk.CTkLabel(self.market_data_frame, text="", font=("Arial", 16))
        self.change_label.pack(pady=5)
        self.market_cap_label = ctk.CTkLabel(self.market_data_frame, text="", font=("Arial", 16))
        self.market_cap_label.pack(pady=5)
        self.volume_label = ctk.CTkLabel(self.market_data_frame, text="", font=("Arial", 16))
        self.volume_label.pack(pady=5)
        self.profit_label = ctk.CTkLabel(self.market_data_frame, text="", font=("Arial", 20))
        self.profit_label.pack(pady=5)
        self.chart_frame = ctk.CTkFrame(self.root)
        self.chart_frame.pack(pady=10, fill="both", expand=True)
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.figure.patch.set_facecolor('#2B2B2B')
        self.ax.set_facecolor('#2B2B2B')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.news_frame = ctk.CTkFrame(self.root)
        self.news_frame.pack(pady=10, fill="x")
        self.news_label = ctk.CTkLabel(self.news_frame, text="", font=("Arial", 18))
        self.news_label.pack(pady=5)
        self.news_source_label = ctk.CTkLabel(self.news_frame, text="", font=("Arial", 12))
        self.news_source_label.pack(pady=5)
        self.news_listbox = tk.Listbox(self.news_frame, height=6, bg='#2B2B2B', fg='white', selectbackground='#1E1E1E')
        self.news_listbox.pack(fill="both", padx=10, pady=5)
        self.comments_frame = ctk.CTkFrame(self.root)
        self.comments_frame.pack(pady=10, fill="x")
        self.comments_label = ctk.CTkLabel(self.comments_frame, text="", font=("Arial", 18))
        self.comments_label.pack(pady=5)
        self.comments_source_label = ctk.CTkLabel(self.comments_frame, text="", font=("Arial", 12))
        self.comments_source_label.pack(pady=5)
        self.comments_listbox = tk.Listbox(
            self.comments_frame, height=6, bg='#2B2B2B', fg='white', selectbackground='#1E1E1E'
        )
        self.comments_listbox.pack(fill="both", padx=10, pady=5)

        self.update_interface_language()

    def get_float_value(self, var):
        value = var.get()
        if isinstance(value, str):
            value = value.replace(',', '.')
        try:
            return float(value)
        except ValueError:
            return 0.0

    def on_language_change(self, value):
        self.selected_language.set(value)
        self.update_interface_language()
        self.set_default_currency()
        self.update_static_data()

    def set_default_currency(self):
        lang_code = LANGUAGES[self.selected_language.get()]
        for currency, languages in CURRENCIES.items():
            if lang_code in languages:
                self.selected_currency.set(currency)
                break
        else:
            self.selected_currency.set("USD")

    def on_currency_change(self, value):
        self.selected_currency.set(value)
        self.update_static_data()

    def update_interface_language(self):
        lang_code = LANGUAGES[self.selected_language.get()]
        translations = {
            'title': {
                'en': "Crypto Trading Dashboard",
                'tr': "Kripto Ticaret Panosu",
                'fr': "Tableau de Trading Crypto",
                'de': "Krypto-Handelsübersicht",
                'es': "Panel de Comercio Cripto",
                'ru': "Панель Торговли Криптовалютой",
            },
            'language': {
                'en': "Language:",
                'tr': "Dil Seçimi:",
                'fr': "Langue:",
                'de': "Sprache:",
                'es': "Idioma:",
                'ru': "Язык:",
            },
            'currency': {
                'en': "Currency:",
                'tr': "Para Birimi:",
                'fr': "Devise:",
                'de': "Währung:",
                'es': "Moneda:",
                'ru': "Валюта:",
            },
            'cryptocurrency': {
                'en': "Cryptocurrency:",
                'tr': "Kripto Para Birimi:",
                'fr': "Cryptomonnaie:",
                'de': "Kryptowährung:",
                'es': "Criptomoneda:",
                'ru': "Криптовалюта:",
            },
            'investment': {
                'en': "Investment Amount ({currency}):",
                'tr': "Yatırım Tutarı ({currency}):",
                'fr': "Montant de l'Investissement ({currency}):",
                'de': "Investitionsbetrag ({currency}):",
                'es': "Cantidad de Inversión ({currency}):",
                'ru': "Сумма Инвестиций ({currency}):",
            },
            'purchase_price': {
                'en': "Purchase Price ({currency}):",
                'tr': "Satın Alma Fiyatı ({currency}):",
                'fr': "Prix d'Achat ({currency}):",
                'de': "Kaufpreis ({currency}):",
                'es': "Precio de Compra ({currency}):",
                'ru': "Цена Покупки ({currency}):",
            },
            'stop_price': {
                'en': "Stop-Loss Price ({currency}):",
                'tr': "Stop-Loss Fiyatı ({currency}):",
                'fr': "Prix Stop-Loss ({currency}):",
                'de': "Stop-Loss Preis ({currency}):",
                'es': "Precio Stop-Loss ({currency}):",
                'ru': "Цена Stop-Loss ({currency}):",
            },
            'profit_status': {
                'en': "Profit/Loss:",
                'tr': "Kâr/Zarar:",
                'fr': "Profit/Perte:",
                'de': "Gewinn/Verlust:",
                'es': "Ganancia/Pérdida:",
                'ru': "Прибыль/Убыток:",
            },
            'price_loading': {
                'en': "Price Loading...",
                'tr': "Fiyat Yükleniyor...",
                'fr': "Chargement du Prix...",
                'de': "Preis wird geladen...",
                'es': "Cargando Precio...",
                'ru': "Цена загружается...",
            },
            'change_loading': {
                'en': "24h Change Loading...",
                'tr': "24s Değişim Yükleniyor...",
                'fr': "Changement sur 24h en cours...",
                'de': "24h Änderung wird geladen...",
                'es': "Cambiando en 24h...",
                'ru': "Изменение за 24ч загружается...",
            },
            'market_cap_loading': {
                'en': "Market Cap Loading...",
                'tr': "Piyasa Değeri Yükleniyor...",
                'fr': "Capitalisation Boursière en cours...",
                'de': "Marktkapitalisierung wird geladen...",
                'es': "Cargando Capitalización de Mercado...",
                'ru': "Рыночная капитализация загружается...",
            },
            'volume_loading': {
                'en': "24h Volume Loading...",
                'tr': "24s Hacim Yükleniyor...",
                'fr': "Volume sur 24h en cours...",
                'de': "24h Volumen wird geladen...",
                'es': "Cargando Volumen de 24h...",
                'ru': "Объем за 24ч загружается...",
            },
            'profit_loading': {
                'en': "Profit/Loss Loading...",
                'tr': "Kâr/Zarar Yükleniyor...",
                'fr': "Chargement du Profit/Perte...",
                'de': "Gewinn/Verlust wird geladen...",
                'es': "Cargando Ganancia/Pérdida...",
                'ru': "Прибыль/Убыток загружается...",
            },
            'latest_news': {
                'en': "Latest News",
                'tr': "Son Haberler",
                'fr': "Dernières Nouvelles",
                'de': "Neueste Nachrichten",
                'es': "Últimas Noticias",
                'ru': "Последние Новости",
            },
            'no_news': {
                'en': "No news available.",
                'tr': "Haber bulunamadı.",
                'fr': "Pas de nouvelles disponibles.",
                'de': "Keine Nachrichten verfügbar.",
                'es': "No hay noticias disponibles.",
                'ru': "Новости недоступны.",
            },
            'news_source': {
                'en': "News Source: {source}",
                'tr': "Haber Kaynağı: {source}",
                'fr': "Source des Nouvelles: {source}",
                'de': "Nachrichtenquelle: {source}",
                'es': "Fuente de Noticias: {source}",
                'ru': "Источник новостей: {source}",
            },
            'professional_comments': {
                'en': "Professional Comments",
                'tr': "Profesyonel Yorumlar",
                'fr': "Commentaires Professionnels",
                'de': "Professionelle Kommentare",
                'es': "Comentarios Profesionales",
                'ru': "Профессиональные Комментарии",
            },
            'no_comments': {
                'en': "No comments available.",
                'tr': "Yorum bulunamadı.",
                'fr': "Pas de commentaires disponibles.",
                'de': "Keine Kommentare verfügbar.",
                'es': "No hay comentarios disponibles.",
                'ru': "Комментарии недоступны.",
            },
            'comments_source': {
                'en': "Comments Source: {source}",
                'tr': "Yorum Kaynağı: {source}",
                'fr': "Source des Commentaires: {source}",
                'de': "Kommentarquelle: {source}",
                'es': "Fuente de Comentarios: {source}",
                'ru': "Источник комментариев: {source}",
            },
            'cpu_usage': {
                'en': "CPU Usage:",
                'tr': "CPU Kullanımı:",
                'fr': "Utilisation du CPU:",
                'de': "CPU-Auslastung:",
                'es': "Uso de CPU:",
                'ru': "Использование CPU:",
            },
            'ram_usage': {
                'en': "RAM Usage:",
                'tr': "RAM Kullanımı:",
                'fr': "Utilisation de la RAM:",
                'de': "RAM-Auslastung:",
                'es': "Uso de RAM:",
                'ru': "Использование RAM:",
            },
            'disk_usage': {
                'en': "Disk Usage:",
                'tr': "Disk Kullanımı:",
                'fr': "Utilisation du Disque:",
                'de': "Festplattennutzung:",
                'es': "Uso del Disco:",
                'ru': "Использование Диска:",
            },
            'platform_info': {
                'en': "Platform:",
                'tr': "Platform:",
                'fr': "Plateforme:",
                'de': "Plattform:",
                'es': "Plataforma:",
                'ru': "Платформа:",
            },
            'cpu_freq': {
                'en': "CPU Frequency:",
                'tr': "CPU Frekansı:",
                'fr': "Fréquence du CPU:",
                'de': "CPU-Frequenz:",
                'es': "Frecuencia de CPU:",
                'ru': "Частота CPU:",
            },
            'network_usage': {
                'en': "Network Usage:",
                'tr': "Ağ Kullanımı:",
                'fr': "Utilisation du Réseau:",
                'de': "Netzwerknutzung:",
                'es': "Uso de Red:",
                'ru': "Использование Сети:",
            },
            'battery_status': {
                'en': "Battery Status:",
                'tr': "Batarya Durumu:",
                'fr': "État de la Batterie:",
                'de': "Batteriestatus:",
                'es': "Estado de la Batería:",
                'ru': "Состояние Батареи:",
            },
            'cpu_temp': {
                'en': "CPU Temperature:",
                'tr': "CPU Sıcaklığı:",
                'fr': "Température du CPU:",
                'de': "CPU-Temperatur:",
                'es': "Temperatura de CPU:",
                'ru': "Температура CPU:",
            },
            'chart_title': {
                'en': "{name} Price Chart",
                'tr': "{name} Fiyat Grafiği",
                'fr': "Graphique du Prix de {name}",
                'de': "{name} Preisdiagramm",
                'es': "Gráfico de Precio de {name}",
                'ru': "График Цены {name}",
            },
            'date': {
                'en': "Date",
                'tr': "Tarih",
                'fr': "Date",
                'de': "Datum",
                'es': "Fecha",
                'ru': "Дата",
            },
            'price_currency': {
                'en': "Price ({currency})",
                'tr': "Fiyat ({currency})",
                'fr': "Prix ({currency})",
                'de': "Preis ({currency})",
                'es': "Precio ({currency})",
                'ru': "Цена ({currency})",
            },
        }
        self.root.title(translations['title'][lang_code].format(name=self.crypto_data.get('name', 'Crypto')))
        self.language_label.configure(text=translations['language'][lang_code])
        self.currency_label.configure(text=translations['currency'][lang_code])
        self.crypto_label.configure(text=translations['cryptocurrency'][lang_code])
        currency = self.selected_currency.get()
        self.investment_label.configure(text=translations['investment'][lang_code].format(currency=currency))
        self.purchase_label.configure(text=translations['purchase_price'][lang_code].format(currency=currency))
        self.stop_label.configure(text=translations['stop_price'][lang_code].format(currency=currency))
        self.profit_status_label.configure(text=translations['profit_status'][lang_code])
        self.price_label.configure(text=translations['price_loading'][lang_code])
        self.change_label.configure(text=translations['change_loading'][lang_code])
        self.market_cap_label.configure(text=translations['market_cap_loading'][lang_code])
        self.volume_label.configure(text=translations['volume_loading'][lang_code])
        self.profit_label.configure(text=translations['profit_loading'][lang_code])
        self.news_label.configure(text=translations['latest_news'][lang_code])
        self.comments_label.configure(text=translations['professional_comments'][lang_code])
        self.cpu_label.configure(text=translations['cpu_usage'][lang_code])
        self.ram_label.configure(text=translations['ram_usage'][lang_code])
        self.disk_label.configure(text=translations['disk_usage'][lang_code])
        self.cpu_freq_label.configure(text=translations['cpu_freq'][lang_code])
        self.net_sent_label.configure(text=f"{translations['network_usage'][lang_code]} Sent: ")
        self.net_received_label.configure(text=f"{translations['network_usage'][lang_code]} Received: ")
        self.battery_label.configure(text=translations['battery_status'][lang_code])
        self.cpu_temp_label.configure(text=translations['cpu_temp'][lang_code])
        self.platform_label.configure(text=f"{translations['platform_info'][lang_code]} {platform.system()} {platform.release()}")
        if self.crypto_data.get('name'):
            self.ax.set_title(translations['chart_title'][lang_code].format(name=self.crypto_data.get('name', 'Crypto')), color='white')
            self.ax.set_xlabel(translations['date'][lang_code], color='white')
            self.ax.set_ylabel(translations['price_currency'][lang_code].format(currency=self.selected_currency.get()), color='white')
            self.canvas.draw()
    def on_crypto_change(self, value):
        for crypto in CRYPTOCURRENCIES:
            if crypto["symbol"] == value:
                self.selected_crypto.set(crypto["id"])
                self.selected_crypto_symbol.set(crypto["symbol"])
                break
        self.crypto_data = {}
        self.price_history = []
        self.news_items = []
        self.comments_items = []
        self.stop_websocket()
        self.start_websocket()
        self.update_static_data()
    def start_websocket(self):
        crypto_symbol = self.selected_crypto_symbol.get().lower() + 'usdt'
        websocket_url = f"wss://stream.binance.com:9443/ws/{crypto_symbol}@trade"
        self.ws = websocket.WebSocketApp(websocket_url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
    def stop_websocket(self):
        if hasattr(self, 'ws'):
            self.ws.close()
    def on_message(self, ws, message):
        data = json.loads(message)
        price = float(data['p'])
        self.price.set(price)
        self.root.after(0, self.update_market_data)
    def on_error(self, ws, error):
        print(f"WebSocket Error: {error}")
    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket Connection Closed")
    def fetch_price_history(self, crypto_id):
        url = f"{COINGECKO_API_URL}/coins/{crypto_id}/market_chart"
        params = {
            "vs_currency": self.selected_currency.get().lower(),
            "days": "30",
            "interval": "daily",
        }
        data = self.make_request(url, params, "price history")
        return data.get("prices", []) if data else []

    def fetch_static_data_threaded(self, crypto_id, crypto_symbol):
        crypto_data = self.fetch_crypto_data(crypto_id)
        price_history = self.fetch_price_history(crypto_id)
        if crypto_data and price_history:
            self.root.after(0, self.update_crypto_data, crypto_data, price_history)
        news_items = self.fetch_news(crypto_id)
        comments_items = self.fetch_professional_comments(crypto_symbol)
        self.root.after(0, self.update_news_comments, news_items, comments_items)

    def update_crypto_data(self, crypto_data, price_history):
        self.crypto_data = crypto_data
        self.price_history = price_history
        self.update_chart()

    def update_news_comments(self, news_items, comments_items):
        self.news_items = news_items
        self.comments_items = comments_items
        self.update_news()
        self.update_comments()

    def update_static_data(self):
        crypto_id = self.selected_crypto.get()
        crypto_symbol = self.selected_crypto_symbol.get()
        threading.Thread(target=self.fetch_static_data_threaded, args=(crypto_id, crypto_symbol)).start()
        self.root.after(1800000, self.update_static_data)  

    def fetch_crypto_data(self, crypto_id):
        url = f"{COINGECKO_API_URL}/coins/markets"
        params = {
            "vs_currency": self.selected_currency.get().lower(),
            "ids": crypto_id,
            "order": "market_cap_desc",
            "sparkline": False,
            "price_change_percentage": "1h,24h,7d",
        }
        data = self.make_request(url, params, "crypto data")
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        else:
            return None

    def fetch_news(self, crypto_id):
        lang_code = LANGUAGES[self.selected_language.get()]
        news_api_key = self.api_keys.get('newsapi')
        if not news_api_key:
            print("NewsAPI.org API key not found.")
            return []

        url = f"https://newsapi.org/v2/everything"
        params = {
            "q": crypto_id,
            "language": lang_code,
            "apiKey": news_api_key,
        }
        data = self.make_request(url, params, "news")
        if data and "articles" in data:
            self.news_source = "NewsAPI.org"
            return [article["title"] for article in data["articles"]]
        else:
            return []

    def fetch_professional_comments(self, crypto_symbol):
        api_key = self.api_keys.get('cryptocompare')
        if not api_key:
            print("CryptoCompare API key not found.")
            return []

        url = f"https://min-api.cryptocompare.com/data/v2/news/"
        params = {
            "categories": crypto_symbol,
            "lang": LANGUAGES[self.selected_language.get()],
            "api_key": api_key,
        }
        data = self.make_request(url, params, "professional comments")
        if data and "Data" in data:
            self.comments_source = "CryptoCompare"
            return [article["title"] for article in data.get("Data", [])]
        else:
            return []

    def make_request(self, url, params, data_type):
        max_retries = 3
        wait_time = 5
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                if response.status_code == 429:
                    print(f"Rate limit reached for {data_type}. Waiting...")
                    time.sleep(wait_time)
                    wait_time *= 2
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                print(f"Error fetching {data_type}: {e}")
                return None
            except Exception as e:
                print(f"Error fetching {data_type}: {e}")
                return None
        print(f"Failed to fetch {data_type}. Please try again later.")
        return None

    def update_market_data(self):
        price = self.price.get()
        if not self.crypto_data:
            return

        price_change_24h = self.crypto_data.get("price_change_percentage_24h", 0)
        market_cap = self.crypto_data.get("market_cap", 0)
        volume = self.crypto_data.get("total_volume", 0)

        currency = self.selected_currency.get()
        lang_code = LANGUAGES[self.selected_language.get()]
        translations = {
            'price': {
                'en': f"Price: {currency} {price:,.2f}",
                'tr': f"Fiyat: {price:,.2f} {currency}",
                'fr': f"Prix: {price:,.2f} {currency}",
                'de': f"Preis: {price:,.2f} {currency}",
                'es': f"Precio: {price:,.2f} {currency}",
                'ru': f"Цена: {price:,.2f} {currency}",
            },
            'change': {
                'en': f"24h Change: {price_change_24h:+.2f}%",
                'tr': f"24s Değişim: {price_change_24h:+.2f}%",
                'fr': f"Changement 24h: {price_change_24h:+.2f}%",
                'de': f"24h Änderung: {price_change_24h:+.2f}%",
                'es': f"Cambio 24h: {price_change_24h:+.2f}%",
                'ru': f"Изменение за 24ч: {price_change_24h:+.2f}%",
            },
            'market_cap': {
                'en': f"Market Cap: {currency} {market_cap:,.0f}",
                'tr': f"Piyasa Değeri: {market_cap:,.0f} {currency}",
                'fr': f"Capitalisation Boursière: {market_cap:,.0f} {currency}",
                'de': f"Marktkapitalisierung: {market_cap:,.0f} {currency}",
                'es': f"Capitalización de Mercado: {market_cap:,.0f} {currency}",
                'ru': f"Рыночная Капитализация: {market_cap:,.0f} {currency}",
            },
            'volume': {
                'en': f"24h Volume: {currency} {volume:,.0f}",
                'tr': f"24s Hacim: {volume:,.0f} {currency}",
                'fr': f"Volume 24h: {volume:,.0f} {currency}",
                'de': f"24h Volumen: {volume:,.0f} {currency}",
                'es': f"Volumen 24h: {volume:,.0f} {currency}",
                'ru': f"Объем за 24ч: {volume:,.0f} {currency}",
            },
            'profit_loss': {
                'en': f"Profit/Loss: {currency} {self.calculate_profit(price):+.2f}",
                'tr': f"Kâr/Zarar: {self.calculate_profit(price):+.2f} {currency}",
                'fr': f"Profit/Perte: {self.calculate_profit(price):+.2f} {currency}",
                'de': f"Gewinn/Verlust: {self.calculate_profit(price):+.2f} {currency}",
                'es': f"Ganancia/Pérdida: {self.calculate_profit(price):+.2f} {currency}",
                'ru': f"Прибыль/Убыток: {self.calculate_profit(price):+.2f} {currency}",
            },
        }

        self.price_label.configure(text=translations['price'][lang_code])
        self.change_label.configure(text=translations['change'][lang_code])
        self.market_cap_label.configure(text=translations['market_cap'][lang_code])
        self.volume_label.configure(text=translations['volume'][lang_code])
        self.profit_label.configure(text=translations['profit_loss'][lang_code])
        self.update_profit_status(price)

    def calculate_profit(self, current_price):
        investment = self.get_float_value(self.investment_amount)
        purchase_price = self.get_float_value(self.purchase_price)
        if purchase_price == 0:
            return 0
        crypto_amount = investment / purchase_price
        current_value = crypto_amount * current_price
        profit = current_value - investment
        return profit

    def update_profit_status(self, current_price):
        purchase_price = self.get_float_value(self.purchase_price)
        stop_price = self.get_float_value(self.stop_price)
        lang_code = LANGUAGES[self.selected_language.get()]
        translations = {
            'profit': {
                'en': "Profit",
                'tr': "Kâr",
                'fr': "Profit",
                'de': "Gewinn",
                'es': "Ganancia",
                'ru': "Прибыль",
            },
            'loss': {
                'en': "Loss",
                'tr': "Zarar",
                'fr': "Perte",
                'de': "Verlust",
                'es': "Pérdida",
                'ru': "Убыток",
            },
            'stop_loss_triggered': {
                'en': "Stop-Loss Triggered",
                'tr': "Stop-Loss Tetiklendi",
                'fr': "Stop-Loss Déclenché",
                'de': "Stop-Loss Ausgelöst",
                'es': "Stop-Loss Activado",
                'ru': "Стоп-лосс Сработал",
            },
        }

        if purchase_price == 0:
            status = ""
            color = "white"
        else:
            if current_price >= purchase_price:
                status = translations['profit'][lang_code]
                color = "green"
            elif current_price <= stop_price and stop_price > 0:
                status = translations['stop_loss_triggered'][lang_code]
                color = "red"
            else:
                status = translations['loss'][lang_code]
                color = "red"

        self.profit_status.set(status)
        self.profit_status_label.configure(text=status, text_color=color)

    def update_chart(self):
        if not self.price_history:
            return

        dates = [datetime.datetime.fromtimestamp(d[0]/1000) for d in self.price_history]
        prices = [d[1] for d in self.price_history]

        self.ax.clear()
        self.ax.plot(dates, prices, label='Price', color='cyan')

        lang_code = LANGUAGES[self.selected_language.get()]
        currency = self.selected_currency.get()
        translations = {
            'chart_title': {
                'en': "{name} Price Chart",
                'tr': "{name} Fiyat Grafiği",
                'fr': "Graphique du Prix de {name}",
                'de': "{name} Preisdiagramm",
                'es': "Gráfico de Precio de {name}",
                'ru': "График Цены {name}",
            },
            'date': {
                'en': "Date",
                'tr': "Tarih",
                'fr': "Date",
                'de': "Datum",
                'es': "Fecha",
                'ru': "Дата",
            },
            'price_currency': {
                'en': "Price ({currency})",
                'tr': "Fiyat ({currency})",
                'fr': "Prix ({currency})",
                'de': "Preis ({currency})",
                'es': "Precio ({currency})",
                'ru': "Цена ({currency})",
            },
        }

        self.ax.set_title(translations['chart_title'][lang_code].format(name=self.crypto_data.get('name', 'Crypto')), color='white')
        self.ax.set_xlabel(translations['date'][lang_code], color='white')
        self.ax.set_ylabel(translations['price_currency'][lang_code].format(currency=currency), color='white')

        self.ax.legend()
        self.ax.grid(True, linestyle='--', alpha=0.5)

        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')

        self.figure.autofmt_xdate()
        self.canvas.draw()

    def update_news(self):
        self.news_listbox.delete(0, tk.END)
        lang_code = LANGUAGES[self.selected_language.get()]
        translations = {
            'no_news': {
                'en': "No news available.",
                'tr': "Haber bulunamadı.",
                'fr': "Pas de nouvelles disponibles.",
                'de': "Keine Nachrichten verfügbar.",
                'es': "No hay noticias disponibles.",
                'ru': "Новости недоступны.",
            },
            'news_source': {
                'en': "News Source: {source}",
                'tr': "Haber Kaynağı: {source}",
                'fr': "Source des Nouvelles: {source}",
                'de': "Nachrichtenquelle: {source}",
                'es': "Fuente de Noticias: {source}",
                'ru': "Источник новостей: {source}",
            },
        }

        if self.news_items:
            for news in self.news_items[:5]:
                self.news_listbox.insert(tk.END, news)
        else:
            self.news_listbox.insert(tk.END, translations['no_news'][lang_code])

        if self.news_source:
            self.news_source_label.configure(text=translations['news_source'][lang_code].format(source=self.news_source))
        else:
            self.news_source_label.configure(text="")

    def update_comments(self):
        self.comments_listbox.delete(0, tk.END)
        lang_code = LANGUAGES[self.selected_language.get()]
        translations = {
            'no_comments': {
                'en': "No comments available.",
                'tr': "Yorum bulunamadı.",
                'fr': "Pas de commentaires disponibles.",
                'de': "Keine Kommentare verfügbar.",
                'es': "No hay comentarios disponibles.",
                'ru': "Комментарии недоступны.",
            },
            'comments_source': {
                'en': "Comments Source: {source}",
                'tr': "Yorum Kaynağı: {source}",
                'fr': "Source des Commentaires: {source}",
                'de': "Kommentarquelle: {source}",
                'es': "Fuente de Comentarios: {source}",
                'ru': "Источник комментариев: {source}",
            },
        }

        if self.comments_items:
            for comment in self.comments_items[:5]:
                self.comments_listbox.insert(tk.END, comment)
        else:
            self.comments_listbox.insert(tk.END, translations['no_comments'][lang_code])

        if self.comments_source:
            self.comments_source_label.configure(
                text=translations['comments_source'][lang_code].format(source=self.comments_source)
            )
        else:
            self.comments_source_label.configure(text="")

    def update_system_resources(self):
        lang_code = LANGUAGES[self.selected_language.get()]
        translations = {
            'cpu_usage': {
                'en': "CPU Usage:",
                'tr': "CPU Kullanımı:",
                'fr': "Utilisation du CPU:",
                'de': "CPU-Auslastung:",
                'es': "Uso de CPU:",
                'ru': "Использование CPU:",
            },
            'ram_usage': {
                'en': "RAM Usage:",
                'tr': "RAM Kullanımı:",
                'fr': "Utilisation de la RAM:",
                'de': "RAM-Auslastung:",
                'es': "Uso de RAM:",
                'ru': "Использование RAM:",
            },
            'disk_usage': {
                'en': "Disk Usage:",
                'tr': "Disk Kullanımı:",
                'fr': "Utilisation du Disque:",
                'de': "Festplattennutzung:",
                'es': "Uso del Disco:",
                'ru': "Использование Диска:",
            },
            'platform_info': {
                'en': "Platform:",
                'tr': "Platform:",
                'fr': "Plateforme:",
                'de': "Plattform:",
                'es': "Plataforma:",
                'ru': "Платформа:",
            },
            'cpu_freq': {
                'en': "CPU Frequency:",
                'tr': "CPU Frekansı:",
                'fr': "Fréquence du CPU:",
                'de': "CPU-Frequenz:",
                'es': "Frecuencia de CPU:",
                'ru': "Частота CPU:",
            },
            'network_usage': {
                'en': "Network Usage:",
                'tr': "Ağ Kullanımı:",
                'fr': "Utilisation du Réseau:",
                'de': "Netzwerknutzung:",
                'es': "Uso de Red:",
                'ru': "Использование Сети:",
            },
            'battery_status': {
                'en': "Battery Status:",
                'tr': "Batarya Durumu:",
                'fr': "État de la Batterie:",
                'de': "Batteriestatus:",
                'es': "Estado de la Batería:",
                'ru': "Состояние Батареи:",
            },
            'cpu_temp': {
                'en': "CPU Temperature:",
                'tr': "CPU Sıcaklığı:",
                'fr': "Température du CPU:",
                'de': "CPU-Temperatur:",
                'es': "Temperatura de CPU:",
                'ru': "Температура CPU:",
            },
        }

        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_progress.set(cpu_percent / 100)
        self.cpu_label.configure(text=f"{translations['cpu_usage'][lang_code]} {cpu_percent}%")

        ram_percent = psutil.virtual_memory().percent
        self.ram_progress.set(ram_percent / 100)
        self.ram_label.configure(text=f"{translations['ram_usage'][lang_code]} {ram_percent}%")

        disk_percent = psutil.disk_usage('/').percent
        self.disk_progress.set(disk_percent / 100)
        self.disk_label.configure(text=f"{translations['disk_usage'][lang_code]} {disk_percent}%")

        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            current_freq = cpu_freq.current
            max_freq = cpu_freq.max
            self.cpu_freq_label.configure(text=f"{translations['cpu_freq'][lang_code]} {current_freq:.2f} MHz (Max: {max_freq:.2f} MHz)")
        else:
            self.cpu_freq_label.configure(text=f"{translations['cpu_freq'][lang_code]} N/A")

        net_io = psutil.net_io_counters()
        sent_mb = net_io.bytes_sent / (1024 * 1024)
        recv_mb = net_io.bytes_recv / (1024 * 1024)
        self.net_sent_label.configure(text=f"{translations['network_usage'][lang_code]} Sent: {sent_mb:.2f} MB")
        self.net_received_label.configure(text=f"{translations['network_usage'][lang_code]} Received: {recv_mb:.2f} MB")

        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = battery.power_plugged
                status = "Plugged In" if plugged else "On Battery"
                if lang_code == 'tr':
                    status = "Şarjda" if plugged else "Pil Üzerinde"
                elif lang_code == 'fr':
                    status = "Branché" if plugged else "Sur Batterie"
                elif lang_code == 'de':
                    status = "Eingesteckt" if plugged else "Am Akku"
                elif lang_code == 'es':
                    status = "Conectado" if plugged else "En Batería"
                elif lang_code == 'ru':
                    status = "В сети" if plugged else "От батареи"
                self.battery_label.configure(text=f"{translations['battery_status'][lang_code]} {percent}% ({status})")
            else:
                self.battery_label.configure(text=f"{translations['battery_status'][lang_code]} N/A")
        else:
            self.battery_label.configure(text=f"{translations['battery_status'][lang_code]} N/A")
        temps = {}
        try:
            temps = psutil.sensors_temperatures()
        except AttributeError:
            pass  
        if temps:
            cpu_temps = temps.get('coretemp') or temps.get('cpu-thermal') or []
            if cpu_temps:
                temp_values = [t.current for t in cpu_temps if t.current is not None]
                if temp_values:
                    avg_temp = sum(temp_values) / len(temp_values)
                    self.cpu_temp_label.configure(text=f"{translations['cpu_temp'][lang_code]} {avg_temp:.1f}°C")
                else:
                    self.cpu_temp_label.configure(text=f"{translations['cpu_temp'][lang_code]} N/A")
            else:
                self.cpu_temp_label.configure(text=f"{translations['cpu_temp'][lang_code]} N/A")
        else:
            self.cpu_temp_label.configure(text=f"{translations['cpu_temp'][lang_code]} N/A")

        self.root.after(2000, self.update_system_resources)  

def main():
    root = ctk.CTk()
    app = CryptoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
