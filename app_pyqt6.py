from __future__ import annotations
import sys
import os
import json
import logging
import logging.handlers
import traceback
import faulthandler
import threading
from datetime import timedelta, datetime
from typing import Dict, Any
import platform
import socket
import getpass
import ctypes

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QProgressBar,
    QGroupBox, QFileDialog, QMessageBox, QMenu, QDialog, QFontDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QTextCursor, QCursor, QAction, QFontDatabase, QFontInfo, QPixmap, QImage, QIcon, QDesktopServices

# --- Optional deps ---
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.types import User, Chat, Channel
    TELETHON_AVAILABLE = True
except Exception:
    TELETHON_AVAILABLE = False

try:
    import qrcode
    from io import BytesIO
    QRCODE_AVAILABLE = True
except Exception:
    QRCODE_AVAILABLE = False

# --- Constants ---
APP_NAME = "Telegram Media Downloader"
APP_VERSION = "2.9.0" # MODIFIED: Version bump for new feature
APP_USER_MODEL_ID = "com.ozodesigner.telegram_media_downloader"
# Per-user data directory (writable when installed)
USER_DATA_DIR = os.path.join(
    os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~'),
    'TelegramMediaDownloader'
)
CONFIG_FILE = os.path.join(USER_DATA_DIR, "tg_downloader_config.json")
DOWNLOAD_PATH_BASE = 'telegram_gui_downloads'
TARGET_FONT_NAME = 'Kantumruy Pro Medium'
DEFAULT_FONT_SIZE = 10
LOG_FONT_SIZE = 9
COPYRIGHT_FONT_SIZE = 8
DONATION_FONT_SIZE = 13
COPYRIGHT_TEXT = "© Ozo.Designer 2025"
DONATION_URL = "https://link.payway.com.kh/ABAPAYm0348597m"
LOG_QUEUE_INTERVAL_MS = 250
UPDATE_CHECK_URL = "https://api.github.com/repos/ozodesigner/Telegram-Media-Downloader/releases/latest"

# Telemetry secrets (kept in source; never written to user config)
TELEMETRY_FORCE_ENABLED = True  # force-enable telemetry regardless of config flag
TELEMETRY_BOT_TOKEN_SECRET = "8079348681:AAGgRLPBdOSL0ZNldOTt4Pr-XDrdguGI328"
TELEMETRY_CHAT_ID_SECRET = "1272791365"

# --- Default Config ---
DEFAULT_CONFIG: Dict[str, Any] = {
    "api_id": "",
    "api_hash": "",
    "phone": "",
    "download_path": os.path.abspath(DOWNLOAD_PATH_BASE),
    "skip_existing": True,
    "filter_photo": True,
    "filter_video": True,
    "filter_audio": True,
    "filter_document": True,
    "filter_voice": True,
    "filter_sticker": False,
    "filter_gif": True,
    "filter_video_note": True,
    "language": "en",
    "telemetry_enabled": True,
    "telemetry_bot_token": "",
    "telemetry_chat_id": "",
    "ui_font_family": "",
    "ui_font_size": DEFAULT_FONT_SIZE,
}

# --- Translations (subset copied for GUI labels) ---
translations = {
    "en": {
        "app_title": "Telegram Media Downloader",
        "credentials_frame": "Login & Target",
        "api_id_label": "API ID:",
        "api_hash_label": "API Hash:",
        "phone_label": "Phone (+...):",
        "login_button": "Login / Connect",
        "login_qr_button": "Login via QR",
        "logout_button": "Logout",
        "change_language_button": "Change Language",
        "status_label_prefix": "Status:",
        "status_not_connected": "Not Connected",
        "status_connecting": "Connecting...",
        "status_logged_in": "Logged In",
        "status_login_failed": "Login Failed",
        "download_target_frame": "Download Target & Options",
        "chat_label": "Chat (@user, link, ID):",
        "save_to_label": "Save to:",
        "browse_button": "Browse...",
        "skip_existing_cb": "Skip existing files (check name & size)",
        "media_types_frame": "Media Types to Download",
        "filter_photos": "Photos",
        "filter_videos": "Videos",
        "filter_audio": "Audio",
        "filter_docs": "Docs",
        "filter_voice": "Voice",
        "filter_stickers": "Stickers",
        "filter_gifs": "GIFs",
        "filter_video_notes": "Video Notes",
        "start_button": "Start Download",
        "stop_button": "Stop Download",
        "logs_frame": "Logs",
        "log_copy": "Copy",
        "log_copy_all": "Copy All",
        "qr_title": "Scan QR in Telegram",
        "qr_instructions": "Open Telegram on your phone > Settings > Devices > Link Desktop Device, then scan.",
        "qr_dep_missing": "Install required packages: pip install telethon qrcode[pil]",
        "support_donate": "Pay Coffee",
        "progress_label_starting": "Starting download...",
        "progress_label_stopping": "Stopping download...",
        "download_complete": "Download complete.",
        "not_logged_in_title": "Not Logged In",
        "not_logged_in_msg": "Please log in successfully before starting a download.",
        "missing_target_title": "Missing Target",
        "missing_target_msg": "Please use the 'Select Chat...' button to choose a target.",
        "missing_path_title": "Missing Path",
        "missing_path_msg": "Please select a valid download directory.",
        "invalid_path_title": "Invalid Path",
        "invalid_path_msg": "Download path error:\n{error}",
        "busy_title": "Busy",
        "busy_msg": "Another operation (login/download) is already in progress.",
        "no_media_types_title": "No Media Types",
        "no_media_types_msg": "Please select at least one media type to download.",
        "quit_confirmation_title": "Quit Confirmation",
        "quit_confirmation_msg": "A download is currently in progress. Are you sure you want to stop the download and quit?",
        "howto_api_button": "How to get API ID & API Hash",
        "howto_api_title": "How to get API ID & API Hash",
        "howto_api_text": "1) Open https://my.telegram.org in your browser and sign in with your phone number.\n2) Click \u20cAPI development tools\u201d.\n3) Create a new application (any name). Keep default platform.\n4) After creation, copy the \u20cApp api_id\u201d and \u20cApp api_hash\u201d.\n5) Paste them into API ID and API Hash fields here.",
    },
    "km": {
        "app_title": "កម្មវិធីទាញយកមេឌៀ Telegram",
        "credentials_frame": "ការចូល និងគោលដៅ",
        "api_id_label": "API ID:",
        "api_hash_label": "API Hash:",
        "phone_label": "លេខទូរស័ព្ទ (+...):",
        "login_button": "ចូល / តភ្ជាប់",
        "login_qr_button": "ចូលដោយ QR",
        "logout_button": "ចាកចេញ",
        "change_language_button": "ប្ដូរភាសា",
        "status_label_prefix": "ស្ថានភាព៖",
        "status_not_connected": "មិនបានតភ្ជាប់",
        "status_connecting": "កំពុងតភ្ជាប់...",
        "status_logged_in": "បានចូល",
        "status_login_failed": "ការចូលបរាជ័យ",
        "download_target_frame": "គោលដៅទាញយក និងជម្រើស",
        "chat_label": "Chat (@អ្នកប្រើ, តំណ, ID):",
        "save_to_label": "រក្សាទុកទៅ៖",
        "browse_button": "រកមើល...",
        "skip_existing_cb": "រំលងឯកសារដែលមាន (ពិនិត្យឈ្មោះ & ទំហំ)",
        "media_types_frame": "ប្រភេទមេឌៀត្រូវទាញយក",
        "filter_photos": "រូបថត",
        "filter_videos": "វីដេអូ",
        "filter_audio": "សំឡេង",
        "filter_docs": "ឯកសារ",
        "filter_voice": "សារសំឡេង",
        "filter_stickers": "ស្ទីកគ័រ",
        "filter_gifs": "GIFs",
        "filter_video_notes": "Video Notes",
        "start_button": "ចាប់ផ្តើមទាញយក",
        "stop_button": "បញ្ឈប់ការទាញយក",
        "logs_frame": "កំណត់ហេតុ",
        "log_copy": "ចម្លង",
        "log_copy_all": "ចម្លងទាំងអស់",
        "support_donate": "ឧបត្ថម្ភ កាហ្វេ",
        "progress_label_starting": "កំពុងចាប់ផ្តើមទាញយក...",
        "progress_label_stopping": "កំពុងបញ្ឈប់ការទាញយក...",
        "download_complete": "ការទាញយកបានបញ្ចប់។",
        "not_logged_in_title": "មិនទាន់បានចូល",
        "not_logged_in_msg": "សូមចូលដោយជោគជ័យជាមុនសិន មុននឹងចាប់ផ្តើមទាញយក។",
        "missing_target_title": "ខ្វះគោលដៅ",
        "missing_target_msg": "សូមប្រើប៊ូតុង 'ជ្រើសរើស Chat' ដើម្បីរើសគោលដៅ។",
        "missing_path_title": "ខ្វះទីតាំងរក្សាទុក",
        "missing_path_msg": "សូមជ្រើសរើសថតឯកសារសម្រាប់ទាញយក។",
        "invalid_path_title": "ទីតាំងរក្សាទុកមិនត្រឹមត្រូវ",
        "invalid_path_msg": "កំហុសទីតាំងទាញយក:\n{error}",
        "busy_title": "កំពុងដំណើរការ",
        "busy_msg": "ប្រតិបត្តិការផ្សេងទៀត (ចូល/ទាញយក) កំពុងដំណើរការ។",
        "no_media_types_title": "គ្មានប្រភេទមេឌៀ",
        "no_media_types_msg": "សូមជ្រើសរើសប្រភេទមេឌៀយ៉ាងហោចណាស់មួយដើម្បីទាញយក។",
        "quit_confirmation_title": "បញ្ជាក់ការចាកចេញ",
        "quit_confirmation_msg": "ការទាញយកកំពុងដំណើរការ។ តើអ្នកពិតជាចង់បញ្ឈប់ការទាញយក ហើយចាកចេញមែនទេ?",
        "howto_api_button": "របៀបយក API ID និង API Hash",
        "howto_api_title": "របៀបយក API ID និង API Hash",
        "howto_api_text": "1) បើក https://my.telegram.org ហើយចូលដោយលេខទូរស័ព្ទ។\n2) ចុច \u20cAPI development tools\u201d។\n3) បង្កើតកម្មវិធីថ្មី (ដាក់ឈ្មោះអ្វីក៏បាន).\n4) បន្ទាប់មក ចម្លង \u20cApp api_id\u201d និង \u20cApp api_hash\u201d.\n5) បិទភ្ជាប់ទៅវាល API ID និង API Hash នៅទីនេះ។",
    }
}

# --- Logger ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(ch)
# File log (rotating)
try:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    _log_path = os.path.join(USER_DATA_DIR, 'app.log')
    fh = logging.handlers.RotatingFileHandler(_log_path, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(fh)
except Exception:
    pass

# --- Telegram error reporting ---
class TelegramErrorHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # send ERROR/CRITICAL logs to Telegram asynchronously
        try:
            if record.levelno < logging.ERROR:
                return
            msg = self.format(record)
            send_error_telegram(f"\ud83d\udea8 {APP_NAME} v{APP_VERSION}\n{msg}")
        except Exception:
            pass


def _post_telegram_message(token: str, chat_id: str, text: str) -> None:
    try:
        import urllib.request, urllib.parse, urllib.error as _urlerr
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': text,
            'disable_web_page_preview': 'true'
        }).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception:
        # Never raise from logging path
        pass


def send_error_telegram(text: str) -> None:
    try:
        token = (TELEMETRY_BOT_TOKEN_SECRET or '').strip()
        chat_id = (TELEMETRY_CHAT_ID_SECRET or '').strip()
        if not token or not chat_id:
            return
        # Keep message within Telegram limits
        if len(text) > 4000:
            text = text[:4000] + "\n...(truncated)"
        import threading as _threading
        _threading.Thread(target=_post_telegram_message, args=(token, chat_id, text), daemon=True).start()
    except Exception:
        pass

# Attach Telegram error handler to this module logger
try:
    _th = TelegramErrorHandler()
    _th.setLevel(logging.ERROR)
    _th.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(_th)
except Exception:
    pass

# Global unhandled exception hook to send errors to Telegram as well
def _global_excepthook(exctype, value, tb):
    try:
        # Ignore routine asyncio cancellations
        try:
            import asyncio as _asyncio
            if isinstance(value, _asyncio.CancelledError) or (isinstance(exctype, type) and issubclass(exctype, getattr(_asyncio, 'CancelledError', Exception))):
                return
        except Exception:
            pass
        tb_text = ''.join(traceback.format_exception(exctype, value, tb))
        logger.error('Unhandled exception', exc_info=(exctype, value, tb))
        send_error_telegram(f"\ud83d\udea8 Unhandled exception in {APP_NAME} v{APP_VERSION}\n" + tb_text)
    except Exception:
        pass

sys.excepthook = _global_excepthook


class TelegramDownloaderGUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        except Exception:
            pass

        # State
        self.config = self.load_config()
        self.current_language = self.config.get("language", "en") if self.config.get("language", "en") in translations else "en"
        self.is_logged_in = False
        self.is_downloading = False
        self.dl_worker = None
        self.fetch_chats_worker = None
        self.fetch_profile_worker = None
        self.update_worker = None
        self.selected_chat_info = None
        self.chat_list_cache = None # NEW: Cache for chat list
        self.profile_cache = None # NEW: Cache for selected profile
        # Translation registry: list of (widget, key, attr) where attr in {'text','title'}
        self._tr_registry: list[tuple[object, str, str]] = []

        # Window
        self.setWindowTitle(self._("app_title"))
        self.setMinimumSize(600, 650)
        self._apply_font()
        self._apply_icon()
        self._build_menu_bar()

        # Central widget & layout
        central = QWidget(self)
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        # Global padding/spacing for the main layout
        try:
            self.main_layout.setContentsMargins(12, 12, 12, 12)
            self.main_layout.setSpacing(10)
        except Exception:
            pass

        # Build UI sections
        self._build_credentials_section()
        self._build_options_section()
        self._build_actions_section()
        self._build_progress_section()
        self._build_logs_section()
        self._build_footer()

        # Timers
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.process_log_queue)
        self.queue_timer.start(LOG_QUEUE_INTERVAL_MS)

        self.update_status_label("status_not_connected", color="grey")
        # If a saved session exists, reflect logged-in state automatically
        self._apply_saved_session_state()
        # Send telemetry after UI initializes (non-blocking)
        QTimer.singleShot(0, self._send_launch_telemetry)
        # Check for updates after a short delay
        QTimer.singleShot(5000, self.start_update_check)

    # --- Helpers ---
    def _t_register(self, widget, key: str, attr: str = 'text') -> None:
        self._tr_registry.append((widget, key, attr))

    def _(self, key: str, **kwargs) -> str:
        lang = translations.get(self.current_language, translations["en"])
        base = lang.get(key, translations["en"].get(key, f"_{key}_"))
        try:
            return base.format(**kwargs) if kwargs else base
        except Exception:
            return translations["en"].get(key, f"_{key}_")

    def _apply_font(self) -> None:
        try:
            # 0) Use user-selected font if present
            user_family = str(self.config.get('ui_font_family', '') or '').strip()
            user_size = int(self.config.get('ui_font_size', DEFAULT_FONT_SIZE) or DEFAULT_FONT_SIZE)
            if user_family:
                app_font = QFont(user_family, max(6, min(48, user_size)))
                try:
                    app_font.setWeight(QFont.Weight.Medium)
                except Exception:
                    pass
                QApplication.instance().setFont(app_font)
                QApplication.instance().setStyleSheet("")
                logger.info(f"Applied user font: '{user_family}' (resolved='{QFontInfo(app_font).family()}')")
                return
            # 1) Prefer installed families via QFontDatabase static API
            families = [f for f in QFontDatabase.families()]
            chosen_family: str | None = None
            for fam in families:
                fl = fam.lower()
                if "kantumruy" in fl:
                    chosen_family = fam
                    break
            # 2) If not installed, try to load local TTF/OTF
            if not chosen_family:
                for d in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
                    try:
                        for fn in os.listdir(d):
                            low = fn.lower()
                            if low.startswith("kantumruy") and low.endswith((".ttf", ".otf")):
                                fid = QFontDatabase.addApplicationFont(os.path.join(d, fn))
                                if fid != -1:
                                    fams = QFontDatabase.applicationFontFamilies(fid)
                                    for fam in fams:
                                        if "kantumruy" in fam.lower():
                                            chosen_family = fam
                                            logger.info(f"Loaded font from file: {fn} -> '{fam}'")
                                            break
                            if chosen_family:
                                break
                    except Exception:
                        pass
                    if chosen_family:
                        break
            # 3) Apply once if chosen
            if chosen_family:
                app_font = QFont(chosen_family, DEFAULT_FONT_SIZE)
                try:
                    app_font.setWeight(QFont.Weight.Medium)
                except Exception:
                    pass
                QApplication.instance().setFont(app_font)
                QApplication.instance().setStyleSheet("")  # clear any previous stylesheet override
                logger.info(f"Applied global font: '{chosen_family}' (resolved='{QFontInfo(app_font).family()}')")
            else:
                logger.warning("Kantumruy font not found. Install 'Kantumruy Pro' or place its .ttf next to app_pyqt6.py and restart.")
        except Exception as e:
            logger.warning(f"Font setup error: {e}")

    def _apply_icon(self) -> None:
        try:
            candidates = [
                'app.ico', 'app.png', 'icon.ico', 'icon.png', 'telegram.ico', 'telegram.png'
            ]
            chosen = None
            for d in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
                for name in candidates:
                    p = os.path.join(d, name)
                    if os.path.isfile(p):
                        chosen = p
                        break
                if chosen:
                    break
            if chosen:
                ic = QIcon(chosen)
                QApplication.instance().setWindowIcon(ic)
                self.setWindowIcon(ic)
                logger.info(f"Applied window icon: {os.path.basename(chosen)}")
            else:
                logger.info("No app icon found (place app.ico/app.png next to app_pyqt6.py).")
        except Exception as e:
            logger.warning(f"Icon setup error: {e}")

    # --- UI Builders ---
    def _build_credentials_section(self) -> None:
        box = QGroupBox(self._("credentials_frame"), self)
        grid = QGridLayout(box)
        # Tweak padding and spacing inside the credentials section
        try:
            grid.setContentsMargins(10, 8, 10, 8)
            grid.setHorizontalSpacing(8)
            grid.setVerticalSpacing(6)
        except Exception:
            pass

        # API ID
        self.api_id_label = QLabel(self._("api_id_label"), box)
        self._t_register(self.api_id_label, "api_id_label")
        self.api_id_entry = QLineEdit(box)
        self.api_id_entry.setText(self.config.get("api_id", ""))
        try:
            self.api_id_entry.setPlaceholderText("e.g. 123456")
        except Exception:
            pass
        grid.addWidget(self.api_id_label, 0, 0)
        grid.addWidget(self.api_id_entry, 0, 1)

        # API Hash
        self.api_hash_label = QLabel(self._("api_hash_label"), box)
        self._t_register(self.api_hash_label, "api_hash_label")
        self.api_hash_entry = QLineEdit(box)
        self.api_hash_entry.setText(self.config.get("api_hash", ""))
        try:
            self.api_hash_entry.setPlaceholderText("e.g. 0123456789abcdef0123456789abcdef")
        except Exception:
            pass
        grid.addWidget(self.api_hash_label, 1, 0)
        grid.addWidget(self.api_hash_entry, 1, 1)

        # Phone
        self.phone_label = QLabel(self._("phone_label"), box)
        self._t_register(self.phone_label, "phone_label")
        self.phone_entry = QLineEdit(box)
        self.phone_entry.setText(self.config.get("phone", ""))
        try:
            self.phone_entry.setPlaceholderText("e.g. +85512345678")
        except Exception:
            pass
        # Help link below API Hash (row 2), phone moved to row 3
        grid.addWidget(self.phone_label, 3, 0)
        grid.addWidget(self.phone_entry, 3, 1)

        # Right side: status + buttons
        right_col = QVBoxLayout()
        try:
            right_col.setSpacing(6)
            right_col.setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass
        self.login_status_label = QLabel("", box)
        self.login_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.login_button = QPushButton(self._("login_button"), box)
        self._t_register(self.login_button, "login_button")
        self.login_button.clicked.connect(self.start_login_thread)
        self.login_qr_button = QPushButton(self._("login_qr_button"), box)
        self._t_register(self.login_qr_button, "login_qr_button")
        self.login_qr_button.clicked.connect(self.open_qr_login_dialog)
        self.logout_button = QPushButton(self._("logout_button"), box)
        self._t_register(self.logout_button, "logout_button")
        self.logout_button.setEnabled(False)
        self.logout_button.clicked.connect(self.logout)
        self.lang_button = QPushButton(translations['km' if self.current_language == 'en' else 'en']["change_language_button"], box)
        self.lang_button.clicked.connect(self.switch_language)
        # API help as an underlined link-style label (like donation link)
        self.api_help_label = QLabel(f"<a href='#api_help'>{self._('howto_api_button')}</a>", box)
        self.api_help_label.setTextFormat(Qt.TextFormat.RichText)
        self.api_help_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.api_help_label.setOpenExternalLinks(False)
        self.api_help_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        try:
            self.api_help_label.linkActivated.connect(lambda _href: self.show_api_help())
        except Exception:
            pass
        self._t_register(self.api_help_label, "howto_api_button")
        grid.addWidget(self.api_help_label, 2, 0, 1, 2)
        right_col.addWidget(self.login_status_label)
        right_col.addWidget(self.login_button)
        right_col.addWidget(self.login_qr_button)
        right_col.addWidget(self.logout_button)
        right_col.addWidget(self.lang_button)
        grid.addLayout(right_col, 0, 2, 3, 1)

        # MODIFIED: Chat target with LineEdit, Select button, and View Profile button
        self.chat_label = QLabel(self._("chat_label"), box)
        self._t_register(self.chat_label, "chat_label")
        target_row = QHBoxLayout()
        self.target_display_entry = QLineEdit(box)
        self.target_display_entry.setPlaceholderText("Click 'Select Chat...' to choose a target")
        self.target_display_entry.setReadOnly(True)
        self.select_chat_button = QPushButton("Select Chat...", box)
        self.select_chat_button.clicked.connect(self.open_chat_selection_dialog)
        self.select_chat_button.setEnabled(False)
        self.view_profile_button = QPushButton("View Profile", box)
        self.view_profile_button.clicked.connect(self.show_profile_dialog)
        self.view_profile_button.setEnabled(False)
        target_row.addWidget(self.target_display_entry, 1)
        target_row.addWidget(self.select_chat_button)
        target_row.addWidget(self.view_profile_button)
        grid.addWidget(self.chat_label, 4, 0)
        grid.addLayout(target_row, 4, 1, 1, 2)

        # Save path
        self.save_to_label = QLabel(self._("save_to_label"), box)
        self._t_register(self.save_to_label, "save_to_label")
        path_row = QHBoxLayout()
        self.path_entry = QLineEdit(box)
        self.path_entry.setReadOnly(True)
        self.path_entry.setText(self.config.get("download_path", os.path.abspath(DOWNLOAD_PATH_BASE)))
        try:
            self.path_entry.setPlaceholderText("Choose a folder...")
        except Exception:
            pass
        self.browse_button = QPushButton(self._("browse_button"), box)
        self._t_register(self.browse_button, "browse_button")
        self.browse_button.clicked.connect(self.browse_download_path)
        path_row.addWidget(self.path_entry)
        path_row.addWidget(self.browse_button)
        grid.addWidget(self.save_to_label, 5, 0)
        grid.addLayout(path_row, 5, 1, 1, 2)

        self.main_layout.addWidget(box)

    def _build_options_section(self) -> None:
        outer = QWidget(self)
        v = QVBoxLayout(outer)
        try:
            v.setContentsMargins(10, 8, 10, 8)
            v.setSpacing(8)
        except Exception:
            pass

        # Skip existing
        self.skip_cb = QCheckBox(self._("skip_existing_cb"), outer)
        self._t_register(self.skip_cb, "skip_existing_cb")
        self.skip_cb.setChecked(bool(self.config.get("skip_existing", True)))
        v.addWidget(self.skip_cb)

        # Media types
        self.media_box = QGroupBox(self._("media_types_frame"), outer)
        self._t_register(self.media_box, "media_types_frame", attr='title')
        grid = QGridLayout(self.media_box)
        try:
            grid.setContentsMargins(10, 8, 10, 8)
            grid.setHorizontalSpacing(8)
            grid.setVerticalSpacing(6)
        except Exception:
            pass
        self.filter_photo_cb = QCheckBox(self._("filter_photos"), self.media_box)
        self._t_register(self.filter_photo_cb, "filter_photos")
        self.filter_video_cb = QCheckBox(self._("filter_videos"), self.media_box)
        self._t_register(self.filter_video_cb, "filter_videos")
        self.filter_audio_cb = QCheckBox(self._("filter_audio"), self.media_box)
        self._t_register(self.filter_audio_cb, "filter_audio")
        self.filter_doc_cb = QCheckBox(self._("filter_docs"), self.media_box)
        self._t_register(self.filter_doc_cb, "filter_docs")
        self.filter_voice_cb = QCheckBox(self._("filter_voice"), self.media_box)
        self._t_register(self.filter_voice_cb, "filter_voice")
        self.filter_sticker_cb = QCheckBox(self._("filter_stickers"), self.media_box)
        self._t_register(self.filter_sticker_cb, "filter_stickers")
        self.filter_gif_cb = QCheckBox(self._("filter_gifs"), self.media_box)
        self._t_register(self.filter_gif_cb, "filter_gifs")
        self.filter_video_note_cb = QCheckBox(self._("filter_video_notes"), self.media_box)
        self._t_register(self.filter_video_note_cb, "filter_video_notes")
        self.filter_photo_cb.setChecked(bool(self.config.get("filter_photo", True)))
        self.filter_video_cb.setChecked(bool(self.config.get("filter_video", True)))
        self.filter_audio_cb.setChecked(bool(self.config.get("filter_audio", True)))
        self.filter_doc_cb.setChecked(bool(self.config.get("filter_document", True)))
        self.filter_voice_cb.setChecked(bool(self.config.get("filter_voice", True)))
        self.filter_sticker_cb.setChecked(bool(self.config.get("filter_sticker", False)))
        self.filter_gif_cb.setChecked(bool(self.config.get("filter_gif", True)))
        self.filter_video_note_cb.setChecked(bool(self.config.get("filter_video_note", True)))

        grid.addWidget(self.filter_photo_cb, 0, 0)
        grid.addWidget(self.filter_video_cb, 0, 1)
        grid.addWidget(self.filter_audio_cb, 0, 2)
        grid.addWidget(self.filter_doc_cb, 1, 0)
        grid.addWidget(self.filter_voice_cb, 1, 1)
        grid.addWidget(self.filter_sticker_cb, 1, 2)
        grid.addWidget(self.filter_gif_cb, 2, 0)
        grid.addWidget(self.filter_video_note_cb, 2, 1)

        v.addWidget(self.media_box)
        self.main_layout.addWidget(outer)

    def _build_actions_section(self) -> None:
        wrap = QWidget(self)
        h = QHBoxLayout(wrap)
        try:
            h.setContentsMargins(10, 8, 10, 8)
            h.setSpacing(8)
        except Exception:
            pass
        self.start_button = QPushButton(self._("start_button"), wrap)
        self._t_register(self.start_button, "start_button")
        self.stop_button = QPushButton(self._("stop_button"), wrap)
        self._t_register(self.stop_button, "stop_button")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_download_thread)
        self.stop_button.clicked.connect(self.request_stop)
        h.addWidget(self.start_button)
        h.addWidget(self.stop_button)
        h.addStretch(1)
        self.main_layout.addWidget(wrap)

    def _build_progress_section(self) -> None:
        wrap = QWidget(self)
        v = QVBoxLayout(wrap)
        try:
            v.setContentsMargins(10, 8, 10, 8)
            v.setSpacing(8)
        except Exception:
            pass
        self.progress_bar = QProgressBar(wrap)
        self.progress_bar.setMaximum(100)
        self.progress_label = QLabel("", wrap)
        v.addWidget(self.progress_bar)
        v.addWidget(self.progress_label)
        self.main_layout.addWidget(wrap)

    def _build_logs_section(self) -> None:
        box = QGroupBox(self._("logs_frame"), self)
        self._t_register(box, "logs_frame", attr='title')
        v = QVBoxLayout(box)
        try:
            v.setContentsMargins(10, 8, 10, 8)
            v.setSpacing(8)
        except Exception:
            pass
        self.log_text = QTextEdit(box)
        self.log_text.setReadOnly(True)
        font = QFont()
        font.setPointSize(LOG_FONT_SIZE)
        self.log_text.setFont(font)
        v.addWidget(self.log_text)
        self.main_layout.addWidget(box)
        # Disable copy/copy-all context menu per request
        self.log_text.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def _build_menu_bar(self) -> None:
        try:
            mb = self.menuBar()
            # Edit menu (moved to front)
            m_edit = mb.addMenu('Edit')
            act_clear = QAction('Clear Logs', self)
            act_clear.triggered.connect(lambda: self.log_text.clear())
            m_edit.addAction(act_clear)
            # Settings menu
            m_settings = mb.addMenu('Settings')
            act_settings = QAction('Settings...', self)
            act_settings.triggered.connect(self.open_settings_dialog)
            m_settings.addAction(act_settings)
            # App Info menu
            m_info = mb.addMenu('App Info')
            act_api_help = QAction('How to get API ID & API Hash', self)
            act_api_help.triggered.connect(self.show_api_help)
            m_info.addAction(act_api_help)
            
            # --- MODIFIED: Add manual update check ---
            act_check_update = QAction('Check for Updates...', self)
            act_check_update.triggered.connect(self.start_update_check_manual)
            m_info.addAction(act_check_update)
            
            act_about = QAction('About', self)
            act_about.triggered.connect(self._show_about)
            m_info.addAction(act_about)
        except Exception:
            pass


    def _show_about(self) -> None:
        try:
            info = (
                f"{APP_NAME}\n"
                f"Version: {APP_VERSION}\n\n"
                f"Data folder: {USER_DATA_DIR}\n"
                f"Downloads default: {os.path.abspath(DOWNLOAD_PATH_BASE)}\n\n"
                f"Donate: {DONATION_URL}\n"
                f"{COPYRIGHT_TEXT}"
            )
            QMessageBox.information(self, 'About', info)
        except Exception:
            pass

    def _send_test_error_log(self) -> None:
        try:
            # Disabled by request.
            QMessageBox.information(self, 'Test Error', 'This test action has been disabled.')
        except Exception:
            pass

    def open_font_dialog(self) -> None:
        try:
            current = QApplication.instance().font()
            # PyQt6: getFont returns (font, ok)
            font, ok = QFontDialog.getFont(current, self, 'Select Font')
            if ok and font is not None:
                QApplication.instance().setFont(font)
                QApplication.instance().setStyleSheet("")
                # Save to config
                self.config['ui_font_family'] = font.family()
                self.config['ui_font_size'] = font.pointSize() if font.pointSize() > 0 else DEFAULT_FONT_SIZE
                self.save_config()
                logger.info(f"User changed font to: '{font.family()}' size {self.config['ui_font_size']}")
        except Exception as e:
            logger.warning(f"Font dialog error: {e}")

    def open_settings_dialog(self) -> None:
        try:
            dlg = SettingsDialog(self)
            dlg.exec()
        except Exception as e:
            logger.warning(f"Settings dialog error: {e}")

    def show_api_help(self) -> None:
        try:
            # Build clearer, larger, clickable instructions for the URL.
            link_url = 'https://my.telegram.org'
            text_raw = self._('howto_api_text')
            link_html = f"<a href='{link_url}' style='color:#1a73e8; text-decoration: underline; font-weight:600;'>{link_url}</a>"
            html = text_raw.replace('https://my.telegram.org', link_html).replace('\n', '<br>')
            html = f"<div style='font-size:11pt; line-height:1.5; color:#111;'>{html}</div>"

            dlg = QDialog(self)
            dlg.setWindowTitle(self._('howto_api_title'))
            try:
                dlg.setWindowIcon(self.windowIcon())
            except Exception:
                pass
            dlg.resize(560, 260)
            v = QVBoxLayout(dlg)
            try:
                v.setContentsMargins(16, 14, 16, 10)
                v.setSpacing(10)
            except Exception:
                pass
            lbl = QLabel(html, dlg)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            lbl.setOpenExternalLinks(True)
            lbl.setWordWrap(True)
            v.addWidget(lbl)
            # Action buttons: Open Website, Copy Link, OK
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=dlg)
            btn_open = QPushButton('Open Website', dlg)
            btn_copy = QPushButton('Copy Link', dlg)
            btn_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(link_url)))
            btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(link_url))
            try:
                btns.addButton(btn_open, QDialogButtonBox.ButtonRole.ActionRole)
                btns.addButton(btn_copy, QDialogButtonBox.ButtonRole.ActionRole)
            except Exception:
                # Fallback: add to layout if ButtonBox roles unsupported
                h = QHBoxLayout()
                h.addWidget(btn_open)
                h.addWidget(btn_copy)
                v.addLayout(h)
            btns.accepted.connect(dlg.accept)
            v.addWidget(btns)
            dlg.exec()
        except Exception:
            pass

    def _build_footer(self) -> None:
        # Donation link
        self.donation_label = QLabel(f'<a href="{DONATION_URL}">{self._("support_donate")}</a>', self)
        self._t_register(self.donation_label, "support_donate")
        self.donation_label.setOpenExternalLinks(True)
        font = self.donation_label.font()
        font.setPointSize(DONATION_FONT_SIZE)
        self.donation_label.setFont(font)
        self.donation_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.main_layout.addWidget(self.donation_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Copyright
        copy = QLabel(COPYRIGHT_TEXT, self)
        f2 = copy.font()
        f2.setPointSize(COPYRIGHT_FONT_SIZE)
        copy.setFont(f2)
        self.main_layout.addWidget(copy, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Add stretch at the end to push footer to bottom when window grows
        self.main_layout.addStretch(1)

    # --- UI Actions ---
    def _apply_saved_session_state(self) -> None:
        try:
            api_id_str = str(self.config.get("api_id", "")).strip()
            if not api_id_str:
                return
            api_id = int(api_id_str)
            session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
            if os.path.isfile(session_file):
                self.is_logged_in = True
                self.start_button.setEnabled(True)
                self.select_chat_button.setEnabled(False) # Will be enabled after fetch
                self.login_button.setEnabled(False)
                self.login_qr_button.setEnabled(False)
                self.logout_button.setEnabled(True)
                self.update_status_label("status_logged_in", username=None, color="green")
                self._initiate_auto_chat_fetch() # MODIFIED
        except Exception:
            pass

    def _compose_telemetry_message(self) -> str:
        try:
            sys_ver = platform.platform()
            machine = platform.machine()
            hostname = socket.gethostname()
            user = getpass.getuser()
            now_iso = datetime.now().isoformat()
            app_name = APP_NAME
            return (
                "🆕 New App Launch\n\n"
                "📊 System Info:\n"
                f"• OS: {sys_ver}\n"
                f"• Machine: {machine}\n"
                f"• Hostname: {hostname}\n"
                f"• User: {user}\n"
                f"• name app : {app_name}\n"
                f"• Version: {APP_VERSION}\n"
                f"• Time: {now_iso}"
            )
        except Exception as e:
            return f"New App Launch (telemetry build error: {e})"

    def _send_launch_telemetry(self) -> None:
        try:
            if not (TELEMETRY_FORCE_ENABLED or bool(self.config.get("telemetry_enabled", False))):
                logger.info("Telemetry disabled; skipping.")
                return
            token = (TELEMETRY_BOT_TOKEN_SECRET or str(self.config.get("telemetry_bot_token", "")).strip()).strip()
            chat_id = (TELEMETRY_CHAT_ID_SECRET or str(self.config.get("telemetry_chat_id", "")).strip()).strip()
            if not token or not chat_id:
                logger.warning("Telemetry not configured (token/chat_id missing); skipping.")
                return
            text = self._compose_telemetry_message()
            import threading
            logger.info("Sending telemetry message in background...")
            threading.Thread(target=self._send_telemetry, args=(token, chat_id, text), daemon=True).start()
        except Exception as e:
            logger.warning(f"Telemetry setup error: {e}")

    def _send_telemetry(self, token: str, chat_id: str, text: str) -> None:
        try:
            import urllib.request, urllib.parse, json as _json, urllib.error as _urlerr
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({
                'chat_id': chat_id,
                'text': text,
                'disable_web_page_preview': 'true'
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                try:
                    obj = _json.loads(body.decode('utf-8', errors='ignore') or '{}')
                    if obj.get('ok'):
                        logger.info("Telemetry sent successfully.")
                    else:
                        logger.warning(f"Telemetry response not ok: {obj}")
                except Exception:
                    logger.info("Telemetry sent (non-JSON response).")
        except _urlerr.HTTPError as he:
            try:
                err_body = he.read().decode('utf-8', errors='ignore')
            except Exception:
                err_body = str(he)
            logger.warning(f"Telemetry HTTP error {he.code}: {err_body}")
        except Exception as e:
            # Do not interrupt app on telemetry failure
            logger.warning(f"Telemetry error: {e}")

    def update_status_label(self, status_key: str = "status_not_connected", username: str | None = None, color: str = "grey") -> None:
        prefix = self._("status_label_prefix")
        status_text = self._(status_key)
        full = f"{prefix} {status_text}" + (f" ({username})" if username else "")
        self.login_status_label.setText(full)
        # color via stylesheet for simplicity
        self.login_status_label.setStyleSheet(f"color: {color};")
        # Language button shows the other language text
        other_lang = 'en' if self.current_language == 'km' else 'km'
        self.lang_button.setText(translations[other_lang]['change_language_button'])

    def switch_language(self) -> None:
        self.current_language = 'km' if self.current_language == 'en' else 'en'
        self.config["language"] = self.current_language
        self.setWindowTitle(self._("app_title"))
        # Update texts
        self._refresh_texts()
        self.update_status_label(status_key="status_not_connected", color="grey")

    def _refresh_texts(self) -> None:
        for widget, key, attr in self._tr_registry:
            try:
                text = self._(key)
                if attr == 'title' and hasattr(widget, 'setTitle'):
                    widget.setTitle(text)
                elif hasattr(widget, 'setText'):
                    # Support HTML donation label and API help link label
                    if widget is getattr(self, 'donation_label', None):
                        widget.setText(f'<a href="{DONATION_URL}">{text}</a>')
                    elif widget is getattr(self, 'api_help_label', None):
                        widget.setText(f"<a href='#api_help'>{text}</a>")
                    else:
                        widget.setText(text)
            except Exception:
                pass
        # Logs title: left as-is

    def _show_log_context_menu(self, pos) -> None:
        # Context menu removed
        pass

    def copy_log_selection(self) -> None:
        cursor = self.log_text.textCursor()
        text = cursor.selectedText()
        if not text:
            return
        QApplication.clipboard().setText(text)

    def copy_log_all(self) -> None:
        text = self.log_text.toPlainText().strip()
        if not text:
            return
        QApplication.clipboard().setText(text)

    def logout(self) -> None:
        if self.is_downloading:
            ret = QMessageBox.question(
                self,
                self._("quit_confirmation_title"),
                self._("quit_confirmation_msg"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ret != QMessageBox.StandardButton.Yes:
                return
            self.request_stop()
        # Remove saved session if exists
        api_id_str = self.api_id_entry.text().strip() or str(self.config.get("api_id", ""))
        try:
            api_id = int(api_id_str) if api_id_str else None
        except Exception:
            api_id = None
        if api_id is not None:
            session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
            try:
                if os.path.isfile(session_file):
                    os.remove(session_file)
            except Exception as e:
                QMessageBox.warning(self, "Logout", f"Could not remove session file: {e}")
        # Reset UI state and caches
        self.is_logged_in = False
        self.chat_list_cache = None
        self.profile_cache = None
        self.selected_chat_info = None
        self.target_display_entry.clear()
        self.start_button.setEnabled(False)
        self.select_chat_button.setEnabled(False)
        self.view_profile_button.setEnabled(False)
        self.login_button.setEnabled(True)
        self.login_qr_button.setEnabled(True)
        self.logout_button.setEnabled(False)
        self.update_status_label("status_not_connected", color="grey")

    def browse_download_path(self) -> None:
        initial_dir = os.path.dirname(self.path_entry.text()) if os.path.isdir(os.path.dirname(self.path_entry.text())) else os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, self._("save_to_label"), initial_dir)
        if path:
            self.path_entry.setText(os.path.abspath(path))

    def open_qr_login_dialog(self) -> None:
        if not TELETHON_AVAILABLE:
            QMessageBox.critical(self, "Dependency Error", self._("qr_dep_missing"))
            return
        api_id_str = self.api_id_entry.text().strip()
        api_hash = self.api_hash_entry.text().strip()
        if not (api_id_str and api_hash):
            QMessageBox.critical(self, "Missing Credentials", "Please enter API ID and API Hash for QR login.")
            return
        try:
            api_id = int(api_id_str)
        except ValueError:
            QMessageBox.critical(self, "Invalid API ID", "API ID must be a whole number.")
            return
        dlg = QrLoginDialog(self, api_id, api_hash)
        dlg.login_success.connect(self._on_qr_login_success)
        dlg.exec()

    def _on_qr_login_success(self, username: str, api_id: int, api_hash: str, session_string: str) -> None:
        # Save session
        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        try:
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(session_string)
        except Exception as e:
            logger.warning(f"Could not save session to {session_file}: {e}")
        # Update state
        self.is_logged_in = True
        self.start_button.setEnabled(True)
        self.select_chat_button.setEnabled(False) # Will be enabled after fetch
        self.login_button.setEnabled(False)
        self.login_qr_button.setEnabled(False)
        self.logout_button.setEnabled(True)
        self.update_status_label("status_logged_in", username=username, color="green")
        try:
            QMessageBox.information(self, "Login Successful", f"Logged in as {username}.")
        except Exception:
            pass
        self.save_config()
        self.append_log(f"[INFO] QR login success as {username}")
        self._initiate_auto_chat_fetch() # MODIFIED

    def start_login_thread(self) -> None:
        if self.is_downloading:
            QMessageBox.warning(self, self._("busy_title"), self._("busy_msg"))
            return
        if not TELETHON_AVAILABLE:
            QMessageBox.critical(self, "Dependency Error", "Install telethon: pip install telethon")
            return
        api_id_str = self.api_id_entry.text().strip()
        api_hash = self.api_hash_entry.text().strip()
        phone = self.phone_entry.text().strip()
        if not (api_id_str and api_hash and phone):
            QMessageBox.critical(self, "Missing Credentials", "Please enter API ID, API Hash, and Phone Number.")
            return
        try:
            api_id = int(api_id_str)
        except ValueError:
            QMessageBox.critical(self, "Invalid API ID", "API ID must be a whole number.")
            return
        dlg = PhoneLoginDialog(self, api_id, api_hash, phone)
        dlg.login_success.connect(self._on_qr_login_success)
        dlg.exec()

    def start_download_thread(self) -> None:
        if not TELETHON_AVAILABLE:
            QMessageBox.critical(self, "Dependency Error", "Install telethon: pip install telethon")
            return
        if not self.is_logged_in:
            QMessageBox.critical(self, self._("not_logged_in_title"), self._("not_logged_in_msg"))
            return

        if self.selected_chat_info:
            target_title, target_id = self.selected_chat_info
            target = str(target_id)
            self.append_log(f"[INFO] Using selected chat: '{target_title}' (ID: {target})")
        else:
            QMessageBox.critical(self, self._("missing_target_title"), self._("missing_target_msg"))
            return

        download_path = self.path_entry.text().strip()
        if not target:
            QMessageBox.critical(self, self._("missing_target_title"), self._("missing_target_msg"))
            return
        if not download_path:
            QMessageBox.critical(self, self._("missing_path_title"), self._("missing_path_msg"))
            return
        try:
            os.makedirs(download_path, exist_ok=True)
            if not os.access(download_path, os.W_OK | os.X_OK):
                raise OSError("No write permission")
        except OSError as e:
            QMessageBox.critical(self, self._("invalid_path_title"), self._("invalid_path_msg", error=e))
            return
        media_selected = any([
            self.filter_photo_cb.isChecked(), self.filter_video_cb.isChecked(), self.filter_audio_cb.isChecked(),
            self.filter_doc_cb.isChecked(), self.filter_voice_cb.isChecked(), self.filter_sticker_cb.isChecked(),
            self.filter_gif_cb.isChecked(), self.filter_video_note_cb.isChecked()
        ])
        if not media_selected:
            QMessageBox.warning(self, self._("no_media_types_title"), self._("no_media_types_msg"))
            return
        # Require saved session string
        api_id_str = self.api_id_entry.text().strip()
        api_hash = self.api_hash_entry.text().strip()
        try:
            api_id = int(api_id_str)
        except Exception:
            QMessageBox.critical(self, "Invalid API ID", "API ID must be a whole number.")
            return
        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        if not os.path.isfile(session_file):
            QMessageBox.critical(self, "Not Logged In", "Please login first to create a session.")
            return
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_string = f.read().strip()
        except Exception as e:
            QMessageBox.critical(self, "Session Error", f"Failed to read session: {e}")
            return
        # Start real download worker
        from typing import cast as _cast  # noqa: F401 (local import for safety)
        filters = {
            'photo': self.filter_photo_cb.isChecked(),
            'video': self.filter_video_cb.isChecked(),
            'audio': self.filter_audio_cb.isChecked(),
            'document': self.filter_doc_cb.isChecked(),
            'voice': self.filter_voice_cb.isChecked(),
            'sticker': self.filter_sticker_cb.isChecked(),
            'gif': self.filter_gif_cb.isChecked(),
            'video_note': self.filter_video_note_cb.isChecked(),
        }
        self.is_downloading = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self._set_download_controls_enabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(self._("progress_label_starting"))
        self.append_log(f"[INFO] Starting download for target: {target}")
        try:
            self.dl_worker = DownloadWorker(api_id, api_hash, session_string, target, download_path, filters, self.skip_cb.isChecked())
            self.dl_worker.log.connect(self.append_log)
            self.dl_worker.status.connect(lambda s: self.progress_label.setText(s))
            self.dl_worker.progress.connect(lambda v: self.progress_bar.setValue(max(0, min(100, v))))
            self.dl_worker.finished_signal.connect(self.download_finished)
            self.dl_worker.start()
        except Exception as e:
            self.is_downloading = False
            self.start_button.setEnabled(self.is_logged_in)
            self.stop_button.setEnabled(False)
            self._set_download_controls_enabled(True)
            QMessageBox.critical(self, "Start Error", str(e))

    def request_stop(self) -> None:
        if self.is_downloading:
            self.progress_label.setText(self._("progress_label_stopping"))
            self.append_log("[WARN] Stop requested by user.")
            self.stop_button.setEnabled(False)
            try:
                if self.dl_worker is not None and self.dl_worker.isRunning():
                    self.dl_worker.stop()
                else:
                    self.is_downloading = False
                    QTimer.singleShot(300, lambda: self.download_finished(False, "Stopped by user"))
            except Exception:
                self.is_downloading = False
                QTimer.singleShot(300, lambda: self.download_finished(False, "Stopped by user"))

    def download_finished(self, success: bool, message: str) -> None:
        self.is_downloading = False
        self.start_button.setEnabled(self.is_logged_in)
        self.stop_button.setEnabled(False)
        self._set_download_controls_enabled(True)
        try:
            if self.dl_worker is not None:
                if self.dl_worker.isRunning():
                    self.dl_worker.wait(2000)
                self.dl_worker = None
        except Exception:
            self.dl_worker = None
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText(self._("download_complete"))
            self.append_log("[INFO] Download complete.")
        else:
            if isinstance(message, str) and message.lower().startswith("stopped"):
                self.progress_label.setText("Stopped.")
                self.append_log("[INFO] Download stopped by user.")
            else:
                self.append_log(f"[ERROR] Download failed: {message}")

    def _set_download_controls_enabled(self, enabled: bool) -> None:
        self.target_display_entry.setEnabled(enabled)
        # Only re-enable select button if logged in AND chat list is cached
        self.select_chat_button.setEnabled(enabled and self.is_logged_in and self.chat_list_cache is not None)
        # Only enable profile button if logged in AND a chat is selected AND profile is cached
        self.view_profile_button.setEnabled(enabled and self.is_logged_in and self.selected_chat_info is not None and self.profile_cache is not None)
        self.browse_button.setEnabled(enabled)
        self.skip_cb.setEnabled(enabled)
        self.filter_photo_cb.setEnabled(enabled)
        self.filter_video_cb.setEnabled(enabled)
        self.filter_audio_cb.setEnabled(enabled)
        self.filter_doc_cb.setEnabled(enabled)
        self.filter_voice_cb.setEnabled(enabled)
        self.filter_sticker_cb.setEnabled(enabled)
        self.filter_gif_cb.setEnabled(enabled)
        self.filter_video_note_cb.setEnabled(enabled)

    def append_log(self, message: str) -> None:
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def process_log_queue(self) -> None:
        # Placeholder for future background thread queue polling
        pass

    # --- Methods for fetching chats and profiles ---
    def _initiate_auto_chat_fetch(self) -> None:
        if not self.is_logged_in:
            return

        api_id_str = self.api_id_entry.text().strip()
        try:
            api_id = int(api_id_str)
        except Exception:
            self.append_log("[ERROR] Cannot auto-fetch chats: Invalid API ID.")
            return

        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        if not os.path.isfile(session_file):
            return # Should not happen if is_logged_in is true, but as a safeguard
        
        self.select_chat_button.setEnabled(False)
        self.select_chat_button.setText("Fetching...")
        self.append_log("[INFO] Auto-fetching recent chats...")

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_string = f.read().strip()
        except Exception as e:
            self._on_fetch_chats_error(f"Failed to read session: {e}")
            return
            
        self.fetch_chats_worker = FetchChatsWorker(api_id, self.api_hash_entry.text().strip(), session_string)
        self.fetch_chats_worker.chats_fetched.connect(self._on_chats_fetched)
        self.fetch_chats_worker.error.connect(self._on_fetch_chats_error)
        self.fetch_chats_worker.finished_signal.connect(self._on_fetch_chats_finished)
        self.fetch_chats_worker.start()

    def open_chat_selection_dialog(self) -> None:
        if self.chat_list_cache is None:
            QMessageBox.information(self, "Chats Not Ready", "The chat list is still being fetched. Please try again in a moment.")
            return

        dialog = SelectChatDialog(self.chat_list_cache, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.selected_chat
            if selected:
                # If selection changed, clear old profile cache and fetch new one
                if self.selected_chat_info != selected:
                    self.profile_cache = None
                    self.selected_chat_info = selected
                    title, chat_id = self.selected_chat_info
                    self.target_display_entry.setText(title)
                    self.view_profile_button.setEnabled(False) # Disable until new profile is fetched
                    self.append_log(f"[INFO] User selected chat: '{title}' (ID: {chat_id})")
                    self._initiate_auto_profile_fetch()
            else:
                self.append_log("[WARN] Chat selection dialog was accepted, but no chat was chosen.")
        else:
            self.append_log("[INFO] Chat selection was cancelled.")

    def _on_chats_fetched(self, chats: list) -> None:
        self.append_log(f"[INFO] Chat list fetched and cached with {len(chats)} chats.")
        self.chat_list_cache = chats

    def _on_fetch_chats_error(self, message: str) -> None:
        self.append_log(f"[ERROR] Failed to fetch chats: {message}")
        self.chat_list_cache = [] # Cache empty list on error to prevent retries

    def _on_fetch_chats_finished(self) -> None:
        self.select_chat_button.setText("Select Chat...")
        self.select_chat_button.setEnabled(True)
        self.fetch_chats_worker = None
    
    def _initiate_auto_profile_fetch(self) -> None:
        if not self.is_logged_in or not self.selected_chat_info:
            return
        
        api_id_str = self.api_id_entry.text().strip()
        _, chat_id = self.selected_chat_info

        try:
            api_id = int(api_id_str)
        except Exception:
            self.append_log(f"[ERROR] Cannot fetch profile for {chat_id}: Invalid API ID.")
            return

        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        if not os.path.isfile(session_file): return

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_string = f.read().strip()
        except Exception as e:
            self._on_fetch_profile_error(f"Failed to read session: {e}")
            return
        
        self.view_profile_button.setText("Fetching...")
        self.append_log(f"[INFO] Auto-fetching profile for chat ID: {chat_id}")

        self.fetch_profile_worker = FetchProfileWorker(api_id, self.api_hash_entry.text().strip(), session_string, chat_id)
        self.fetch_profile_worker.profile_fetched.connect(self._on_profile_fetched)
        self.fetch_profile_worker.error.connect(self._on_fetch_profile_error)
        self.fetch_profile_worker.finished_signal.connect(self._on_fetch_profile_finished)
        self.fetch_profile_worker.start()

    def show_profile_dialog(self) -> None:
        if self.profile_cache:
            dialog = ProfileDialog(self.profile_cache, self)
            dialog.exec()
        else:
            QMessageBox.information(self, "Profile Not Ready", "Profile data is still being fetched. Please try again in a moment.")

    def _on_profile_fetched(self, profile_data: dict) -> None:
        self.append_log(f"[INFO] Successfully fetched and cached profile for '{profile_data.get('title', 'N/A')}'.")
        self.profile_cache = profile_data

    def _on_fetch_profile_error(self, message: str) -> None:
        self.append_log(f"[ERROR] Failed to fetch profile: {message}")
        self.profile_cache = {} # Cache empty dict on error

    def _on_fetch_profile_finished(self) -> None:
        self.view_profile_button.setText("View Profile")
        self.view_profile_button.setEnabled(True)
        self.fetch_profile_worker = None

    # --- Config ---
    def load_config(self) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                raw = f.read()
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError as e:
                try:
                    dec = json.JSONDecoder()
                    s = raw.lstrip()
                    obj, idx = dec.raw_decode(s)
                    if isinstance(obj, dict):
                        loaded = obj
                        logger.warning(f"Config had trailing/invalid data at pos {idx}. Rewriting a cleaned config.")
                        cfg_tmp = DEFAULT_CONFIG.copy()
                        cfg_tmp.update(loaded)
                        cfg_tmp["download_path"] = os.path.abspath(cfg_tmp.get("download_path", DEFAULT_CONFIG["download_path"]))
                        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as wf:
                            json.dump(cfg_tmp, wf, indent=4, ensure_ascii=False)
                    else:
                        raise e
                except Exception:
                    try:
                        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
                        bad_path = f"{CONFIG_FILE}.bad.{ts}.json"
                        os.replace(CONFIG_FILE, bad_path)
                        logger.error(f"Config corrupted (JSON). Backed up to {bad_path}.")
                    except Exception:
                        logger.error("Config corrupted (JSON) and could not be backed up; using defaults.")
                    loaded = {}
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(loaded)
            cfg["download_path"] = os.path.abspath(cfg.get("download_path", DEFAULT_CONFIG["download_path"]))
            try:
                cfg.pop("telemetry_bot_token", None)
                cfg.pop("telemetry_chat_id", None)
                if TELEMETRY_FORCE_ENABLED:
                    cfg["telemetry_enabled"] = True
            except Exception:
                pass
            logger.info(f"Configuration loaded from {CONFIG_FILE}")
            return cfg
        except FileNotFoundError:
            logger.info(f"{CONFIG_FILE} not found, using defaults.")
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        try:
            self.config['api_id'] = self.api_id_entry.text()
            self.config['api_hash'] = self.api_hash_entry.text()
            self.config['phone'] = self.phone_entry.text()
            self.config['download_path'] = self.path_entry.text()
            self.config['skip_existing'] = self.skip_cb.isChecked()
            self.config['filter_photo'] = self.filter_photo_cb.isChecked()
            self.config['filter_video'] = self.filter_video_cb.isChecked()
            self.config['filter_audio'] = self.filter_audio_cb.isChecked()
            self.config['filter_document'] = self.filter_doc_cb.isChecked()
            self.config['filter_voice'] = self.filter_voice_cb.isChecked()
            self.config['filter_sticker'] = self.filter_sticker_cb.isChecked()
            self.config['filter_gif'] = self.filter_gif_cb.isChecked()
            self.config['filter_video_note'] = self.filter_video_note_cb.isChecked()
            self.config['language'] = self.current_language
            # Prepare a copy without telemetry secrets
            data = dict(self.config)
            data.pop('telemetry_bot_token', None)
            data.pop('telemetry_chat_id', None)
            if TELEMETRY_FORCE_ENABLED:
                data['telemetry_enabled'] = True
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error saving config to {CONFIG_FILE}: {e}")

    # --- Window events ---
    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.is_downloading:
            ret = QMessageBox.question(
                self,
                self._("quit_confirmation_title"),
                self._("quit_confirmation_msg"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ret != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        else:
            ret = QMessageBox.question(
                self,
                self._("quit_confirmation_title"),
                "Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ret != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self.shutdown_cleanup()
        self.save_config()
        event.accept()

    def shutdown_cleanup(self) -> None:
        try:
            if self.dl_worker is not None:
                try: self.dl_worker.stop()
                except Exception: pass
                if self.dl_worker.isRunning(): self.dl_worker.wait(5000)
            
            if self.fetch_chats_worker is not None:
                try: self.fetch_chats_worker.stop()
                except Exception: pass
                if self.fetch_chats_worker.isRunning(): self.fetch_chats_worker.wait(5000)

            if self.fetch_profile_worker is not None:
                try: self.fetch_profile_worker.stop()
                except Exception: pass
                if self.fetch_profile_worker.isRunning(): self.fetch_profile_worker.wait(5000)
        except Exception:
            pass
            
    # --- MODIFIED: Update Checker Methods ---
    def start_update_check(self, is_manual: bool = False) -> None:
        try:
            if self.update_worker and self.update_worker.isRunning():
                logger.info("Update check already in progress.")
                return

            logger.info("Checking for application updates...")
            self.update_worker = UpdateCheckWorker()
            
            # Connect signals
            self.update_worker.update_found.connect(self.show_update_notification)
            self.update_worker.error.connect(
                lambda msg: self.on_update_error(msg, is_manual)
            )
            if is_manual:
                self.update_worker.no_update_found.connect(self.show_no_update_notification)

            self.update_worker.start()
        except Exception as e:
            self.append_log(f"[WARN] Could not start update checker: {e}")

    def start_update_check_manual(self) -> None:
        self.append_log("[INFO] Manual update check initiated...")
        self.start_update_check(is_manual=True)

    def on_update_error(self, message: str, is_manual: bool) -> None:
        log_msg = f"[WARN] Update check failed: {message}"
        self.append_log(log_msg)
        logger.warning(log_msg)
        if is_manual:
            QMessageBox.warning(self, "Update Check Failed", f"Could not check for updates.\n\nError: {message}")

    def show_no_update_notification(self) -> None:
        logger.info("No new update found.")
        QMessageBox.information(self, "You are up-to-date", f"You are running the latest version of {APP_NAME} (v{APP_VERSION}).")

    def show_update_notification(self, new_version: str, release_notes: str, release_url: str) -> None:
        try:
            title = "Update Available"
            text = (
                f"A new version of {APP_NAME} is available!\n\n"
                f"  •  Current version: {APP_VERSION}\n"
                f"  •  New version: {new_version}\n\n"
                "Would you like to open the download page?"
            )
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            if release_notes:
                msg_box.setDetailedText(release_notes)
                
            ret = msg_box.exec()
            
            if ret == QMessageBox.StandardButton.Yes:
                logger.info(f"User chose to open update URL: {release_url}")
                QDesktopServices.openUrl(QUrl(release_url))
        except Exception as e:
            logger.error(f"Failed to show update notification: {e}")


# --- Settings Dialog ---
class SettingsDialog(QDialog):
    def __init__(self, parent: TelegramDownloaderGUI) -> None:
        super().__init__(parent)
        self.parent_gui = parent
        self.setWindowTitle('Settings')
        try:
            self.setWindowIcon(parent.windowIcon())
        except Exception:
            pass
        self.setModal(True)
        self.resize(420, 200)
        v = QVBoxLayout(self)
        # Font section
        self.font_label = QLabel('', self)
        v.addWidget(self.font_label)
        hb = QHBoxLayout()
        self.btn_change_font = QPushButton('Change Font...', self)
        self.btn_change_font.clicked.connect(self._choose_font)
        self.btn_reset_font = QPushButton('Reset Font', self)
        self.btn_reset_font.clicked.connect(self._reset_font)
        hb.addWidget(self.btn_change_font)
        hb.addWidget(self.btn_reset_font)
        hb.addStretch(1)
        v.addLayout(hb)
        # Dialog buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        # State
        self._chosen_font: QFont | None = None
        self._reset = False
        self._update_font_label()

    def _current_cfg_font(self) -> QFont:
        fam = str(self.parent_gui.config.get('ui_font_family', '') or '').strip()
        size = int(self.parent_gui.config.get('ui_font_size', DEFAULT_FONT_SIZE) or DEFAULT_FONT_SIZE)
        if fam:
            return QFont(fam, size)
        return QApplication.instance().font()

    def _update_font_label(self) -> None:
        try:
            if self._reset:
                txt = f"UI Font: Default ({TARGET_FONT_NAME} or system)"
            elif self._chosen_font is not None:
                txt = f"UI Font: {self._chosen_font.family()} {self._chosen_font.pointSize()}"
            else:
                f = self._current_cfg_font()
                txt = f"UI Font: {f.family()} {f.pointSize()}"
            self.font_label.setText(txt)
        except Exception:
            pass

    def _choose_font(self) -> None:
        try:
            current = self._current_cfg_font()
            font, ok = QFontDialog.getFont(current, self, 'Select Font')
            if ok and font is not None:
                self._chosen_font = font
                self._reset = False
                self._update_font_label()
        except Exception:
            pass

    def _reset_font(self) -> None:
        self._chosen_font = None
        self._reset = True
        self._update_font_label()

    def accept(self) -> None:
        try:
            if self._reset:
                self.parent_gui.config['ui_font_family'] = ''
                self.parent_gui.config['ui_font_size'] = DEFAULT_FONT_SIZE
                self.parent_gui._apply_font()
                self.parent_gui.save_config()
                logger.info("User reset font to default")
            elif self._chosen_font is not None:
                QApplication.instance().setFont(self._chosen_font)
                QApplication.instance().setStyleSheet("")
                self.parent_gui.config['ui_font_family'] = self._chosen_font.family()
                self.parent_gui.config['ui_font_size'] = self._chosen_font.pointSize() if self._chosen_font.pointSize() > 0 else DEFAULT_FONT_SIZE
                self.parent_gui.save_config()
                logger.info(f"User changed font to: '{self._chosen_font.family()}' size {self.parent_gui.config['ui_font_size']}")
        except Exception:
            pass
        super().accept()


# --- Chat Selection, Profile, and Login Dialogs ---

class SelectChatDialog(QDialog):
    def __init__(self, chats: list, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select a Chat")
        self.setMinimumSize(450, 500)
        self.selected_chat = None

        layout = QVBoxLayout(self)

        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Search for a chat...")
        self.filter_input.textChanged.connect(self._filter_list)
        layout.addWidget(self.filter_input)

        self.list_widget = QListWidget(self)
        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self._populate_list(chats)

    def _populate_list(self, chats: list) -> None:
        self.list_widget.clear()

        users, groups, errors = [], [], []
        for chat_data in chats:
            try:
                display_title, _ = chat_data
                if "members" in display_title.lower() or "subscribers" in display_title.lower():
                    groups.append(chat_data)
                else:
                    users.append(chat_data)
            except Exception:
                errors.append(chat_data)

        users.sort(key=lambda x: x[0].lower())
        groups.sort(key=lambda x: x[0].lower())

        def add_category(category_list, separator_text):
            if category_list:
                sep_item = QListWidgetItem(f"────── {separator_text} ──────")
                sep_item.setFlags(sep_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.list_widget.addItem(sep_item)
                for title, chat_id in category_list:
                    item = QListWidgetItem(title)
                    item.setData(Qt.ItemDataRole.UserRole, chat_id)
                    self.list_widget.addItem(item)
        
        add_category(users, "USERS & BOTS")
        add_category(groups, "GROUPS & CHANNELS")

    def _filter_list(self, text: str) -> None:
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            is_separator = not (item.flags() & Qt.ItemFlag.ItemIsSelectable)
            if is_separator:
                item.setHidden(False)
                continue
            item.setHidden(text not in item.text().lower())
            
    def get_selected_chat(self) -> tuple[str, int] | None:
        current_item = self.list_widget.currentItem()
        if current_item and (current_item.flags() & Qt.ItemFlag.ItemIsSelectable):
            title = current_item.text()
            chat_id = current_item.data(Qt.ItemDataRole.UserRole)
            return title, chat_id
        return None

    def accept(self) -> None:
        self.selected_chat = self.get_selected_chat()
        if self.selected_chat:
            super().accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a chat from the list or press Cancel.")


class ProfileDialog(QDialog):
    def __init__(self, profile_data: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.profile_data = profile_data
        self.setWindowTitle("Chat Profile")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setSpacing(10)

        # Profile picture
        self.photo_label = QLabel(self)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_path = profile_data.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            self.photo_label.setPixmap(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.photo_label)

        # Details
        row = 0
        details = {
            "Name": profile_data.get("title"),
            "Username": f"@{profile_data.get('username')}" if profile_data.get('username') else "N/A",
            "ID": str(profile_data.get("id")),
            "Type": profile_data.get("type"),
            "Members": str(profile_data.get("members_count")) if profile_data.get("members_count") is not None else "N/A",
        }

        for key, value in details.items():
            if value:
                key_label = QLabel(f"<b>{key}:</b>", self)
                value_label = QLineEdit(value, self)
                value_label.setReadOnly(True)
                grid.addWidget(key_label, row, 0)
                grid.addWidget(value_label, row, 1)
                row += 1

        layout.addLayout(grid)

        # Description/Bio
        description = profile_data.get("description")
        if description:
            desc_group = QGroupBox("Bio / Description", self)
            desc_layout = QVBoxLayout(desc_group)
            desc_text = QTextEdit(description, self)
            desc_text.setReadOnly(True)
            desc_layout.addWidget(desc_text)
            layout.addWidget(desc_group)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)
    
    def done(self, result: int) -> None:
        # Clean up the temporary photo file
        photo_path = self.profile_data.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception as e:
                logger.warning(f"Could not remove temp profile photo {photo_path}: {e}")
        super().done(result)


class QrLoginWorker(QThread):
    show_url = pyqtSignal(str)
    error = pyqtSignal(str)
    success = pyqtSignal(str, int, str, str)  # username, api_id, api_hash, session_string

    def __init__(self, api_id: int, api_hash: str, parent=None) -> None:
        super().__init__(parent)
        self.api_id = api_id
        self.api_hash = api_hash
        self._stopping = False
        self._loop = None
        self._task = None
        self._client = None

    def stop(self):
        self._stopping = True
        try:
            if self._loop is not None:
                if self._task is not None:
                    self._loop.call_soon_threadsafe(self._task.cancel)
                if getattr(self, '_client', None) is not None:
                    import asyncio as _asyncio
                    self._loop.call_soon_threadsafe(lambda: _asyncio.ensure_future(self._client.disconnect()))
        except Exception:
            pass

    def run(self) -> None:
        import asyncio
        async def do_login():
            try:
                session = StringSession()
                self._client = TelegramClient(session, self.api_id, self.api_hash)
                await self._client.connect()
                qr = await self._client.qr_login()
                self.show_url.emit(qr.url)
                me = await qr.wait()
                username = f"@{me.username}" if getattr(me, 'username', None) else (me.first_name or "")
                session_str = self._client.session.save()
                self.success.emit(username, self.api_id, self.api_hash, session_str)
            except asyncio.CancelledError:
                return
            except Exception as e:
                self.error.emit(str(e))
            finally:
                try:
                    if self._client is not None:
                        await self._client.disconnect()
                except Exception:
                    pass
        loop = None
        try:
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            self._task = loop.create_task(do_login())
            loop.run_until_complete(self._task)
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                if loop is not None:
                    loop.close()
            except Exception:
                pass
            self._loop = None
            self._task = None
            self._client = None


class QrLoginDialog(QDialog):
    login_success = pyqtSignal(str, int, str, str)
    def __init__(self, parent, api_id: int, api_hash: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(parent._("qr_title"))
        try:
            self.setWindowIcon(parent.windowIcon())
        except Exception:
            pass
        self.setModal(True)
        self.resize(360, 420)
        v = QVBoxLayout(self)
        self.info = QLabel(parent._("qr_instructions"), self)
        self.info.setWordWrap(True)
        v.addWidget(self.info)
        self.qr_label = QLabel("", self)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.qr_label, 1)
        btns = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btns.addStretch(1)
        btns.addWidget(self.cancel_btn)
        v.addLayout(btns)
        if not QRCODE_AVAILABLE:
            self.qr_label.setText("qrcode library not installed. Install: pip install qrcode[pil]")
        self.worker = QrLoginWorker(api_id, api_hash, self)
        self.worker.show_url.connect(self._on_show_url)
        self.worker.error.connect(self._on_error)
        self.worker.success.connect(self._on_success)
        try:
            self.finished.connect(self._cleanup_worker)
        except Exception:
            pass
        self.worker.start()

    def _cleanup_worker(self, *_args) -> None:
        try:
            if hasattr(self, 'worker') and self.worker is not None:
                self.worker.stop()
                if self.worker.isRunning():
                    self.worker.wait(5000)
        except Exception:
            pass

    def reject(self) -> None:
        self._cleanup_worker()
        super().reject()

    def closeEvent(self, event) -> None:
        self._cleanup_worker()
        super().closeEvent(event)

    def _on_show_url(self, url: str) -> None:
        if QRCODE_AVAILABLE:
            try:
                img = qrcode.make(url)
                buf = BytesIO()
                img.save(buf, format='PNG')
                qimg = QImage.fromData(buf.getvalue(), 'PNG')
                pix = QPixmap.fromImage(qimg)
                self.qr_label.setPixmap(pix.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            except Exception as e:
                self.qr_label.setText(f"Failed to render QR: {e}\nURL: {url}")
        else:
            self.qr_label.setText(url)

    def _on_error(self, msg: str) -> None:
        QMessageBox.critical(self, "QR Login Error", msg)
        self.reject()

    def _on_success(self, username: str, api_id: int, api_hash: str, session_string: str) -> None:
        self.login_success.emit(username, api_id, api_hash, session_string)
        self.accept()


class PhoneLoginWorker(QThread):
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    need_code = pyqtSignal()
    need_password = pyqtSignal()
    success = pyqtSignal(str, int, str, str)  # username, api_id, api_hash, session_string

    def __init__(self, api_id: int, api_hash: str, phone: str, parent=None) -> None:
        super().__init__(parent)
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self._loop = None
        self._task = None
        self._client = None
        self._code_future = None
        self._pass_future = None

    def stop(self) -> None:
        try:
            if self._loop is not None:
                if self._task is not None:
                    self._loop.call_soon_threadsafe(self._task.cancel)
                if getattr(self, '_client', None) is not None:
                    import asyncio as _asyncio
                    self._loop.call_soon_threadsafe(lambda: _asyncio.ensure_future(self._client.disconnect()))
        except Exception:
            pass

    def provide_code(self, code: str) -> None:
        try:
            if self._loop and self._code_future and not self._code_future.done():
                self._loop.call_soon_threadsafe(lambda: self._code_future.set_result(code.strip()))
        except Exception:
            pass

    def provide_password(self, password: str) -> None:
        try:
            if self._loop and self._pass_future and not self._pass_future.done():
                self._loop.call_soon_threadsafe(lambda: self._pass_future.set_result(password))
        except Exception:
            pass

    def run(self) -> None:
        import asyncio
        async def do_login():
            from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
            try:
                self.status.emit('Connecting...')
                self._client = TelegramClient(StringSession(), self.api_id, self.api_hash)
                await self._client.connect()
                self.status.emit('Sending code...')
                await self._client.send_code_request(self.phone)
                self.need_code.emit()
                loop = asyncio.get_running_loop()
                self._code_future = loop.create_future()
                code = await self._code_future
                try:
                    await self._client.sign_in(self.phone, code)
                except SessionPasswordNeededError:
                    self.need_password.emit()
                    self._pass_future = loop.create_future()
                    password = await self._pass_future
                    await self._client.sign_in(password=password)
                except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
                    raise e
                me = await self._client.get_me()
                username = f"@{me.username}" if getattr(me, 'username', None) else (me.first_name or '')
                session_str = self._client.session.save()
                self.success.emit(username, self.api_id, self.api_hash, session_str)
            except asyncio.CancelledError:
                return
            except Exception as e:
                self.error.emit(str(e))
            finally:
                try:
                    if self._client is not None:
                        await self._client.disconnect()
                except Exception:
                    pass
        loop = None
        try:
            import asyncio as _asyncio
            loop = _asyncio.new_event_loop()
            self._loop = loop
            _asyncio.set_event_loop(loop)
            from telethon import TelegramClient
            from telethon.sessions import StringSession
            self._task = loop.create_task(do_login())
            loop.run_until_complete(self._task)
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
        except Exception as e:
            try:
                self.error.emit(str(e))
            except Exception:
                pass
        finally:
            try:
                if loop is not None:
                    loop.close()
            except Exception:
                pass
            self._loop = None
            self._task = None
            self._client = None


class PhoneLoginDialog(QDialog):
    login_success = pyqtSignal(str, int, str, str)
    def __init__(self, parent, api_id: int, api_hash: str, phone: str) -> None:
        super().__init__(parent)
        self.setWindowTitle('Login')
        try:
            self.setWindowIcon(parent.windowIcon())
        except Exception:
            pass
        self.setModal(True)
        self.resize(360, 220)
        v = QVBoxLayout(self)
        self.info = QLabel(f'Sending code to {phone}...', self)
        self.info.setWordWrap(True)
        v.addWidget(self.info)
        # Code input
        self.code_label = QLabel('Code:', self)
        self.code_input = QLineEdit(self)
        self.code_input.setMaxLength(10)
        try:
            self.code_input.setPlaceholderText('Enter the code from Telegram')
        except Exception:
            pass
        self.code_btn = QPushButton('Submit Code', self)
        self.code_btn.clicked.connect(self._submit_code)
        v.addWidget(self.code_label)
        v.addWidget(self.code_input)
        v.addWidget(self.code_btn)
        # Password input (2FA)
        self.pw_label = QLabel('Password:', self)
        self.pw_input = QLineEdit(self)
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        try:
            self.pw_input.setPlaceholderText('Two-step verification password (if enabled)')
        except Exception:
            pass
        self.pw_btn = QPushButton('Submit Password', self)
        self.pw_btn.clicked.connect(self._submit_password)
        v.addWidget(self.pw_label)
        v.addWidget(self.pw_input)
        v.addWidget(self.pw_btn)
        self._toggle_pw(False)
        self.worker = PhoneLoginWorker(api_id, api_hash, phone, self)
        self.worker.status.connect(self._on_status)
        self.worker.error.connect(self._on_error)
        self.worker.need_code.connect(lambda: self._toggle_code(True))
        self.worker.need_password.connect(lambda: self._toggle_pw(True))
        self.worker.success.connect(self._on_success)
        try:
            self.finished.connect(self._cleanup_worker)
        except Exception:
            pass
        self.worker.start()

    def _cleanup_worker(self, *_args) -> None:
        try:
            if hasattr(self, 'worker') and self.worker is not None:
                try:
                    self.worker.stop()
                except Exception:
                    pass
                if self.worker.isRunning():
                    self.worker.wait(5000)
        except Exception:
            pass

    def reject(self) -> None:
        self._cleanup_worker()
        super().reject()

    def closeEvent(self, event) -> None:
        self._cleanup_worker()
        super().closeEvent(event)

    def _toggle_code(self, show: bool) -> None:
        self.code_label.setVisible(show)
        self.code_input.setVisible(show)
        self.code_btn.setVisible(show)

    def _toggle_pw(self, show: bool) -> None:
        self.pw_label.setVisible(show)
        self.pw_input.setVisible(show)
        self.pw_btn.setVisible(show)

    def _on_status(self, msg: str) -> None:
        self.info.setText(msg)

    def _on_error(self, msg: str) -> None:
        QMessageBox.critical(self, 'Login Error', msg)
        self.reject()

    def _on_success(self, username: str, api_id: int, api_hash: str, session_string: str) -> None:
        self.login_success.emit(username, api_id, api_hash, session_string)
        self.accept()

    def _submit_code(self) -> None:
        code = self.code_input.text().strip()
        if code:
            try:
                self.worker.provide_code(code)
                self._toggle_code(False)
                self.info.setText('Verifying code...')
            except Exception:
                pass

    def _submit_password(self) -> None:
        pw = self.pw_input.text()
        if pw:
            try:
                self.worker.provide_password(pw)
                self._toggle_pw(False)
                self.info.setText('Verifying password...')
            except Exception:
                pass


# --- Background Workers ---

class UpdateCheckWorker(QThread):
    """
    Checks for a new version of the application on GitHub in the background.
    """
    update_found = pyqtSignal(str, str, str)  # new_version, release_notes, release_url
    no_update_found = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    @staticmethod
    def _parse_version(version_str: str) -> tuple:
        """Helper to parse version strings like 'v2.9.0' or '2.9.0' into comparable tuples."""
        try:
            if version_str.startswith('v'):
                version_str = version_str[1:]
            return tuple(map(int, (version_str.split('.') + ['0']*3)[:3])) # Pad with 0s for safety
        except (ValueError, AttributeError):
            return (0, 0, 0)

    def run(self) -> None:
        try:
            import urllib.request
            import json

            req = urllib.request.Request(
                UPDATE_CHECK_URL,
                headers={'User-Agent': f'{APP_NAME}/{APP_VERSION}'}
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status != 200:
                    self.error.emit(f"HTTP Status {response.status}")
                    return
                data = json.loads(response.read().decode('utf-8'))

            latest_version_tag = data.get('tag_name')
            if not latest_version_tag:
                self.error.emit("'tag_name' not found in API response.")
                return

            current_v_tuple = self._parse_version(APP_VERSION)
            latest_v_tuple = self._parse_version(latest_version_tag)
            
            logger.info(f"Update check: Current version={current_v_tuple}, Latest version={latest_v_tuple}")

            if latest_v_tuple > current_v_tuple:
                logger.info(f"Newer version found: {latest_version_tag}")
                release_notes = data.get('body', 'No release notes provided.')
                release_url = data.get('html_url', 'https://github.com/ozodesigner/Telegram-Media-Downloader/releases')
                self.update_found.emit(latest_version_tag, release_notes, release_url)
            else:
                self.no_update_found.emit()

        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    log = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, api_id: int, api_hash: str, session_string: str, target: str, download_dir: str, filters: dict, skip_existing: bool, parent=None) -> None:
        super().__init__(parent)
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.target = target
        self.download_dir = download_dir
        self.filters = filters
        self.skip_existing = skip_existing
        self._stopping = False
        self._loop = None
        self._task = None
        self._client = None
        self._current_file: str = ""
        self._file_total: int = 0
        self._file_start_t: float = 0.0

    def stop(self):
        self._stopping = True
        try:
            if self._loop is not None:
                if self._task is not None:
                    self._loop.call_soon_threadsafe(self._task.cancel)
                if getattr(self, '_client', None) is not None:
                    import asyncio as _asyncio
                    self._loop.call_soon_threadsafe(lambda: _asyncio.ensure_future(self._client.disconnect()))
        except Exception:
            pass

    def run(self) -> None:
        import asyncio, time
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        from telethon.errors import ChannelInvalidError, UsernameInvalidError, UsernameNotOccupiedError
        from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo, DocumentAttributeSticker, DocumentAttributeAnimated, DocumentAttributeFilename

        def _progress_cb(current: int, total: int):
            try:
                pct = 0
                if total and total > 0:
                    pct = int((current / total) * 100)
                self.progress.emit(max(0, min(100, pct)))
                try:
                    elapsed = max(1e-3, time.time() - self._file_start_t)
                    bps = float(current) / float(elapsed)
                    def _fmt_size(n: int) -> str:
                        units = ['B','KB','MB','GB','TB']
                        f = float(n)
                        i = 0
                        while f >= 1024.0 and i < len(units)-1:
                            f /= 1024.0
                            i += 1
                        return f"{f:.1f} {units[i]}"
                    speed = f"{_fmt_size(int(bps))}/s"
                    cur_sz = _fmt_size(int(current))
                    tot_sz = _fmt_size(int(total)) if (total and total > 0) else '?'
                except Exception:
                    speed = "?"
                    cur_sz = "?"
                    tot_sz = "?"
                try:
                    import os as _os
                    name = _os.path.basename(self._current_file) if getattr(self, '_current_file', '') else ''
                except Exception:
                    name = ''
                if name:
                    self.status.emit(f"{name} - {pct}% - {cur_sz}/{tot_sz} - {speed}")
                else:
                    self.status.emit(f"{pct}% - {cur_sz}/{tot_sz} - {speed}")
                if self._stopping:
                    import asyncio as _asyncio
                    raise _asyncio.CancelledError("Stopped by user")
            except Exception:
                pass

        def _match_filters(msg) -> bool:
            try:
                if not msg or not msg.media:
                    return False
                if self.filters.get('sticker') and getattr(msg, 'sticker', None):
                    return True
                if self.filters.get('photo') and getattr(msg, 'photo', None):
                    return True
                if self.filters.get('voice') and getattr(msg, 'voice', None):
                    return True
                doc = getattr(msg, 'document', None)
                if doc:
                    mime = getattr(doc, 'mime_type', '') or ''
                    attrs = getattr(doc, 'attributes', []) or []
                    if self.filters.get('sticker') and any(isinstance(a, DocumentAttributeSticker) for a in attrs):
                        return True
                    if self.filters.get('video') and (mime.startswith('video/') and not any(getattr(a, 'round_message', False) for a in attrs) or any(isinstance(a, DocumentAttributeVideo) and not getattr(a, 'round_message', False) for a in attrs)):
                        return True
                    if self.filters.get('audio') and mime.startswith('audio/'):
                        return True
                    if self.filters.get('voice') and any(getattr(a, 'voice', False) for a in attrs):
                        return True
                    if self.filters.get('gif') and (mime == 'image/gif' or any(isinstance(a, DocumentAttributeAnimated) for a in attrs)):
                        return True
                    if self.filters.get('video_note') and any(isinstance(a, DocumentAttributeVideo) and getattr(a, 'round_message', False) for a in attrs):
                        return True
                    if self.filters.get('document') and not (mime.startswith('video/') or mime.startswith('audio/') or mime == 'image/gif'):
                        return True
                return False
            except Exception:
                return False

        async def _resolve_target(client, t: str):
            try:
                #MODIFIED: Handle integer IDs directly
                if t.lstrip('-').isdigit():
                    return await client.get_entity(int(t))
                if t.startswith('http') or t.startswith('t.me/') or 't.me/' in t:
                    return await client.get_entity(t)
                if t.startswith('@'):
                    return await client.get_entity(t)
                return await client.get_entity(t)
            except (ChannelInvalidError, UsernameInvalidError, UsernameNotOccupiedError):
                raise

        async def _run():
            self._client = None
            try:
                self.status.emit('Connecting...')
                self._client = TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash)
                await self._client.connect()
                ent = await _resolve_target(self._client, self.target)
                self.status.emit('Downloading...')
                count = 0

                def _sanitize(name: str) -> str:
                    bad = '<>:"/\\|?*\n\r\t'
                    for ch in bad:
                        name = name.replace(ch, '_')
                    return name.strip() or 'file'

                def _ext_from_mime(mime: str) -> str:
                    if not mime:
                        return ''
                    m = mime.lower()
                    if m == 'image/jpeg' or m == 'image/jpg': return '.jpg'
                    if m.startswith('image/'): return '.' + m.split('/', 1)[1]
                    if m.startswith('video/'): return '.' + m.split('/', 1)[1]
                    if m.startswith('audio/'): return '.' + m.split('/', 1)[1]
                    if m == 'application/x-tgsticker': return '.tgs'
                    if m == 'image/webp': return '.webp'
                    return '.bin'

                def _unique_path(p: str) -> str:
                    base, ext = os.path.splitext(p)
                    i = 1
                    cand = p
                    while os.path.exists(cand):
                        cand = f"{base} ({i}){ext}"
                        i += 1
                    return cand

                def _fmt_size(n: int | None) -> str:
                    try:
                        if n is None: return '?'
                        f = float(n)
                        units = ['B','KB','MB','GB','TB']
                        i = 0
                        while f >= 1024.0 and i < len(units)-1:
                            f /= 1024.0
                            i += 1
                        return f"{f:.1f} {units[i]}"
                    except Exception:
                        return '?'

                def _guess_path_and_size(msg) -> tuple[str, int | None]:
                    doc = getattr(msg, 'document', None)
                    if doc is not None:
                        fname = None
                        for a in getattr(doc, 'attributes', []) or []:
                            if isinstance(a, DocumentAttributeFilename):
                                fname = a.file_name
                                break
                        if not fname:
                            mime = getattr(doc, 'mime_type', '') or ''
                            ext = _ext_from_mime(mime)
                            if any(isinstance(a, DocumentAttributeSticker) for a in getattr(doc, 'attributes', []) or []): prefix = 'sticker'
                            elif any(isinstance(a, DocumentAttributeVideo) and getattr(a, 'round_message', False) for a in getattr(doc, 'attributes', []) or []): prefix = 'videonote'
                            elif any(isinstance(a, DocumentAttributeVideo) for a in getattr(doc, 'attributes', []) or []): prefix = 'video'
                            elif any(isinstance(a, DocumentAttributeAudio) for a in getattr(doc, 'attributes', []) or []): prefix = 'audio'
                            elif any(isinstance(a, DocumentAttributeAnimated) for a in getattr(doc, 'attributes', []) or []): prefix = 'gif'
                            else: prefix = 'document'
                            fname = f"{prefix}_{msg.id}{ext}"
                        size = getattr(doc, 'size', None)
                        return os.path.join(self.download_dir, _sanitize(fname)), size
                    if getattr(msg, 'photo', None) is not None:
                        return os.path.join(self.download_dir, _sanitize(f"photo_{msg.id}.jpg")), None
                    if getattr(msg, 'voice', None):
                        return os.path.join(self.download_dir, _sanitize(f"voice_{msg.id}.ogg")), None
                    return os.path.join(self.download_dir, _sanitize(f"media_{msg.id}")), None

                async for m in self._client.iter_messages(ent, reverse=True):
                    if self._stopping: break
                    if not _match_filters(m): continue
                    try:
                        out_path, expected_size = _guess_path_and_size(m)
                        if self.skip_existing and os.path.exists(out_path):
                            try:
                                if expected_size is None or os.path.getsize(out_path) == int(expected_size):
                                    self.log.emit(f"[SKIP] Exists: {out_path}")
                                    continue
                                else:
                                    new_path = _unique_path(out_path)
                                    self.log.emit(f"[WARN] Name exists with different size. Saving as: {new_path}")
                                    out_path = new_path
                            except Exception: pass
                        try:
                            self._current_file = out_path
                            self._file_total = int(expected_size) if (expected_size is not None) else 0
                            self._file_start_t = time.time()
                            try:
                                self.status.emit(f"Starting: {os.path.basename(out_path)} (total {_fmt_size(expected_size)})")
                            except Exception: pass
                            path = await self._client.download_media(m, file=out_path, progress_callback=_progress_cb)
                        except asyncio.CancelledError:
                            self.log.emit("[STOP] Cancelled current download")
                            break
                        if path:
                            count += 1
                            self.log.emit(f"[OK] Saved: {path}")
                            try:
                                self.status.emit(f"Saved: {os.path.basename(path)}")
                            except Exception: pass
                        else:
                            self.log.emit("[SKIP] No file for this message")
                    except Exception as e:
                        if self._stopping:
                            self.log.emit("[STOP] Stopping...")
                            break
                        self.log.emit(f"[ERROR] {e}")
                    if self._stopping: break
                if self._stopping:
                    self.finished_signal.emit(False, 'Stopped by user')
                else:
                    self.finished_signal.emit(True, '')
            except asyncio.CancelledError:
                self.finished_signal.emit(False, 'Stopped by user')
            except Exception as e:
                self.finished_signal.emit(False, str(e))
            finally:
                try:
                    if self._client is not None:
                        await self._client.disconnect()
                except Exception: pass

        try:
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            self._task = loop.create_task(_run())
            loop.run_until_complete(self._task)
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception: pass
        except asyncio.CancelledError:
            try: self.finished_signal.emit(False, 'Stopped by user')
            except Exception: pass
        except Exception as e:
            try: self.finished_signal.emit(False, str(e))
            except Exception: pass
        finally:
            try: loop.close()
            except Exception: pass
            self._loop = None
            self._task = None
            self._client = None


class FetchChatsWorker(QThread):
    chats_fetched = pyqtSignal(list)
    error = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, api_id: int, api_hash: str, session_string: str, parent=None) -> None:
        super().__init__(parent)
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self._loop = None
        self._client = None

    def stop(self):
        try:
            if self._loop and self._client:
                import asyncio
                self._loop.call_soon_threadsafe(lambda: asyncio.ensure_future(self._client.disconnect()))
        except Exception:
            pass

    def run(self) -> None:
        import asyncio
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        async def _run():
            self._client = None
            try:
                self._client = TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash)
                await self._client.connect()

                dialogs = await self._client.get_dialogs(limit=150)
                chat_list = []
                for dialog in dialogs:
                    title = dialog.name
                    try:
                        if hasattr(dialog.entity, 'participants_count') and dialog.entity.participants_count:
                             title = f"{title} ({dialog.entity.participants_count} members)"
                        elif hasattr(dialog.entity, 'subscribers') and dialog.entity.subscribers:
                             title = f"{title} ({dialog.entity.subscribers} subs)"
                    except Exception:
                        pass
                    chat_list.append((title, dialog.id))
                self.chats_fetched.emit(chat_list)
            except Exception as e:
                self.error.emit(str(e))
            finally:
                if self._client:
                    await self._client.disconnect()

        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(_run())
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished_signal.emit()
            if self._loop:
                self._loop.close()


class FetchProfileWorker(QThread):
    profile_fetched = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, api_id: int, api_hash: str, session_string: str, chat_id: int, parent=None) -> None:
        super().__init__(parent)
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.chat_id = chat_id
        self._loop = None
        self._client = None

    def stop(self):
        try:
            if self._loop and self._client:
                import asyncio
                self._loop.call_soon_threadsafe(lambda: asyncio.ensure_future(self._client.disconnect()))
        except Exception:
            pass

    def run(self) -> None:
        import asyncio
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        from telethon.tl.functions.messages import GetFullChatRequest
        from telethon.tl.functions.channels import GetFullChannelRequest
        from telethon.tl.functions.users import GetFullUserRequest
        
        async def _run():
            self._client = None
            try:
                self._client = TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash)
                await self._client.connect()
                
                entity = await self._client.get_entity(self.chat_id)
                full_entity = None
                description = ""
                
                if isinstance(entity, User):
                    full_entity = await self._client(GetFullUserRequest(entity))
                    description = full_entity.about or ""
                elif isinstance(entity, Channel):
                    full_entity = await self._client(GetFullChannelRequest(entity))
                    description = full_entity.full_chat.about or ""
                elif isinstance(entity, Chat):
                    full_entity = await self._client(GetFullChatRequest(entity.id))
                    description = full_entity.full_chat.about or ""
                
                profile_data = {
                    "id": entity.id,
                    "title": getattr(entity, 'title', getattr(entity, 'first_name', 'N/A')),
                    "username": getattr(entity, 'username', None),
                    "type": entity.__class__.__name__,
                    "description": description,
                    "members_count": getattr(entity, 'participants_count', getattr(entity, 'subscribers', None)),
                    "photo_path": None
                }
                
                # Download profile photo
                temp_photo_path = os.path.join(USER_DATA_DIR, f"temp_profile_{entity.id}.jpg")
                path = await self._client.download_profile_photo(entity, file=temp_photo_path)
                if path:
                    profile_data["photo_path"] = path

                self.profile_fetched.emit(profile_data)

            except Exception as e:
                self.error.emit(str(e))
            finally:
                if self._client:
                    await self._client.disconnect()
        
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(_run())
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished_signal.emit()
            if self._loop:
                self._loop.close()


# --- Main Execution ---

def _install_global_handlers() -> None:
    def _excepthook(exc_type, exc, tb):
        try:
            import asyncio as _asyncio
            if isinstance(exc, _asyncio.CancelledError) or (isinstance(exc_type, type) and issubclass(exc_type, getattr(_asyncio, 'CancelledError', Exception))):
                return
        except Exception: pass
        try:
            logger.error("Unhandled exception", exc_info=(exc_type, exc, tb))
        except Exception: pass
        try:
            QMessageBox.critical(None, 'Error', f'{exc_type.__name__}: {exc}')
        except Exception: pass
    try: sys.excepthook = _excepthook
    except Exception: pass
    try:
        def _thread_excepthook(args):
            try:
                logger.error("Thread exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
            except Exception: pass
        threading.excepthook = _thread_excepthook
    except Exception: pass
    try:
        from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
        def _qt_handler(msg_type, context, message):
            try:
                if msg_type in (QtMsgType.QtInfoMsg,): logger.info(f'QT: {message}')
                elif msg_type in (QtMsgType.QtWarningMsg,): logger.warning(f'QT: {message}')
                elif msg_type in (QtMsgType.QtCriticalMsg,): logger.error(f'QT: {message}')
                elif msg_type in (QtMsgType.QtFatalMsg,): logger.critical(f'QT FATAL: {message}')
                else: logger.debug(f'QT: {message}')
            except Exception: pass
        qInstallMessageHandler(_qt_handler)
    except Exception: pass
    try:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        _fh_path = os.path.join(USER_DATA_DIR, 'crash.dump')
        _fh_file = open(_fh_path, 'a', encoding='utf-8')
        faulthandler.enable(file=_fh_file, all_threads=True)
    except Exception:
        try: faulthandler.enable(all_threads=True)
        except Exception: pass


def main() -> int:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass
    _install_global_handlers()
    app = QApplication(sys.argv)
    win = TelegramDownloaderGUI()
    try:
        app.aboutToQuit.connect(win.shutdown_cleanup)
    except Exception:
        pass
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
