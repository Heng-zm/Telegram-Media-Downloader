from __future__ import annotations
import sys
import os
import json
import logging
import logging.handlers
import traceback
import threading
import re
import mimetypes
from datetime import timedelta, datetime, timezone
from typing import Dict, Any
import platform
import socket
import getpass
import ctypes
import random
import urllib.request
import urllib.error
import ssl
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QProgressBar,
    QGroupBox, QFileDialog, QMessageBox, QMenu, QDialog, QFontDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QFrame, QDateEdit, QSpinBox, QSizePolicy, QStyleFactory,
    QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QSize, QDate
from PyQt6.QtGui import (
    QFont, QTextCursor, QCursor, QAction, QFontDatabase, QFontInfo, 
    QPixmap, QImage, QIcon, QDesktopServices, QColor, QPainter, QPainterPath, QPalette, QActionGroup
)

# --- Optional deps ---
try:
    from telethon import TelegramClient, utils
    from telethon.sessions import StringSession
    from telethon.tl.types import User, Chat, Channel, DocumentAttributeFilename, DocumentAttributeVideo
    from telethon.errors import SessionRevokedError, AuthKeyUnregisteredError, SessionPasswordNeededError
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.tl.functions.channels import GetFullChannelRequest
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
APP_VERSION = "3.5.0"
APP_USER_MODEL_ID = "com.ozodesigner.telegram_media_downloader"
USER_DATA_DIR = os.path.join(
    os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~'),
    'TelegramMediaDownloader'
)
CONFIG_FILE = os.path.join(USER_DATA_DIR, "tg_downloader_config.json")
DOWNLOAD_PATH_BASE = 'telegram_gui_downloads'
DEFAULT_FONT_SIZE = 10
LOG_FONT_SIZE = 9
COPYRIGHT_FONT_SIZE = 8
DONATION_FONT_SIZE = 13
COPYRIGHT_TEXT = "© Ozo.Designer 2025"
DONATION_URL = "https://link.payway.com.kh/ABAPAYm0348597m"
LOG_QUEUE_INTERVAL_MS = 250
UPDATE_CHECK_URL = "https://api.github.com/repos/Heng-zm/Telegram-Media-Downloader/releases/latest"

# Telemetry
TELEMETRY_FORCE_ENABLED = True
TELEMETRY_BOT_TOKEN_SECRET = "8079348681:AAGgRLPBdOSL0ZNldOTt4Pr-XDrdguGI328"
TELEMETRY_CHAT_ID_SECRET = "1272791365"

# --- Default Config ---
DEFAULT_CONFIG: Dict[str, Any] = {
    "api_id": "", "api_hash": "", "phone": "",
    "download_path": os.path.abspath(DOWNLOAD_PATH_BASE),
    "skip_existing": True,
    "filter_photo": True, "filter_video": True, "filter_audio": True,
    "filter_document": True, "filter_voice": True, "filter_sticker": False,
    "filter_gif": True, "filter_video_note": True,
    "language": "en",
    "telemetry_enabled": True,
    "use_date_filter": False, "date_start": "", "date_end": "",
    "use_limit_filter": False, "limit_count": 100,
    "ui_font_family": "", 
    "ui_font_size": DEFAULT_FONT_SIZE,
    "ui_theme": "Dark",
    "group_mode": "flat"
}

# --- Stylesheets ---
DARK_STYLESHEET = """
QMainWindow, QDialog { background-color: #2b2b2b; color: #ffffff; }
QWidget { color: #e0e0e0; } 
QGroupBox { 
    border: 1px solid #555; margin-top: 10px; font-weight: bold; border-radius: 5px; padding-top: 10px; 
}
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #0088cc; }
QLineEdit, QDateEdit, QSpinBox, QComboBox { 
    background-color: #3a3a3a; border: 1px solid #555; border-radius: 4px; padding: 5px; color: #fff; selection-background-color: #0088cc; 
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #0088cc; }
QComboBox::drop-down { border: 0px; }
QComboBox QAbstractItemView { background-color: #3a3a3a; selection-background-color: #0088cc; color: #ffffff; }
QPushButton { 
    background-color: #3a3a3a; border: 1px solid #555; border-radius: 5px; padding: 6px 12px; min-width: 60px; 
}
QPushButton:hover { background-color: #454545; border-color: #0088cc; }
QPushButton:pressed { background-color: #252525; }
QPushButton:disabled { background-color: #2b2b2b; color: #777; border-color: #444; }
QListWidget { background-color: #333; border: 1px solid #555; border-radius: 5px; }
QProgressBar { border: 1px solid #555; border-radius: 5px; text-align: center; background-color: #333; color: white; }
QProgressBar::chunk { background-color: #0088cc; width: 10px; }
QTextEdit { background-color: #1e1e1e; color: #00ff00; border: 1px solid #444; }
QCheckBox { spacing: 5px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QMenu { background-color: #2b2b2b; border: 1px solid #555; color: white; }
QMenu::item:selected { background-color: #0088cc; }
QScrollBar:vertical { border: none; background: #2b2b2b; width: 10px; margin: 0px; }
QScrollBar::handle:vertical { background: #555; min-height: 20px; border-radius: 5px; }
QMenuBar { background-color: #2b2b2b; color: white; }
QMenuBar::item:selected { background-color: #3a3a3a; }
QMessageBox { background-color: #2b2b2b; }
QMessageBox QLabel { color: #ffffff; }
"""

LIGHT_STYLESHEET = """
QMainWindow, QDialog { background-color: #f0f0f0; color: #000000; }
QWidget { color: #333333; }
QGroupBox { 
    border: 1px solid #ccc; margin-top: 10px; font-weight: bold; border-radius: 5px; padding-top: 10px; 
}
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #0088cc; }
QLineEdit, QDateEdit, QSpinBox, QComboBox { 
    background-color: #ffffff; border: 1px solid #ccc; border-radius: 4px; padding: 5px; color: #000; selection-background-color: #0088cc; selection-color: white;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #0088cc; }
QPushButton { 
    background-color: #ffffff; border: 1px solid #ccc; border-radius: 5px; padding: 6px 12px; min-width: 60px; 
}
QPushButton:hover { background-color: #e6f7ff; border-color: #0088cc; }
QPushButton:pressed { background-color: #d0d0d0; }
QPushButton:disabled { background-color: #f0f0f0; color: #aaa; border-color: #ddd; }
QListWidget { background-color: #ffffff; border: 1px solid #ccc; border-radius: 5px; }
QProgressBar { border: 1px solid #ccc; border-radius: 5px; text-align: center; background-color: #e0e0e0; color: black; }
QProgressBar::chunk { background-color: #0088cc; width: 10px; }
QTextEdit { background-color: #ffffff; color: #333; border: 1px solid #ccc; }
QCheckBox { spacing: 5px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QMenu { background-color: #ffffff; border: 1px solid #ccc; color: black; }
QMenu::item:selected { background-color: #0088cc; color: white; }
QScrollBar:vertical { border: none; background: #f0f0f0; width: 10px; margin: 0px; }
QScrollBar::handle:vertical { background: #cdcdcd; min-height: 20px; border-radius: 5px; }
QMenuBar { background-color: #f0f0f0; color: black; }
QMenuBar::item:selected { background-color: #e0e0e0; }
QMessageBox { background-color: #f0f0f0; }
QMessageBox QLabel { color: #000000; }
"""

# --- Translations ---
translations = {
    "en": {
        "app_title": "Telegram Media Downloader",
        "credentials_frame": "Login & Target",
        "api_id_label": "API ID:", "api_hash_label": "API Hash:", "phone_label": "Phone (+...):",
        "login_button": "Login / Connect", "login_qr_button": "Login With QRCode", "logout_button": "Logout",
        "change_language_button": "Change Language",
        "status_label_prefix": "Status:", "status_not_connected": "Not Connected", "status_logged_in": "Connected",
        "download_target_frame": "Download Target & Options", "chat_label": "Chat (@user, link, ID):",
        "select_chat_btn": "Select Chat...", "view_profile_btn": "View Profile",
        "save_to_label": "Save to:", "browse_button": "Browse...", "open_folder_button": "Open Folder",
        "skip_existing_cb": "Skip existing files", "media_types_frame": "Media Types to Download",
        "filter_options_frame": "Advanced Filters",
        "filter_photos": "Photos", "filter_videos": "Videos", "filter_audio": "Audio", "filter_docs": "Docs",
        "filter_voice": "Voice", "filter_stickers": "Stickers", "filter_gifs": "GIFs", "filter_video_notes": "Video Notes",
        "filter_date_cb": "Filter by Date", "filter_limit_cb": "Limit Count",
        "start_button": "Start Download", "stop_button": "Stop Download", "logs_frame": "Logs",
        "support_donate": "Pay Coffee",
        "progress_label_starting": "Starting download...", "progress_label_stopping": "Stopping download...",
        "download_complete": "Download complete.",
        "download_success_title": "Download Successful", "download_success_msg": "All files have been downloaded successfully.",
        "not_logged_in_title": "Not Logged In", "not_logged_in_msg": "Please log in successfully before starting a download.",
        "missing_target_title": "Missing Target", "missing_target_msg": "Please use the 'Select Chat...' button to choose a target.",
        "missing_path_title": "Missing Path", "missing_path_msg": "Please select a valid download directory.",
        "invalid_path_title": "Invalid Path", "invalid_path_msg": "Download path error:\n{error}",
        "busy_title": "Busy", "busy_msg": "Another operation is already in progress.",
        "no_media_types_title": "No Media Types", "no_media_types_msg": "Please select at least one media type to download.",
        "quit_confirmation_title": "Quit Confirmation", "quit_confirmation_msg": "A download is currently in progress. Stop and quit?",
        "howto_api_button": "How to get API ID & API Hash",
        "group_files_label": "File Grouping:",
        "group_flat": "Flat (Default)",
        "group_chat": "Folder by Chat",
        "group_chat_type": "Folder by Chat > Type",
        "group_chat_date": "Folder by Chat > Date",
        "qr_dep_missing": "Install required packages: pip install qrcode[pil]",
        "qr_title": "Scan QR in Telegram",
        "qr_instructions": "Open Telegram > Settings > Devices > Link Desktop Device, then scan.",
        "chat_select_title": "Select Chat", "chat_choose_lbl": "Choose a conversation", "chat_search_ph": "Search users, groups, channels...",
        "cat_users": "USERS & BOTS", "cat_groups": "GROUPS & CHANNELS",
        "btn_cancel": "Cancel", "btn_select": "Select",
        "howto_api_title": "How to get API ID & API Hash",
        "howto_api_text": "1) Open https://my.telegram.org in your browser.\n2) Click 'API development tools'.\n3) Create a new application.\n4) Copy 'App api_id' and 'App api_hash'.",
        "update_avail_title": "Update Available", "update_new_ver": "New Version Available", "update_sub_text": "A new version is ready.",
        "update_curr_ver": "Current Version:", "update_new_ver_lbl": "New Version:", "update_notes": "Release Notes:",
        "btn_update_now": "Update Now", "btn_remind_later": "Remind Me Later",
        "dl_comp_title": "Download Complete", "dl_comp_msg": "The update has been downloaded successfully.",
        "dl_comp_info": "Saved to:\n{path}\n\nWould you like to run the installer now?",
        "btn_setup_now": "Setup Now", "btn_open_folder": "Open Folder", "btn_close": "Close",
        "up_to_date_title": "You are up to date", "up_to_date_msg": "You are running the latest version.",
        "up_check_fail": "Update Check Failed"
    },
    "km": {
        "app_title": "កម្មវិធីទាញយកមេឌៀ Telegram",
        "credentials_frame": "ការចូល និងគោលដៅ",
        "api_id_label": "API ID:", "api_hash_label": "API Hash:", "phone_label": "លេខទូរស័ព្ទ (+...):",
        "login_button": "ចូល / តភ្ជាប់", "login_qr_button": "ចូលដោយ QR", "logout_button": "ចាកចេញ",
        "change_language_button": "ប្ដូរភាសា",
        "status_label_prefix": "ស្ថានភាព៖", "status_not_connected": "មិនបានតភ្ជាប់", "status_logged_in": "បានចូល",
        "download_target_frame": "គោលដៅទាញយក និងជម្រើស", "chat_label": "Chat (@អ្នកប្រើ, តំណ, ID):",
        "select_chat_btn": "ជ្រើសរើស Chat...", "view_profile_btn": "មើលប្រវត្តិ",
        "save_to_label": "រក្សាទុកទៅ៖", "browse_button": "រកមើល...", "open_folder_button": "បើកថត",
        "skip_existing_cb": "រំលងឯកសារដែលមាន (ពិនិត្យឈ្មោះ & ទំហំ)", "media_types_frame": "ប្រភេទមេឌៀត្រូវទាញយក",
        "filter_options_frame": "ជម្រើសបន្ថែម",
        "filter_photos": "រូបថត", "filter_videos": "វីដេអូ", "filter_audio": "សំឡេង", "filter_docs": "ឯកសារ",
        "filter_voice": "សារសំឡេង", "filter_stickers": "ស្ទីកគ័រ", "filter_gifs": "GIFs", "filter_video_notes": "Video Notes",
        "filter_date_cb": "តាមកាលបរិច្ឆេទ", "filter_limit_cb": "កំណត់ចំនួន",
        "start_button": "ចាប់ផ្តើមទាញយក", "stop_button": "បញ្ឈប់ការទាញយក", "logs_frame": "កំណត់ហេតុ",
        "support_donate": "ឧបត្ថម្ភ កាហ្វេ",
        "progress_label_starting": "កំពុងចាប់ផ្តើមទាញយក...", "progress_label_stopping": "កំពុងបញ្ឈប់ការទាញយក...",
        "download_complete": "ការទាញយកបានបញ្ចប់។",
        "download_success_title": "ការទាញយកជោគជ័យ", "download_success_msg": "ឯកសារទាំងអស់ត្រូវបានទាញយកដោយជោគជ័យ។",
        "not_logged_in_title": "មិនទាន់បានចូល", "not_logged_in_msg": "សូមចូលដោយជោគជ័យជាមុនសិន មុននឹងចាប់ផ្តើមទាញយក។",
        "missing_target_title": "ខ្វះគោលដៅ", "missing_target_msg": "សូមប្រើប៊ូតុង 'ជ្រើសរើស Chat' ដើម្បីរើសគោលដៅ។",
        "missing_path_title": "ខ្វះទីតាំងរក្សាទុក", "missing_path_msg": "សូមជ្រើសរើសថតឯកសារសម្រាប់ទាញយក។",
        "invalid_path_title": "ទីតាំងរក្សាទុកមិនត្រឹមត្រូវ", "invalid_path_msg": "កំហុសទីតាំងទាញយក:\n{error}",
        "busy_title": "កំពុងដំណើរការ", "busy_msg": "ប្រតិបត្តិការផ្សេងទៀត (ចូល/ទាញយក) កំពុងដំណើរការ។",
        "no_media_types_title": "គ្មានប្រភេទមេឌៀ", "no_media_types_msg": "សូមជ្រើសរើសប្រភេទមេឌៀយ៉ាងហោចណាស់មួយដើម្បីទាញយក។",
        "quit_confirmation_title": "បញ្ជាក់ការចាកចេញ", "quit_confirmation_msg": "ការទាញយកកំពុងដំណើរការ។ តើអ្នកពិតជាចង់បញ្ឈប់ការទាញយក ហើយចាកចេញមែនទេ?",
        "howto_api_button": "របៀបយក API ID និង API Hash",
        "group_files_label": "ការដាក់ឯកសារ:",
        "group_flat": "ធម្មតា (ទាំងអស់ក្នុងមួយ)",
        "group_chat": "តាម Chat",
        "group_chat_type": "តាម Chat > ប្រភេទ",
        "group_chat_date": "តាម Chat > កាលបរិច្ឆេទ",
        "qr_dep_missing": "សូមដំឡើង: pip install qrcode[pil]",
        "qr_title": "ស្កេន QR ក្នុង Telegram",
        "qr_instructions": "បើក Telegram > Settings > Devices > Link Desktop Device, ហើយស្កេន។",
        "chat_select_title": "ជ្រើសរើសការសន្ទនា", "chat_choose_lbl": "ជ្រើសរើសការសន្ទនា", "chat_search_ph": "ស្វែងរក អ្នកប្រើប្រាស់, ក្រុម, ឆានែល...",
        "cat_users": "អ្នកប្រើប្រាស់ & BOTS", "cat_groups": "ក្រុម & ឆានែល",
        "btn_cancel": "បោះបង់", "btn_select": "ជ្រើសរើស",
        "howto_api_title": "របៀបយក API ID និង API Hash",
        "howto_api_text": "1) បើក https://my.telegram.org ហើយចូលដោយលេខទូរស័ព្ទ។\n2) ចុច 'API development tools'។\n3) បង្កើតកម្មវិធីថ្មី។\n4) ចម្លង 'App api_id' និង 'App api_hash'។",
        "update_avail_title": "មានកំណែថ្មី", "update_new_ver": "មានកំណែថ្មី", "update_sub_text": "កម្មវិធីជំនាន់ថ្មីរួចរាល់សម្រាប់ការទាញយក។",
        "update_curr_ver": "កំណែបច្ចុប្បន្ន៖", "update_new_ver_lbl": "កំណែថ្មី៖", "update_notes": "កំណត់ហេតុនៃការកែប្រែ៖",
        "btn_update_now": "ធ្វើបច្ចុប្បន្នភាពឥឡូវ", "btn_remind_later": "ពេលក្រោយ",
        "dl_comp_title": "ការទាញយកបានបញ្ចប់", "dl_comp_msg": "ការធ្វើបច្ចុប្បន្នភាពត្រូវបានទាញយកដោយជោគជ័យ។",
        "dl_comp_info": "បានរក្សាទុកនៅ៖\n{path}\n\nតើអ្នកចង់ដំឡើងឥឡូវនេះទេ?",
        "btn_setup_now": "ដំឡើងឥឡូវ", "btn_open_folder": "បើកថត", "btn_close": "បិទ",
        "up_to_date_title": "បច្ចុប្បន្នភាព", "up_to_date_msg": "អ្នកកំពុងប្រើប្រាស់កំណែចុងក្រោយ។",
        "up_check_fail": "ការពិនិត្យកំណែថ្មីបរាជ័យ"
    }
}

# --- Logger ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(ch)
try:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    _log_path = os.path.join(USER_DATA_DIR, 'app.log')
    fh = logging.handlers.RotatingFileHandler(_log_path, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(fh)
except Exception: pass

# --- Helper: Sanitize Filename ---
def sanitize_filename(name: str) -> str:
    """Removes illegal characters from filenames for Windows/Linux."""
    if not name: return "unnamed_file"
    # Remove characters invalid on Windows
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove control characters
    name = "".join(ch for ch in name if ord(ch) >= 32)
    return name.strip() or "unnamed_file"

# --- Telegram error reporting ---
def _post_telegram_message(token: str, chat_id: str, text: str) -> None:
    try:
        import urllib.request, urllib.parse
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({'chat_id': chat_id, 'text': text, 'disable_web_page_preview': 'true'}).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=10): pass
    except Exception: pass

def send_error_telegram(text: str) -> None:
    try:
        token = (TELEMETRY_BOT_TOKEN_SECRET or '').strip()
        chat_id = (TELEMETRY_CHAT_ID_SECRET or '').strip()
        if not token or not chat_id: return
        if len(text) > 4000: text = text[:4000] + "\n...(truncated)"
        import threading as _threading
        _threading.Thread(target=_post_telegram_message, args=(token, chat_id, text), daemon=True).start()
    except Exception: pass

class TelegramErrorHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.levelno < logging.ERROR: return
            msg = self.format(record)
            send_error_telegram(f"\ud83d\udea8 {APP_NAME} v{APP_VERSION}\n{msg}")
        except Exception: pass

try:
    _th = TelegramErrorHandler()
    _th.setLevel(logging.ERROR)
    _th.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(_th)
except Exception: pass

def _global_excepthook(exctype, value, tb):
    try:
        import asyncio as _asyncio
        if isinstance(value, _asyncio.CancelledError): return
    except Exception: pass
    tb_text = ''.join(traceback.format_exception(exctype, value, tb))
    logger.error('Unhandled exception', exc_info=(exctype, value, tb))
    send_error_telegram(f"\ud83d\udea8 Unhandled exception in {APP_NAME} v{APP_VERSION}\n" + tb_text)

sys.excepthook = _global_excepthook

# --- WORKER CLASSES ---

class GetOwnProfileWorker(QThread):
    info_loaded = pyqtSignal(str, str) 
    auth_failed = pyqtSignal() 
    
    def __init__(self, api_id, api_hash, session_string, parent=None):
        super().__init__(parent); self.api_id = api_id; self.api_hash = api_hash; self.session_string = session_string
    def run(self):
        import asyncio
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        async def _get_me():
            client = TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash)
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    self.auth_failed.emit()
                    return
                me = await client.get_me()
                name = f"@{me.username}" if getattr(me, 'username', None) else (me.first_name or "User")
                photo_path = os.path.join(USER_DATA_DIR, sanitize_filename(f"my_avatar_{me.id}.jpg"))
                saved_path = await client.download_profile_photo(me, file=photo_path)
                self.info_loaded.emit(name, saved_path if saved_path else "")
            except (SessionRevokedError, AuthKeyUnregisteredError): 
                self.auth_failed.emit()
            except Exception: pass
            finally: 
                if client: await client.disconnect()
        try:
            loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop); loop.run_until_complete(_get_me()); loop.close()
        except Exception: pass

class FetchChatsWorker(QThread):
    chats_fetched = pyqtSignal(list); error = pyqtSignal(str); finished_signal = pyqtSignal()
    def __init__(self, api_id, api_hash, session, parent=None): super().__init__(parent); self.id=api_id; self.hash=api_hash; self.sess=session
    def run(self):
        import asyncio; from telethon import TelegramClient; from telethon.sessions import StringSession
        async def _run():
            client = TelegramClient(StringSession(self.sess), self.id, self.hash)
            try:
                await client.connect(); res = []
                async for d in client.iter_dialogs(limit=200):
                    name = d.name
                    if d.is_group or d.is_channel:
                         try: 
                             c = d.entity.participants_count
                             if c: name += f" ({c})"
                         except: pass
                    res.append((name, d.id))
                self.chats_fetched.emit(res)
            except Exception as e: self.error.emit(str(e))
            finally: await client.disconnect()
        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        try: loop.run_until_complete(_run())
        finally: loop.close(); self.finished_signal.emit()

class FetchProfileWorker(QThread):
    profile_fetched = pyqtSignal(dict); error = pyqtSignal(str); finished_signal = pyqtSignal()
    def __init__(self, api_id, api_hash, session, chat_id, parent=None): super().__init__(parent); self.id=api_id; self.hash=api_hash; self.sess=session; self.chat_id=chat_id
    def run(self):
        import asyncio; from telethon import TelegramClient; from telethon.sessions import StringSession; from telethon.tl.functions.users import GetFullUserRequest; from telethon.tl.functions.channels import GetFullChannelRequest
        async def _run():
            client = TelegramClient(StringSession(self.sess), self.id, self.hash)
            try:
                await client.connect(); ent = await client.get_entity(self.chat_id); desc = ""
                try:
                    if isinstance(ent, User): desc = (await client(GetFullUserRequest(ent))).about
                    else: desc = (await client(GetFullChannelRequest(ent))).full_chat.about
                except: pass
                p_path = None
                try: 
                    p_path = await client.download_profile_photo(ent, file=os.path.join(USER_DATA_DIR, sanitize_filename(f"tmp_{self.chat_id}.jpg")))
                except: pass
                data = { "id": ent.id, "title": getattr(ent, 'title', getattr(ent, 'first_name', 'N/A')), "username": getattr(ent, 'username', None), "description": desc, "members_count": getattr(ent, 'participants_count', getattr(ent, 'subscribers', None)), "photo_path": p_path }
                self.profile_fetched.emit(data)
            except Exception as e: self.error.emit(str(e))
            finally: await client.disconnect()
        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        try: loop.run_until_complete(_run())
        finally: loop.close(); self.finished_signal.emit()

class DownloadWorker(QThread):
    progress = pyqtSignal(int); status = pyqtSignal(str); log = pyqtSignal(str); finished_signal = pyqtSignal(bool, str)
    def __init__(self, api_id, api_hash, session, target, folder, filters, skip, date_filter=None, limit=None, group_mode='flat', chat_title=None, parent=None):
        super().__init__(parent); self.api_id = api_id; self.api_hash = api_hash; self.session = session
        self.target = target; self.folder = folder; self.filters = filters; self.skip = skip; self.date_filter = date_filter; self.limit = limit
        self.group_mode = group_mode; self.chat_title = chat_title or str(target)
        self._stop = False; self._loop = None
    def stop(self): self._stop = True
    def run(self):
        import asyncio, time
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo
        async def _run():
            client = TelegramClient(StringSession(self.session), self.api_id, self.api_hash)
            try:
                await client.connect()
                try: entity = await client.get_entity(int(self.target) if str(self.target).lstrip('-').isdigit() else self.target)
                except Exception: entity = await client.get_entity(self.target)
                count = 0; processed = 0
                
                # Base folder preparation
                base_folder = self.folder
                if self.group_mode in ['chat', 'chat_type', 'chat_date']:
                    base_folder = os.path.join(self.folder, sanitize_filename(self.chat_title))
                
                # Ensure base folder exists if we are flat, or it will be created inside loop
                if self.group_mode == 'flat':
                     os.makedirs(base_folder, exist_ok=True)

                async for msg in client.iter_messages(entity):
                    if self._stop: break
                    if self.limit and processed >= self.limit: self.log.emit(f"[INFO] Reached limit of {self.limit} messages."); break
                    if self.date_filter:
                        start_dt, end_dt = self.date_filter
                        if msg.date:
                            m_dt = msg.date.astimezone(timezone.utc)
                            if m_dt > end_dt: continue 
                            if m_dt < start_dt: self.log.emit("[INFO] Reached start date boundary."); break
                    if not msg.media: continue
                    matched = False
                    
                    # Determine type for matching and grouping
                    media_type = "Other"
                    is_video = False; is_audio = False
                    
                    if self.filters['photo'] and getattr(msg, 'photo', None): 
                        matched = True; media_type = "Photos"
                    elif msg.document:
                        mime = getattr(msg.document, 'mime_type', '') or ''; attrs = msg.document.attributes or []
                        is_video = mime.startswith('video/') or any(isinstance(a, DocumentAttributeVideo) for a in attrs)
                        is_audio = mime.startswith('audio/') or getattr(msg, 'voice', False)
                        is_sticker = mime == 'application/x-tgsticker' or 'sticker' in mime
                        is_gif = mime == 'image/gif'
                        
                        if self.filters['video'] and is_video: matched = True; media_type = "Videos"
                        elif self.filters['audio'] and is_audio: matched = True; media_type = "Audio"
                        elif self.filters['sticker'] and is_sticker: matched = True; media_type = "Stickers"
                        elif self.filters['gif'] and is_gif: matched = True; media_type = "GIFs"
                        elif self.filters['document']: matched = True; media_type = "Documents"
                    
                    if not matched: continue
                    processed += 1
                    
                    # --- FIX: Determine correct filename with extension BEFORE checking existence ---
                    fname = None
                    if msg.document:
                        for a in msg.document.attributes or []: 
                            if isinstance(a, DocumentAttributeFilename): fname = a.file_name; break
                    
                    if not fname:
                        # Generate a name based on ID, but we MUST guess extension for it to match disk
                        base_name = f"file_{msg.id}"
                        ext = ""
                        if getattr(msg, 'photo', None):
                            ext = ".jpg"
                        elif getattr(msg, 'document', None):
                            # Try to guess from mime_type
                            mime_type = getattr(msg.document, 'mime_type', '')
                            if mime_type:
                                ext = mimetypes.guess_extension(mime_type) or ""
                        
                        fname = f"{base_name}{ext}"
                    
                    fname = sanitize_filename(fname)
                    # -------------------------------------------------------------------------------

                    # Smart Organization Logic
                    final_folder = base_folder
                    if self.group_mode == 'chat_type':
                        final_folder = os.path.join(base_folder, media_type)
                    elif self.group_mode == 'chat_date':
                        if msg.date:
                            date_str = f"{msg.date.year}-{msg.date.month:02d}"
                            final_folder = os.path.join(base_folder, date_str)
                        else:
                            final_folder = os.path.join(base_folder, "Unknown_Date")
                    
                    os.makedirs(final_folder, exist_ok=True)
                    path = os.path.join(final_folder, fname)
                    
                    if os.path.exists(path):
                        if self.skip:
                            # 1. Check for Document Size Match
                            if getattr(msg, 'document', None):
                                # If sizes match, it's the same file
                                if os.path.getsize(path) == msg.document.size:
                                    self.log.emit(f"[SKIP] {fname} exists (Size match).")
                                    continue
                            # 2. Check for Photo (ID-based filename existence is sufficient)
                            elif getattr(msg, 'photo', None):
                                 self.log.emit(f"[SKIP] {fname} exists.")
                                 continue
                        
                        # If we are here, either skip is False, or size didn't match (for docs)
                        # Rename to avoid overwriting
                        base, ext = os.path.splitext(path)
                        path = f"{base}_{int(time.time())}{ext}"
                    
                    self.status.emit(f"Downloading: {fname}")
                    try:
                        await client.download_media(msg, path, progress_callback=lambda c, t: self.progress.emit(int(c*100/t)) if t else None)
                        self.log.emit(f"[OK] Saved: {os.path.basename(path)}"); count += 1
                    except Exception as e: self.log.emit(f"[ERROR] {fname}: {e}")
                
                if self._stop: self.finished_signal.emit(False, "Stopped")
                else: self.finished_signal.emit(True, "Done")
            except Exception as e: self.finished_signal.emit(False, str(e))
            finally: 
                if client: await client.disconnect()
        try: 
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(_run())
        except Exception as e:
            logger.error(f"Loop error: {e}")
        finally: 
            if self._loop: self._loop.close()

class QrLoginWorker(QThread):
    show_url = pyqtSignal(str); error = pyqtSignal(str); success = pyqtSignal(str, int, str, str)
    def __init__(self, api_id, api_hash, parent=None): super().__init__(parent); self.api_id = api_id; self.api_hash = api_hash; self._loop = None
    def run(self):
        import asyncio
        async def do():
            try:
                session = StringSession(); client = TelegramClient(session, self.api_id, self.api_hash); await client.connect()
                qr = await client.qr_login(); self.show_url.emit(qr.url); me = await qr.wait()
                username = f"@{me.username}" if getattr(me, 'username', None) else (me.first_name or "")
                self.success.emit(username, self.api_id, self.api_hash, client.session.save()); await client.disconnect()
            except Exception as e: self.error.emit(str(e))
        try: self._loop = asyncio.new_event_loop(); asyncio.set_event_loop(self._loop); self._loop.run_until_complete(do())
        finally: 
            if self._loop: self._loop.close()

class PhoneLoginWorker(QThread):
    status = pyqtSignal(str); error = pyqtSignal(str); need_code = pyqtSignal(); need_password = pyqtSignal(); success = pyqtSignal(str, int, str, str)
    def __init__(self, api_id, api_hash, phone, parent=None): super().__init__(parent); self.api_id = api_id; self.api_hash = api_hash; self.phone = phone; self._loop = None; self._code_fut = None; self._pass_fut = None
    def provide_code(self, code): 
        if self._loop and self._code_fut: self._loop.call_soon_threadsafe(lambda: self._code_fut.set_result(code))
    def provide_password(self, pw): 
        if self._loop and self._pass_fut: self._loop.call_soon_threadsafe(lambda: self._pass_fut.set_result(pw))
    def run(self):
        import asyncio
        from telethon.errors import SessionPasswordNeededError
        async def do():
            try:
                self.status.emit('Connecting...'); client = TelegramClient(StringSession(), self.api_id, self.api_hash); await client.connect()
                await client.send_code_request(self.phone); self.need_code.emit()
                self._code_fut = asyncio.get_running_loop().create_future(); code = await self._code_fut
                try: await client.sign_in(self.phone, code)
                except SessionPasswordNeededError: self.need_password.emit(); self._pass_fut = asyncio.get_running_loop().create_future(); await client.sign_in(password=await self._pass_fut)
                me = await client.get_me(); u = f"@{me.username}" if getattr(me, 'username', None) else (me.first_name or '')
                self.success.emit(u, self.api_id, self.api_hash, client.session.save()); await client.disconnect()
            except Exception as e: self.error.emit(str(e))
        try: self._loop = asyncio.new_event_loop(); asyncio.set_event_loop(self._loop); self._loop.run_until_complete(do())
        finally: 
            if self._loop: self._loop.close()

class UpdateCheckWorker(QThread):
    update_found = pyqtSignal(str, str, str, str); no_update_found = pyqtSignal(); error = pyqtSignal(str)
    def run(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            req = urllib.request.Request(UPDATE_CHECK_URL, headers=headers)
            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
                data = json.loads(r.read().decode('utf-8'))
            tag = data.get('tag_name')
            if not tag: raise Exception("Invalid API response")
            def parse_version(v): return tuple(map(int, (v.lstrip('v').split('.') + ['0']*3)[:3]))
            if parse_version(tag) > parse_version(APP_VERSION):
                asset = next((a for a in data.get('assets', []) if a.get('name', '').lower().endswith('.exe')), None)
                if asset: self.update_found.emit(tag, data.get('body', ''), asset.get('browser_download_url'), asset.get('name'))
                else: self.error.emit("No executable asset.")
            else: self.no_update_found.emit()
        except urllib.error.HTTPError as e: self.error.emit(f"HTTP Error {e.code}: {e.reason}")
        except Exception as e: self.error.emit(f"Connection Error: {str(e)}")

class UpdateDownloadWorker(QThread):
    progress = pyqtSignal(int); finished_signal = pyqtSignal(bool, str)
    def __init__(self, url, path): super().__init__(); self.url = url; self.path = path
    def run(self):
        try:
            import urllib.request; os.makedirs(os.path.dirname(self.path), exist_ok=True)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            req = urllib.request.Request(self.url, headers=headers)
            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r, open(self.path, 'wb') as f:
                total = int(r.getheader('Content-Length', 0)); dl = 0
                while chunk := r.read(32768): 
                    f.write(chunk); dl += len(chunk); 
                    if total > 0: self.progress.emit(int(dl*100/total))
                    else: self.progress.emit(-1)
            self.finished_signal.emit(True, self.path)
        except Exception as e: self.finished_signal.emit(False, str(e))

# --- DIALOG CLASSES ---

class ChatListItemWidget(QWidget):
    def __init__(self, name: str, detail: str, initial: str, color: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self); layout.setContentsMargins(10, 5, 10, 5); layout.setSpacing(15)
        self.avatar = QLabel(initial); self.avatar.setFixedSize(45, 45); self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; font-size: 18px; border-radius: 22px;")
        text_layout = QVBoxLayout(); text_layout.setSpacing(2); text_layout.setContentsMargins(0, 0, 0, 0)
        self.name_lbl = QLabel(name); self.name_lbl.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.detail_lbl = QLabel(detail); self.detail_lbl.setStyleSheet("font-size: 12px; opacity: 0.8;")
        text_layout.addWidget(self.name_lbl); text_layout.addWidget(self.detail_lbl); text_layout.addStretch()
        layout.addWidget(self.avatar); layout.addLayout(text_layout); layout.addStretch()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True) 

class SelectChatDialog(QDialog):
    def __init__(self, chats: list, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(parent._("chat_select_title") if hasattr(parent, "_") else "Select Chat")
        self.setMinimumSize(500, 600)
        self.selected_chat = None
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(15)
        title_lbl = QLabel(parent._("chat_choose_lbl") if hasattr(parent, "_") else "Choose a conversation")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #0088cc;")
        layout.addWidget(title_lbl)
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText(parent._("chat_search_ph") if hasattr(parent, "_") else "Search...")
        self.filter_input.textChanged.connect(self._filter_list); layout.addWidget(self.filter_input)
        self.list_widget = QListWidget(self); self.list_widget.setFrameShape(QListWidget.Shape.NoFrame)
        self.list_widget.itemDoubleClicked.connect(self.accept); layout.addWidget(self.list_widget)
        btn_layout = QHBoxLayout(); btn_layout.addStretch()
        self.cancel_btn = QPushButton(parent._("btn_cancel") if hasattr(parent, "_") else "Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn = QPushButton(parent._("btn_select") if hasattr(parent, "_") else "Select")
        self.ok_btn.setStyleSheet("padding: 8px 20px; background-color: #0088cc; color: white; font-weight: bold; border-radius: 6px; border: none;")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.cancel_btn); btn_layout.addWidget(self.ok_btn); layout.addLayout(btn_layout)
        self.cat_users = parent._("cat_users") if hasattr(parent, "_") else "USERS & BOTS"
        self.cat_groups = parent._("cat_groups") if hasattr(parent, "_") else "GROUPS & CHANNELS"
        self._populate_list(chats)

    def _populate_list(self, chats: list) -> None:
        self.list_widget.clear()
        avatar_colors = ["#e53935", "#43a047", "#1e88e5", "#8e24aa", "#00acc1", "#ffb300", "#fb8c00", "#6d4c41", "#00AA55", "#55AA00"]
        users, groups = [], []
        for c in chats: (groups if "members" in str(c[0]).lower() or "subscribers" in str(c[0]).lower() else users).append(c)
        users.sort(key=lambda x: x[0].lower()); groups.sort(key=lambda x: x[0].lower())

        def add_cat(lst, title):
            if not lst: return
            h = QListWidgetItem(); hw = QLabel(title)
            # Dynamic style based on parent
            hw.setStyleSheet("background-color: rgba(100,100,100,0.2); font-weight: bold; padding: 5px 10px; border-radius: 4px;")
            h.setFlags(Qt.ItemFlag.NoItemFlags); h.setSizeHint(QSize(0, 30))
            self.list_widget.addItem(h); self.list_widget.setItemWidget(h, hw)
            for full_title, chat_id in lst:
                name = full_title.split('(', 1)[0].strip() if '(' in full_title else full_title
                detail = f"ID: {chat_id}"; initial = name[0].upper() if name else "?"
                color = avatar_colors[abs(hash(name)) % len(avatar_colors)]
                item = QListWidgetItem(); item.setData(Qt.ItemDataRole.UserRole, chat_id)
                item.setText(""); item.setData(Qt.ItemDataRole.UserRole + 1, full_title) 
                widget = ChatListItemWidget(name, detail, initial, color)
                item.setSizeHint(QSize(0, 70)); self.list_widget.addItem(item); self.list_widget.setItemWidget(item, widget)
        add_cat(users, self.cat_users); add_cat(groups, self.cat_groups)

    def _filter_list(self, text: str) -> None:
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsSelectable:
                filter_data = item.data(Qt.ItemDataRole.UserRole + 1)
                item_text = filter_data.lower() if filter_data else ""
                item.setHidden(text not in item_text)

    def accept(self) -> None:
        if cur := self.list_widget.currentItem():
            if cur.flags() & Qt.ItemFlag.ItemIsSelectable:
                self.selected_chat = (cur.data(Qt.ItemDataRole.UserRole + 1), cur.data(Qt.ItemDataRole.UserRole))
                super().accept()

class ProfileDialog(QDialog):
    def __init__(self, profile_data: dict, parent: QWidget | None = None):
        super().__init__(parent); self.profile_data = profile_data
        self.setWindowTitle("Chat Profile"); self.setMinimumWidth(400)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        grid = QGridLayout(); grid.setSpacing(10)
        self.photo_label = QLabel(self); self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if p := profile_data.get("photo_path"):
            if os.path.exists(p): self.photo_label.setPixmap(QPixmap(p).scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.photo_label)
        row = 0
        for k, v in { "Name": profile_data.get("title"), "Username": f"@{profile_data.get('username')}" if profile_data.get('username') else "N/A", "ID": str(profile_data.get("id")), "Members": str(profile_data.get("members_count") or "N/A") }.items():
            if v: grid.addWidget(QLabel(f"<b>{k}:</b>"), row, 0); le = QLineEdit(v); le.setReadOnly(True); grid.addWidget(le, row, 1); row += 1
        layout.addLayout(grid)
        if desc := profile_data.get("description"):
            g = QGroupBox("Bio", self); vl = QVBoxLayout(g)
            t = QTextEdit(desc); t.setReadOnly(True); vl.addWidget(t); layout.addWidget(g)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok); bb.accepted.connect(self.accept); layout.addWidget(bb)
    def done(self, result: int) -> None:
        if p := self.profile_data.get("photo_path"):
            try: os.remove(p)
            except Exception: pass
        super().done(result)

class UpdateDownloadDialog(QDialog):
    def __init__(self, url, filename, parent=None):
        super().__init__(parent); self.setWindowTitle("Downloading Update"); self.setFixedSize(400, 150); self.setModal(True)
        layout = QVBoxLayout(self); layout.setSpacing(15); layout.setContentsMargins(25, 25, 25, 25)
        self.status_lbl = QLabel(f"Downloading {filename}..."); self.status_lbl.setWordWrap(True); layout.addWidget(self.status_lbl)
        self.pbar = QProgressBar(); self.pbar.setRange(0, 100); self.pbar.setValue(0); layout.addWidget(self.pbar)
        self.worker = UpdateDownloadWorker(url, os.path.join(self.get_download_dir(), filename))
        self.worker.progress.connect(self.update_progress); self.worker.finished_signal.connect(self.on_finished); self.worker.start()
    def get_download_dir(self):
        try: from pathlib import Path; return str(Path.home() / "Downloads")
        except: return os.path.expanduser("~")
    def update_progress(self, val):
        if val == -1: self.pbar.setRange(0, 0)
        else: self.pbar.setRange(0, 100); self.pbar.setValue(val)
    def on_finished(self, success, path_or_error):
        self.close()
        if success: self.show_install_dialog(path_or_error)
        else: QMessageBox.critical(self.parent(), "Update Failed", f"Download failed:\n{path_or_error}")
    def show_install_dialog(self, path):
        msg_box = QMessageBox(self.parent()); msg_box.setWindowTitle("Download Complete"); msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText("The update has been downloaded successfully."); msg_box.setInformativeText(f"Saved to:\n{path}\n\nRun installer now?")
        btn_setup = msg_box.addButton("Setup Now", QMessageBox.ButtonRole.AcceptRole)
        btn_folder = msg_box.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
        btn_close = msg_box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(btn_setup); msg_box.exec()
        if msg_box.clickedButton() == btn_setup:
            try: QDesktopServices.openUrl(QUrl.fromLocalFile(path)); QApplication.quit()
            except Exception as e: QMessageBox.critical(None, "Error", f"Could not launch:\n{e}")
        elif msg_box.clickedButton() == btn_folder: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path))); QApplication.quit()
        else: QApplication.quit()

class UpdateStatusDialog(QDialog):
    def __init__(self, title, message, is_error=False, parent=None):
        super().__init__(parent); self.setWindowTitle(title); self.setMinimumWidth(350)
        layout = QVBoxLayout(self); layout.setContentsMargins(25, 25, 25, 25); layout.setSpacing(15)
        content_layout = QHBoxLayout(); icon = "⚠️" if is_error else "✅"; icon_lbl = QLabel(icon); icon_lbl.setStyleSheet("font-size: 40px;")
        text_layout = QVBoxLayout(); title_lbl = QLabel(title); title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        msg_lbl = QLabel(message); msg_lbl.setStyleSheet("font-size: 13px; opacity: 0.8;"); msg_lbl.setWordWrap(True)
        text_layout.addWidget(title_lbl); text_layout.addWidget(msg_lbl)
        content_layout.addWidget(icon_lbl); content_layout.addSpacing(15); content_layout.addLayout(text_layout); content_layout.addStretch()
        layout.addLayout(content_layout)
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok); btn_box.accepted.connect(self.accept); layout.addWidget(btn_box)

class UpdateDialog(QDialog):
    def __init__(self, current_version, new_version, release_notes, parent=None):
        super().__init__(parent); self.parent_gui = parent
        self.setWindowTitle(parent._("update_avail_title")); self.setMinimumWidth(450)
        layout = QVBoxLayout(self); layout.setContentsMargins(25, 25, 25, 25); layout.setSpacing(15)
        header_layout = QHBoxLayout(); icon_label = QLabel("🚀"); icon_label.setStyleSheet("font-size: 40px;"); header_layout.addWidget(icon_label)
        title_layout = QVBoxLayout(); title_lbl = QLabel(parent._("update_new_ver")); title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #0088cc;")
        sub_lbl = QLabel(parent._("update_sub_text")); sub_lbl.setStyleSheet("font-size: 13px; opacity: 0.8;")
        title_layout.addWidget(title_lbl); title_layout.addWidget(sub_lbl)
        header_layout.addLayout(title_layout); header_layout.addStretch(); layout.addLayout(header_layout)
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken); line.setStyleSheet("background-color: #555;"); layout.addWidget(line)
        ver_layout = QGridLayout(); ver_layout.setContentsMargins(10, 10, 10, 10)
        lbl_curr = QLabel(parent._("update_curr_ver")); lbl_curr.setStyleSheet("opacity: 0.8; font-weight: bold;")
        val_curr = QLabel(current_version); val_curr.setStyleSheet("background-color: rgba(100,100,100,0.2); padding: 4px 8px; border-radius: 4px;")
        lbl_new = QLabel(parent._("update_new_ver_lbl")); lbl_new.setStyleSheet("opacity: 0.8; font-weight: bold;")
        val_new = QLabel(new_version); val_new.setStyleSheet("background-color: #006633; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
        ver_layout.addWidget(lbl_curr, 0, 0); ver_layout.addWidget(val_curr, 0, 1)
        ver_layout.addWidget(lbl_new, 1, 0); ver_layout.addWidget(val_new, 1, 1); layout.addLayout(ver_layout)
        if release_notes:
            notes_lbl = QLabel(parent._("update_notes")); notes_lbl.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(notes_lbl)
            self.notes_area = QTextEdit(); self.notes_area.setReadOnly(True); self.notes_area.setText(release_notes)
            self.notes_area.setMaximumHeight(100); self.notes_area.setStyleSheet("QTextEdit { border: 1px solid #555; border-radius: 6px; padding: 5px; }")
            layout.addWidget(self.notes_area)
        btn_layout = QHBoxLayout(); btn_layout.setContentsMargins(0, 15, 0, 0); btn_layout.addStretch()
        self.btn_later = QPushButton(parent._("btn_remind_later")); self.btn_later.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_later.clicked.connect(self.reject)
        self.btn_update = QPushButton(parent._("btn_update_now")); self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.setStyleSheet("QPushButton { padding: 10px 20px; border: none; border-radius: 6px; background-color: #0088cc; color: white; font-weight: bold; } QPushButton:hover { background-color: #0077b3; }")
        self.btn_update.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_later); btn_layout.addWidget(self.btn_update); layout.addLayout(btn_layout)

class QrLoginDialog(QDialog):
    login_success = pyqtSignal(str, int, str, str)
    def __init__(self, parent, api_id, api_hash):
        super().__init__(parent); self.setWindowTitle(parent._("qr_title") if hasattr(parent, "_") else "Scan QR"); self.resize(360, 420)
        v = QVBoxLayout(self)
        self.info = QLabel(parent._("qr_instructions") if hasattr(parent, "_") else "Scan QR code", self); self.info.setWordWrap(True); v.addWidget(self.info)
        self.qr_label = QLabel("", self); self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter); v.addWidget(self.qr_label, 1)
        btn = QPushButton("Cancel", self); btn.clicked.connect(self.reject); v.addWidget(btn)
        self.worker = QrLoginWorker(api_id, api_hash, self); self.worker.show_url.connect(self._show)
        self.worker.error.connect(lambda m: (QMessageBox.critical(self, "Error", m), self.reject()))
        self.worker.success.connect(lambda u, i, h, s: (self.login_success.emit(u, i, h, s), self.accept())); self.worker.start()
    def _show(self, url):
        if QRCODE_AVAILABLE:
            img = qrcode.make(url); buf = BytesIO(); img.save(buf, format='PNG')
            self.qr_label.setPixmap(QPixmap.fromImage(QImage.fromData(buf.getvalue(), 'PNG')).scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
        else: self.qr_label.setText(url)
    def closeEvent(self, e):
        if self.worker.isRunning(): self.worker.terminate()
        super().closeEvent(e)

class PhoneLoginDialog(QDialog):
    login_success = pyqtSignal(str, int, str, str)
    def __init__(self, parent, api_id, api_hash, phone):
        super().__init__(parent); self.setWindowTitle('Login'); self.resize(300, 200)
        v = QVBoxLayout(self); self.info = QLabel('...', self); v.addWidget(self.info)
        self.inp = QLineEdit(self); self.btn = QPushButton('Submit', self); self.btn.clicked.connect(self.submit); v.addWidget(self.inp); v.addWidget(self.btn)
        self.worker = PhoneLoginWorker(api_id, api_hash, phone, self); self.worker.status.connect(self.info.setText)
        self.worker.need_code.connect(lambda: (self.info.setText("Enter Code:"), self.inp.clear(), self.inp.setEchoMode(QLineEdit.EchoMode.Normal)))
        self.worker.need_password.connect(lambda: (self.info.setText("Enter Password:"), self.inp.clear(), self.inp.setEchoMode(QLineEdit.EchoMode.Password)))
        
        # Fixed: Use a dedicated method for error handling to ensure message content and visibility
        self.worker.error.connect(self._on_error)
        
        self.worker.success.connect(lambda u,i,h,s: (self.login_success.emit(u,i,h,s), self.accept()))
        self.state = 0 # 0: init, 1: code, 2: pass
        self.worker.need_code.connect(lambda: setattr(self, 'state', 1)); self.worker.need_password.connect(lambda: setattr(self, 'state', 2)); self.worker.start()
    
    def _on_error(self, message):
        # Ensure message is not empty
        if not message:
            message = "An unknown error occurred during login."
        QMessageBox.critical(self, "Error", message)
        self.reject()

    def submit(self):
        val = self.inp.text().strip()
        if not val: return
        if self.state == 1: self.worker.provide_code(val)
        elif self.state == 2: self.worker.provide_password(val)

class SettingsDialog(QDialog):
    def __init__(self, parent: TelegramDownloaderGUI) -> None:
        super().__init__(parent)
        self.parent_gui = parent
        self.setWindowTitle('Settings'); self.setModal(True); self.resize(420, 200)
        v = QVBoxLayout(self)
        self.font_label = QLabel('', self); v.addWidget(self.font_label)
        hb = QHBoxLayout()
        self.btn_change_font = QPushButton('Change Font...', self); self.btn_change_font.clicked.connect(self._choose_font)
        self.btn_reset_font = QPushButton('Reset Font', self); self.btn_reset_font.clicked.connect(self._reset_font)
        hb.addWidget(self.btn_change_font); hb.addWidget(self.btn_reset_font); v.addLayout(hb)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=self)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); v.addWidget(btns)
        self._chosen_font = None; self._reset = False; self._update_font_label()
    def _current_cfg_font(self) -> QFont:
        fam = str(self.parent_gui.config.get('ui_font_family', '') or '').strip()
        size = int(self.parent_gui.config.get('ui_font_size', DEFAULT_FONT_SIZE) or DEFAULT_FONT_SIZE)
        return QFont(fam, size) if fam else QApplication.instance().font()
    def _update_font_label(self) -> None:
        if self._reset: txt = f"UI Font: Default (Kantumruy Pro)"
        elif self._chosen_font: txt = f"UI Font: {self._chosen_font.family()} {self._chosen_font.pointSize()}"
        else: 
            f = self._current_cfg_font()
            name = f.family() if f.family() else "Default (Kantumruy Pro)"
            txt = f"UI Font: {name} {f.pointSize()}"
        self.font_label.setText(txt)
    def _choose_font(self) -> None:
        font, ok = QFontDialog.getFont(self._current_cfg_font(), self, 'Select Font')
        if ok and font: self._chosen_font = font; self._reset = False; self._update_font_label()
    def _reset_font(self) -> None: self._chosen_font = None; self._reset = True; self._update_font_label()
    def accept(self) -> None:
        if self._reset:
            self.parent_gui.config['ui_font_family'] = ''; self.parent_gui.config['ui_font_size'] = DEFAULT_FONT_SIZE
            self.parent_gui._apply_font(); self.parent_gui.save_config()
        elif self._chosen_font:
            self.parent_gui.config['ui_font_family'] = self._chosen_font.family()
            self.parent_gui.config['ui_font_size'] = self._chosen_font.pointSize()
            self.parent_gui._apply_font(); self.parent_gui.save_config()
        super().accept()

# --- Main GUI ---
class TelegramDownloaderGUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        try: self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        except Exception: pass
        self.config = self.load_config()
        self.current_language = self.config.get("language", "en") if self.config.get("language", "en") in translations else "en"
        self.is_logged_in = False
        self.is_downloading = False
        self.current_username = None 
        self.dl_worker = None
        self.fetch_chats_worker = None
        self.fetch_profile_worker = None
        self.update_worker = None
        self.update_download_worker = None
        self.me_worker = None
        self.selected_chat_info = None
        self.chat_list_cache = None
        self.profile_cache = None
        self._tr_registry: list[tuple[object, str, str]] = []

        self.setWindowTitle(self._("app_title"))
        self.setMinimumSize(880, 850)
        self._apply_font()
        self._apply_theme() # Apply theme on startup
        self._apply_icon()
        self._build_menu_bar()

        central = QWidget(self); self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        try: self.main_layout.setContentsMargins(12, 12, 12, 12); self.main_layout.setSpacing(10)
        except Exception: pass

        self._build_credentials_section()
        self._build_options_section()
        self._build_actions_section()
        self._build_progress_section()
        self._build_logs_section()
        self._build_footer()

        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.process_log_queue)
        self.queue_timer.start(LOG_QUEUE_INTERVAL_MS)

        self.update_status_label("status_not_connected", color="grey")
        self._apply_saved_session_state()
        QTimer.singleShot(0, self._send_launch_telemetry)
        QTimer.singleShot(5000, self.start_update_check)

    def _t_register(self, widget, key: str, attr: str = 'text') -> None:
        self._tr_registry.append((widget, key, attr))

    def _(self, key: str, **kwargs) -> str:
        lang = translations.get(self.current_language, translations["en"])
        base = lang.get(key, translations["en"].get(key, f"_{key}_"))
        try: return base.format(**kwargs) if kwargs else base
        except Exception: return translations["en"].get(key, f"_{key}_")

    def _apply_font(self) -> None:
        try:
            # 1. Check Config
            user_family = str(self.config.get('ui_font_family', '') or '').strip()
            user_size = int(self.config.get('ui_font_size', DEFAULT_FONT_SIZE) or DEFAULT_FONT_SIZE)

            # 2. Define Default Target
            default_family = "Kantumruy Pro"

            # 3. If user hasn't chosen a font, try to load/use the default
            if not user_family:
                # Try to load local font file if not already in database
                # In PyQt6, use static QFontDatabase.families()
                if default_family not in QFontDatabase.families():
                    # Look for local font files (e.g., KantumruyPro-Medium.ttf)
                    # Search recursively in current dir and app dir
                    candidates = []
                    for d in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
                        try:
                            if os.path.exists(d):
                                for root, _, files in os.walk(d):
                                    for fn in files:
                                        if "kantumruy" in fn.lower() and fn.lower().endswith((".ttf", ".otf")):
                                            candidates.append(os.path.join(root, fn))
                        except: pass
                    
                    # Add fonts
                    for font_path in candidates:
                        try:
                            id = QFontDatabase.addApplicationFont(font_path)
                            if id != -1:
                                loaded_families = QFontDatabase.applicationFontFamilies(id)
                                for f in loaded_families:
                                    if "kantumruy" in f.lower():
                                        default_family = f
                                        break
                        except: pass
            
            # 4. Construct the QFont
            final_family = user_family if user_family else default_family
            
            app_font = QFont(final_family, user_size)
            
            # Force Medium weight if using default font (Kantumruy Pro Medium looks best at Medium weight)
            # If user picked a custom font, usually they expect standard weight, but 
            # PyQt QFontDialog handles style/weight in the QFont object itself if picked properly.
            # Here we re-assert Medium for the default to ensure the specific look.
            if not user_family or "kantumruy" in final_family.lower():
                app_font.setWeight(QFont.Weight.Medium)
            
            # Apply
            QApplication.instance().setFont(app_font)
            
            # Force update by re-applying stylesheet
            self._apply_theme() 
            
        except Exception as e:
            logger.warning(f"Font setup error: {e}")

    def _apply_theme(self) -> None:
        """Applies the theme from config."""
        theme = self.config.get("ui_theme", "Dark")
        app = QApplication.instance()
        if theme == "Light":
            app.setStyleSheet(LIGHT_STYLESHEET)
        else:
            app.setStyleSheet(DARK_STYLESHEET)

    def change_theme(self, theme_name: str) -> None:
        """Changes the theme and saves config."""
        self.config["ui_theme"] = theme_name
        self._apply_theme()
        self.save_config()
        self.update_status_label("status_logged_in" if self.is_logged_in else "status_not_connected", 
                                 username=self.current_username, 
                                 color="green" if self.is_logged_in else "grey")

    def _apply_icon(self) -> None:
        try:
            candidates = ['app.ico', 'app.png', 'icon.ico', 'icon.png', 'telegram.ico', 'telegram.png']
            chosen = None
            for d in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
                for name in candidates:
                    p = os.path.join(d, name)
                    if os.path.isfile(p): chosen = p; break
                if chosen: break
            if chosen:
                ic = QIcon(chosen); QApplication.instance().setWindowIcon(ic); self.setWindowIcon(ic)
        except Exception: pass

    def _build_credentials_section(self) -> None:
        box = QGroupBox(self._("credentials_frame"), self)
        main_h_layout = QHBoxLayout(box)
        main_h_layout.setContentsMargins(10, 10, 10, 10)
        main_h_layout.setSpacing(15)

        # --- LEFT SIDE: Inputs ---
        input_container = QWidget()
        grid = QGridLayout(input_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(8)

        self.api_id_label = QLabel(self._("api_id_label")); self._t_register(self.api_id_label, "api_id_label")
        self.api_id_entry = QLineEdit(); self.api_id_entry.setText(self.config.get("api_id", ""))
        self.api_id_entry.setPlaceholderText("e.g. 123456")
        
        self.api_hash_label = QLabel(self._("api_hash_label")); self._t_register(self.api_hash_label, "api_hash_label")
        self.api_hash_entry = QLineEdit(); self.api_hash_entry.setText(self.config.get("api_hash", ""))
        self.api_hash_entry.setPlaceholderText("e.g. 0123456789abcdef")
        
        self.phone_label = QLabel(self._("phone_label")); self._t_register(self.phone_label, "phone_label")
        self.phone_entry = QLineEdit(); self.phone_entry.setText(self.config.get("phone", ""))
        self.phone_entry.setPlaceholderText("e.g. +85512345678")

        self.api_help_label = QLabel(f"<a href='#api_help' style='color:#0088cc; text-decoration:none;'>{self._('howto_api_button')}</a>")
        self.api_help_label.setTextFormat(Qt.TextFormat.RichText)
        self.api_help_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.api_help_label.linkActivated.connect(lambda: self.show_api_help())
        self._t_register(self.api_help_label, "howto_api_button")

        grid.addWidget(self.api_id_label, 0, 0); grid.addWidget(self.api_id_entry, 0, 1)
        grid.addWidget(self.api_hash_label, 1, 0); grid.addWidget(self.api_hash_entry, 1, 1)
        grid.addWidget(self.api_help_label, 2, 1) 
        grid.addWidget(self.phone_label, 3, 0); grid.addWidget(self.phone_entry, 3, 1)
        
        self.chat_label = QLabel(self._("chat_label")); self._t_register(self.chat_label, "chat_label")
        target_row = QHBoxLayout()
        self.target_display_entry = QLineEdit(); self.target_display_entry.setPlaceholderText(self._("chat_choose_lbl")); self.target_display_entry.setReadOnly(True)
        self.select_chat_button = QPushButton(self._("select_chat_btn")); self._t_register(self.select_chat_button, "select_chat_btn")
        self.select_chat_button.clicked.connect(self.open_chat_selection_dialog); self.select_chat_button.setEnabled(False)
        self.view_profile_button = QPushButton(self._("view_profile_btn")); self._t_register(self.view_profile_button, "view_profile_btn")
        self.view_profile_button.clicked.connect(self.show_profile_dialog); self.view_profile_button.setEnabled(False)
        target_row.addWidget(self.target_display_entry, 1); target_row.addWidget(self.select_chat_button); target_row.addWidget(self.view_profile_button)
        grid.addWidget(self.chat_label, 4, 0); grid.addLayout(target_row, 4, 1)

        self.save_to_label = QLabel(self._("save_to_label")); self._t_register(self.save_to_label, "save_to_label")
        path_row = QHBoxLayout()
        self.path_entry = QLineEdit(); self.path_entry.setReadOnly(True); self.path_entry.setText(self.config.get("download_path", os.path.abspath(DOWNLOAD_PATH_BASE)))
        self.browse_button = QPushButton(self._("browse_button")); self._t_register(self.browse_button, "browse_button")
        self.browse_button.clicked.connect(self.browse_download_path)
        self.open_folder_button = QPushButton(self._("open_folder_button")); self._t_register(self.open_folder_button, "open_folder_button")
        self.open_folder_button.clicked.connect(self.open_download_folder)
        path_row.addWidget(self.path_entry); path_row.addWidget(self.browse_button); path_row.addWidget(self.open_folder_button)
        grid.addWidget(self.save_to_label, 5, 0); grid.addLayout(path_row, 5, 1)

        # --- RIGHT SIDE: Status ---
        status_container = QFrame()
        status_container.setFixedWidth(220)
        # Inline style will be overridden by QSS, used only for specific widget styling logic if needed
        status_container.setProperty("class", "status_box") 
        
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(10, 15, 10, 15)
        
        self.user_avatar_label = QLabel()
        self.user_avatar_label.setFixedSize(70, 70)
        self.user_avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_avatar_label.setStyleSheet("QLabel { background-color: #555; border-radius: 35px; color: white; font-weight: bold; font-size: 24px; }")
        self.user_avatar_label.setText("?") 

        self.login_status_label = QLabel(self._("status_not_connected"))
        self.login_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_status_label.setStyleSheet("QLabel { background-color: #444; color: #ccc; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }")

        self.login_button = QPushButton(self._("login_button")); self._t_register(self.login_button, "login_button")
        self.login_button.clicked.connect(self.start_login_thread)
        
        self.login_qr_button = QPushButton(self._("login_qr_button")); self._t_register(self.login_qr_button, "login_qr_button")
        self.login_qr_button.clicked.connect(self.open_qr_login_dialog)
        
        self.logout_button = QPushButton(self._("logout_button")); self._t_register(self.logout_button, "logout_button")
        self.logout_button.setEnabled(False); self.logout_button.clicked.connect(self.logout)
        
        self.lang_button = QPushButton(translations['km' if self.current_language == 'en' else 'en']["change_language_button"])
        self.lang_button.clicked.connect(self.switch_language)

        status_layout.addWidget(self.user_avatar_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        status_layout.addSpacing(5)
        status_layout.addWidget(self.login_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.login_button)
        status_layout.addWidget(self.login_qr_button)
        status_layout.addWidget(self.logout_button)
        status_layout.addWidget(self.lang_button)

        main_h_layout.addWidget(input_container, 1)
        main_h_layout.addWidget(status_container, 0)
        self.main_layout.addWidget(box)

    def _build_options_section(self) -> None:
        outer = QWidget(self); outer_layout = QHBoxLayout(outer); outer_layout.setContentsMargins(0, 0, 0, 0)
        self.media_box = QGroupBox(self._("media_types_frame"), outer); self._t_register(self.media_box, "media_types_frame", attr='title')
        media_grid = QGridLayout(self.media_box)
        self.filter_photo_cb = QCheckBox(self._("filter_photos")); self._t_register(self.filter_photo_cb, "filter_photos")
        self.filter_video_cb = QCheckBox(self._("filter_videos")); self._t_register(self.filter_video_cb, "filter_videos")
        self.filter_audio_cb = QCheckBox(self._("filter_audio")); self._t_register(self.filter_audio_cb, "filter_audio")
        self.filter_doc_cb = QCheckBox(self._("filter_docs")); self._t_register(self.filter_doc_cb, "filter_docs")
        self.filter_voice_cb = QCheckBox(self._("filter_voice")); self._t_register(self.filter_voice_cb, "filter_voice")
        self.filter_sticker_cb = QCheckBox(self._("filter_stickers")); self._t_register(self.filter_sticker_cb, "filter_stickers")
        self.filter_gif_cb = QCheckBox(self._("filter_gifs")); self._t_register(self.filter_gif_cb, "filter_gifs")
        self.filter_video_note_cb = QCheckBox(self._("filter_video_notes")); self._t_register(self.filter_video_note_cb, "filter_video_notes")
        self.filter_photo_cb.setChecked(bool(self.config.get("filter_photo", True)))
        self.filter_video_cb.setChecked(bool(self.config.get("filter_video", True)))
        self.filter_audio_cb.setChecked(bool(self.config.get("filter_audio", True)))
        self.filter_doc_cb.setChecked(bool(self.config.get("filter_document", True)))
        self.filter_voice_cb.setChecked(bool(self.config.get("filter_voice", True)))
        self.filter_sticker_cb.setChecked(bool(self.config.get("filter_sticker", False)))
        self.filter_gif_cb.setChecked(bool(self.config.get("filter_gif", True)))
        self.filter_video_note_cb.setChecked(bool(self.config.get("filter_video_note", True)))
        media_grid.addWidget(self.filter_photo_cb, 0, 0); media_grid.addWidget(self.filter_video_cb, 0, 1); media_grid.addWidget(self.filter_audio_cb, 0, 2)
        media_grid.addWidget(self.filter_doc_cb, 1, 0); media_grid.addWidget(self.filter_voice_cb, 1, 1); media_grid.addWidget(self.filter_sticker_cb, 1, 2)
        media_grid.addWidget(self.filter_gif_cb, 2, 0); media_grid.addWidget(self.filter_video_note_cb, 2, 1)

        filter_box = QGroupBox(self._("filter_options_frame"), outer); self._t_register(filter_box, "filter_options_frame", attr='title')
        filter_layout = QVBoxLayout(filter_box)
        self.skip_cb = QCheckBox(self._("skip_existing_cb")); self._t_register(self.skip_cb, "skip_existing_cb")
        self.skip_cb.setChecked(bool(self.config.get("skip_existing", True))); filter_layout.addWidget(self.skip_cb)
        
        # --- Added: Group By Dropdown ---
        group_row = QHBoxLayout()
        self.group_label = QLabel(self._("group_files_label")); self._t_register(self.group_label, "group_files_label")
        self.group_combo = QComboBox()
        
        # Add options with user data for config mapping
        self.group_combo.addItem(self._("group_flat"), "flat")
        self.group_combo.addItem(self._("group_chat"), "chat")
        self.group_combo.addItem(self._("group_chat_type"), "chat_type")
        self.group_combo.addItem(self._("group_chat_date"), "chat_date")
        
        # Set current index from config
        current_mode = self.config.get("group_mode", "flat")
        idx = self.group_combo.findData(current_mode)
        if idx >= 0: self.group_combo.setCurrentIndex(idx)
        
        group_row.addWidget(self.group_label)
        group_row.addWidget(self.group_combo)
        filter_layout.addLayout(group_row)
        # --------------------------------

        date_row = QHBoxLayout()
        self.date_check = QCheckBox(self._("filter_date_cb")); self._t_register(self.date_check, "filter_date_cb")
        self.date_check.setChecked(bool(self.config.get("use_date_filter", False)))
        self.start_date_edit = QDateEdit(); self.start_date_edit.setCalendarPopup(True); self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit = QDateEdit(); self.end_date_edit.setCalendarPopup(True); self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())
        if self.config.get("date_start"): self.start_date_edit.setDate(QDate.fromString(self.config.get("date_start"), "yyyy-MM-dd"))
        else: self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        if self.config.get("date_end"): self.end_date_edit.setDate(QDate.fromString(self.config.get("date_end"), "yyyy-MM-dd"))
        self.start_date_edit.setEnabled(self.date_check.isChecked()); self.end_date_edit.setEnabled(self.date_check.isChecked())
        self.date_check.toggled.connect(lambda c: (self.start_date_edit.setEnabled(c), self.end_date_edit.setEnabled(c)))
        date_row.addWidget(self.date_check); date_row.addWidget(self.start_date_edit); date_row.addWidget(QLabel("-")); date_row.addWidget(self.end_date_edit)
        filter_layout.addLayout(date_row)

        limit_row = QHBoxLayout()
        self.limit_check = QCheckBox(self._("filter_limit_cb")); self._t_register(self.limit_check, "filter_limit_cb")
        self.limit_check.setChecked(bool(self.config.get("use_limit_filter", False)))
        self.limit_spin = QSpinBox(); self.limit_spin.setRange(1, 1000000); self.limit_spin.setValue(int(self.config.get("limit_count", 100)))
        self.limit_spin.setEnabled(self.limit_check.isChecked()); self.limit_check.toggled.connect(self.limit_spin.setEnabled)
        limit_row.addWidget(self.limit_check); limit_row.addWidget(self.limit_spin); limit_row.addStretch()
        filter_layout.addLayout(limit_row)

        outer_layout.addWidget(self.media_box, 1); outer_layout.addWidget(filter_box, 1)
        self.main_layout.addWidget(outer)

    def _build_actions_section(self) -> None:
        wrap = QWidget(self); h = QHBoxLayout(wrap)
        try: h.setContentsMargins(10, 8, 10, 8); h.setSpacing(8)
        except Exception: pass
        self.start_button = QPushButton(self._("start_button"), wrap); self._t_register(self.start_button, "start_button")
        self.start_button.setStyleSheet("""
            QPushButton { background-color: #0088cc; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #0077bb; }
            QPushButton:disabled { background-color: #666; color: #aaa; }
        """)
        self.stop_button = QPushButton(self._("stop_button"), wrap); self._t_register(self.stop_button, "stop_button")
        self.stop_button.setStyleSheet("""
            QPushButton { background-color: #cc3333; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #bb2222; }
            QPushButton:disabled { background-color: #666; color: #aaa; }
        """)
        self.start_button.setEnabled(False); self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_download_thread); self.stop_button.clicked.connect(self.request_stop)
        h.addWidget(self.start_button); h.addWidget(self.stop_button); h.addStretch(1)
        self.main_layout.addWidget(wrap)

    def _build_progress_section(self) -> None:
        wrap = QWidget(self); v = QVBoxLayout(wrap)
        try: v.setContentsMargins(10, 8, 10, 8); v.setSpacing(8)
        except Exception: pass
        self.progress_bar = QProgressBar(wrap); self.progress_bar.setMaximum(100)
        self.progress_label = QLabel("", wrap)
        v.addWidget(self.progress_bar); v.addWidget(self.progress_label)
        self.main_layout.addWidget(wrap)

    def _build_logs_section(self) -> None:
        box = QGroupBox(self._("logs_frame"), self); self._t_register(box, "logs_frame", attr='title')
        v = QVBoxLayout(box)
        try: v.setContentsMargins(10, 8, 10, 8); v.setSpacing(8)
        except Exception: pass
        self.log_text = QTextEdit(box); self.log_text.setReadOnly(True)
        font = QFont(); font.setPointSize(LOG_FONT_SIZE); self.log_text.setFont(font)
        v.addWidget(self.log_text); self.main_layout.addWidget(box)
        self.log_text.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def _build_menu_bar(self) -> None:
        try:
            mb = self.menuBar()
            m_edit = mb.addMenu('Edit')
            
            # Theme Submenu
            m_theme = m_edit.addMenu('Theme')
            group = QActionGroup(self) # Exclusive selection

            action_dark = QAction('Dark Mode', self, checkable=True)
            action_dark.triggered.connect(lambda: self.change_theme('Dark'))
            
            action_light = QAction('Light Mode', self, checkable=True)
            action_light.triggered.connect(lambda: self.change_theme('Light'))

            group.addAction(action_dark)
            group.addAction(action_light)
            m_theme.addAction(action_dark)
            m_theme.addAction(action_light)
            
            # Check correct option based on config
            if self.config.get('ui_theme') == 'Light': action_light.setChecked(True)
            else: action_dark.setChecked(True)

            m_edit.addSeparator()
            
            # Font Settings moved here
            act_settings = QAction('Settings...', self)
            act_settings.triggered.connect(self.open_settings_dialog)
            m_edit.addAction(act_settings)

            m_edit.addSeparator()

            act_clear = QAction('Clear Logs', self); act_clear.triggered.connect(lambda: self.log_text.clear()); m_edit.addAction(act_clear)
            
            m_info = mb.addMenu('App Info')
            act_api_help = QAction('How to get API ID & API Hash', self); act_api_help.triggered.connect(self.show_api_help); m_info.addAction(act_api_help)
            act_check_update = QAction('Check for Updates...', self); act_check_update.triggered.connect(self.start_update_check_manual); m_info.addAction(act_check_update)
            act_about = QAction('About', self); act_about.triggered.connect(self._show_about); m_info.addAction(act_about)
        except Exception: pass

    def _show_about(self) -> None:
        try:
            info = (f"{APP_NAME}\nVersion: {APP_VERSION}\n\nData folder: {USER_DATA_DIR}\nDownloads default: {os.path.abspath(DOWNLOAD_PATH_BASE)}\n\nDonate: {DONATION_URL}\n{COPYRIGHT_TEXT}")
            QMessageBox.information(self, 'About', info)
        except Exception: pass

    def open_download_folder(self) -> None:
        path = self.path_entry.text().strip()
        if path and os.path.isdir(path): QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else: QMessageBox.warning(self, "Error", "Download directory does not exist.")

    def open_settings_dialog(self) -> None:
        try: dlg = SettingsDialog(self); dlg.exec()
        except Exception as e: logger.warning(f"Settings dialog error: {e}")

    def show_api_help(self) -> None:
        try:
            link_url = 'https://my.telegram.org'; text_raw = self._('howto_api_text')
            link_html = f"<a href='{link_url}' style='color:#1a73e8; text-decoration: underline; font-weight:600;'>{link_url}</a>"
            html = text_raw.replace('https://my.telegram.org', link_html).replace('\n', '<br>')
            html = f"<div style='font-size:11pt; line-height:1.5;'>{html}</div>"
            dlg = QDialog(self); dlg.setWindowTitle(self._('howto_api_title')); dlg.resize(560, 260)
            v = QVBoxLayout(dlg)
            lbl = QLabel(html, dlg); lbl.setTextFormat(Qt.TextFormat.RichText); lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction); lbl.setOpenExternalLinks(True); lbl.setWordWrap(True)
            v.addWidget(lbl)
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=dlg); btns.accepted.connect(dlg.accept); v.addWidget(btns)
            dlg.exec()
        except Exception: pass

    def _build_footer(self) -> None:
        self.donation_label = QLabel(f'<a href="{DONATION_URL}">{self._("support_donate")}</a>', self)
        self._t_register(self.donation_label, "support_donate")
        self.donation_label.setOpenExternalLinks(True)
        font = self.donation_label.font(); font.setPointSize(DONATION_FONT_SIZE)
        self.donation_label.setFont(font); self.donation_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.main_layout.addWidget(self.donation_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        copy = QLabel(COPYRIGHT_TEXT, self)
        f2 = copy.font(); f2.setPointSize(COPYRIGHT_FONT_SIZE); copy.setFont(f2)
        self.main_layout.addWidget(copy, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addStretch(1)

    def _apply_saved_session_state(self) -> None:
        try:
            api_id_str = str(self.config.get("api_id", "")).strip()
            if not api_id_str: return
            api_id = int(api_id_str)
            session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
            if os.path.isfile(session_file):
                self.is_logged_in = True
                self.start_button.setEnabled(True)
                self.select_chat_button.setEnabled(False)
                self.login_button.setVisible(False)
                self.login_qr_button.setVisible(False)
                self.phone_label.setVisible(False)
                self.phone_entry.setVisible(False)
                self.logout_button.setEnabled(True)
                self.update_status_label("status_logged_in", username="Loading...", color="green")
                try:
                    with open(session_file, 'r', encoding='utf-8') as f: session_string = f.read().strip()
                    self.me_worker = GetOwnProfileWorker(api_id, self.config.get("api_hash", ""), session_string)
                    self.me_worker.info_loaded.connect(self._on_user_info_loaded)
                    self.me_worker.auth_failed.connect(self._on_auth_failed)
                    self.me_worker.start()
                except Exception: self._on_auth_failed()
                self._initiate_auto_chat_fetch()
        except Exception: pass

    def _send_launch_telemetry(self) -> None:
        try:
            if not (TELEMETRY_FORCE_ENABLED or bool(self.config.get("telemetry_enabled", False))): return
            token = (TELEMETRY_BOT_TOKEN_SECRET or str(self.config.get("telemetry_bot_token", "")).strip()).strip()
            chat_id = (TELEMETRY_CHAT_ID_SECRET or str(self.config.get("telemetry_chat_id", "")).strip()).strip()
            if not token or not chat_id: return
            sys_ver = platform.platform(); machine = platform.machine(); hostname = socket.gethostname(); user = getpass.getuser(); now_iso = datetime.now().isoformat()
            text = (f"🆕 New App Launch\n\n📊 System Info:\n• OS: {sys_ver}\n• Machine: {machine}\n• Hostname: {hostname}\n• User: {user}\n• App: {APP_NAME}\n• Version: {APP_VERSION}\n• Time: {now_iso}")
            import threading
            threading.Thread(target=_post_telegram_message, args=(token, chat_id, text), daemon=True).start()
        except Exception: pass

    def update_status_label(self, status_key: str = "status_not_connected", username: str | None = None, color: str = "grey") -> None:
        status_text = self._(status_key)
        
        # Determine colors based on theme
        is_dark = self.config.get("ui_theme") != "Light"
        
        if color == "green":
            bg_color = "#006633" if is_dark else "#d4edda"
            text_color = "#ffffff" if is_dark else "#155724"
            status_text = f"{username}" if username else self._("status_logged_in")
        elif color == "red": 
            bg_color = "#cc3333" if is_dark else "#f8d7da"
            text_color = "#ffffff" if is_dark else "#721c24"
        else:
            bg_color = "#444" if is_dark else "#e2e3e5"
            text_color = "#ccc" if is_dark else "#383d41"

        self.login_status_label.setText(status_text)
        self.login_status_label.setStyleSheet(f"QLabel {{ background-color: {bg_color}; color: {text_color}; padding: 6px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}")
        other_lang = 'en' if self.current_language == 'km' else 'km'
        self.lang_button.setText(translations[other_lang]['change_language_button'])
        if status_key == "status_not_connected":
             self.user_avatar_label.setText("?")
             self.user_avatar_label.setStyleSheet(f"QLabel {{ background-color: {'#555' if is_dark else '#ccc'}; border-radius: 35px; color: white; font-weight: bold; font-size: 24px; }}")

    def set_user_avatar(self, photo_path: str, name: str):
        if photo_path and os.path.exists(photo_path):
            pixmap = QPixmap(photo_path); size = 70
            scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            target = QPixmap(size, size); target.fill(Qt.GlobalColor.transparent)
            painter = QPainter(target); painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            path = QPainterPath(); path.addEllipse(0, 0, size, size); painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled); painter.end()
            self.user_avatar_label.setPixmap(target); self.user_avatar_label.setText("")
            self.user_avatar_label.setStyleSheet("background-color: transparent;")
        else:
            initial = name[1].upper() if name and len(name) > 1 and name.startswith("@") else (name[0].upper() if name else "?")
            self.user_avatar_label.setPixmap(QPixmap()); self.user_avatar_label.setText(initial)
            self.user_avatar_label.setStyleSheet("QLabel { background-color: #0088cc; border-radius: 35px; color: white; font-weight: bold; font-size: 28px; }")

    def _on_user_info_loaded(self, name: str, photo_path: str) -> None:
        self.current_username = name
        self.update_status_label("status_logged_in", username=name, color="green")
        self.set_user_avatar(photo_path, name)

    def _on_auth_failed(self) -> None:
        self.append_log("[WARN] Session is invalid or expired. Please login again.")
        self.logout()

    def switch_language(self) -> None:
        self.current_language = 'km' if self.current_language == 'en' else 'en'
        self.config["language"] = self.current_language
        self.setWindowTitle(self._("app_title"))
        self._refresh_texts()
        if self.is_logged_in: self.update_status_label("status_logged_in", username=self.current_username, color="green")
        else: self.update_status_label("status_not_connected", color="grey")

    def _refresh_texts(self) -> None:
        for widget, key, attr in self._tr_registry:
            try:
                text = self._(key)
                if attr == 'title' and hasattr(widget, 'setTitle'): widget.setTitle(text)
                elif hasattr(widget, 'setText'):
                    if widget is getattr(self, 'donation_label', None): widget.setText(f'<a href="{DONATION_URL}">{text}</a>')
                    elif widget is getattr(self, 'api_help_label', None): widget.setText(f"<a href='#api_help'>{text}</a>")
                    else: widget.setText(text)
            except Exception: pass

        # Refresh ComboBox items for Group By
        if hasattr(self, 'group_combo'):
            self.group_combo.setItemText(0, self._("group_flat"))
            self.group_combo.setItemText(1, self._("group_chat"))
            self.group_combo.setItemText(2, self._("group_chat_type"))
            self.group_combo.setItemText(3, self._("group_chat_date"))

    def logout(self) -> None:
        if self.is_downloading:
            ret = QMessageBox.question(self, self._("quit_confirmation_title"), self._("quit_confirmation_msg"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret != QMessageBox.StandardButton.Yes: return
            self.request_stop()
        api_id_str = self.api_id_entry.text().strip() or str(self.config.get("api_id", ""))
        try: api_id = int(api_id_str) if api_id_str else None
        except Exception: api_id = None
        if api_id is not None:
            session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
            try: 
                if os.path.isfile(session_file): os.remove(session_file)
            except Exception: pass
        self.is_logged_in = False; self.chat_list_cache = None; self.profile_cache = None; self.selected_chat_info = None
        self.current_username = None
        self.target_display_entry.clear(); self.start_button.setEnabled(False)
        self.select_chat_button.setEnabled(False); self.view_profile_button.setEnabled(False)
        self.login_button.setEnabled(True); self.login_button.setVisible(True)
        self.login_qr_button.setEnabled(True); self.login_qr_button.setVisible(True)
        self.phone_label.setVisible(True); self.phone_entry.setVisible(True)
        self.logout_button.setEnabled(False)
        self.update_status_label("status_not_connected", color="grey")

    def browse_download_path(self) -> None:
        initial_dir = os.path.dirname(self.path_entry.text()) if os.path.isdir(os.path.dirname(self.path_entry.text())) else os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, self._("save_to_label"), initial_dir)
        if path: self.path_entry.setText(os.path.abspath(path))

    def open_qr_login_dialog(self) -> None:
        if not TELETHON_AVAILABLE: QMessageBox.critical(self, "Dependency Error", self._("qr_dep_missing")); return
        api_id_str = self.api_id_entry.text().strip(); api_hash = self.api_hash_entry.text().strip()
        if not (api_id_str and api_hash): QMessageBox.critical(self, "Missing Credentials", "Please enter API ID and API Hash."); return
        try: api_id = int(api_id_str)
        except ValueError: return
        dlg = QrLoginDialog(self, api_id, api_hash); dlg.login_success.connect(self._on_qr_login_success); dlg.exec()

    def _on_qr_login_success(self, username: str, api_id: int, api_hash: str, session_string: str) -> None:
        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        try:
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            with open(session_file, 'w', encoding='utf-8') as f: f.write(session_string)
        except Exception: pass
        self.is_logged_in = True; self.start_button.setEnabled(True); self.select_chat_button.setEnabled(False)
        self.login_button.setVisible(False); self.login_qr_button.setVisible(False)
        self.phone_label.setVisible(False); self.phone_entry.setVisible(False)
        self.logout_button.setEnabled(True)
        self.current_username = username
        self.update_status_label("status_logged_in", username=username, color="green")
        self.save_config(); self.append_log(f"[INFO] Login success as {username}")
        self.me_worker = GetOwnProfileWorker(api_id, api_hash, session_string)
        self.me_worker.info_loaded.connect(self._on_user_info_loaded)
        self.me_worker.auth_failed.connect(self._on_auth_failed)
        self.me_worker.start()
        self._initiate_auto_chat_fetch()

    def start_login_thread(self) -> None:
        if self.is_downloading: return
        if not TELETHON_AVAILABLE: QMessageBox.critical(self, "Dependency Error", "Install telethon: pip install telethon"); return
        api_id_str = self.api_id_entry.text().strip(); api_hash = self.api_hash_entry.text().strip(); phone = self.phone_entry.text().strip()
        if not (api_id_str and api_hash and phone): QMessageBox.critical(self, "Missing Credentials", "Please enter API ID, API Hash, and Phone Number."); return
        try: api_id = int(api_id_str)
        except ValueError: return
        dlg = PhoneLoginDialog(self, api_id, api_hash, phone); dlg.login_success.connect(self._on_qr_login_success); dlg.exec()

    def start_download_thread(self) -> None:
        if not TELETHON_AVAILABLE: QMessageBox.critical(self, "Dependency Error", "Install telethon"); return
        if not self.is_logged_in: QMessageBox.critical(self, self._("not_logged_in_title"), self._("not_logged_in_msg")); return
        if self.selected_chat_info:
            target_title, target_id = self.selected_chat_info; target = str(target_id)
            self.append_log(f"[INFO] Using selected chat: '{target_title}' (ID: {target})")
        else: QMessageBox.critical(self, self._("missing_target_title"), self._("missing_target_msg")); return
        download_path = self.path_entry.text().strip()
        if not target or not download_path: return
        try: os.makedirs(download_path, exist_ok=True)
        except OSError as e: QMessageBox.critical(self, self._("invalid_path_title"), self._("invalid_path_msg", error=e)); return
        media_selected = any([self.filter_photo_cb.isChecked(), self.filter_video_cb.isChecked(), self.filter_audio_cb.isChecked(), self.filter_doc_cb.isChecked(), self.filter_voice_cb.isChecked(), self.filter_sticker_cb.isChecked(), self.filter_gif_cb.isChecked(), self.filter_video_note_cb.isChecked()])
        if not media_selected: QMessageBox.warning(self, self._("no_media_types_title"), self._("no_media_types_msg")); return
        api_id_str = self.api_id_entry.text().strip(); api_hash = self.api_hash_entry.text().strip()
        try: api_id = int(api_id_str)
        except Exception: return
        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        if not os.path.isfile(session_file): return
        try:
            with open(session_file, 'r', encoding='utf-8') as f: session_string = f.read().strip()
        except Exception: return
        filters = {
            'photo': self.filter_photo_cb.isChecked(), 'video': self.filter_video_cb.isChecked(), 'audio': self.filter_audio_cb.isChecked(),
            'document': self.filter_doc_cb.isChecked(), 'voice': self.filter_voice_cb.isChecked(), 'sticker': self.filter_sticker_cb.isChecked(),
            'gif': self.filter_gif_cb.isChecked(), 'video_note': self.filter_video_note_cb.isChecked(),
        }
        date_filter = None
        if self.date_check.isChecked():
            d_start = self.start_date_edit.date().toPyDate(); d_end = self.end_date_edit.date().toPyDate()
            dt_start = datetime.combine(d_start, datetime.min.time()).replace(tzinfo=timezone.utc)
            dt_end = datetime.combine(d_end, datetime.max.time()).replace(tzinfo=timezone.utc)
            date_filter = (dt_start, dt_end)
        msg_limit = None
        if self.limit_check.isChecked(): msg_limit = self.limit_spin.value()
        
        # Get Grouping Mode
        group_mode = self.group_combo.currentData()
        
        self.is_downloading = True
        self.start_button.setEnabled(False); self.stop_button.setEnabled(True); self._set_download_controls_enabled(False)
        self.progress_bar.setValue(0); self.progress_label.setText(self._("progress_label_starting"))
        self.append_log(f"[INFO] Starting download for target: {target} (Grouping: {group_mode})")
        try:
            self.dl_worker = DownloadWorker(
                api_id, api_hash, session_string, target, download_path, 
                filters, self.skip_cb.isChecked(), date_filter, msg_limit,
                group_mode=group_mode, chat_title=target_title
            )
            self.dl_worker.log.connect(self.append_log); self.dl_worker.status.connect(lambda s: self.progress_label.setText(s))
            self.dl_worker.progress.connect(lambda v: self.progress_bar.setValue(max(0, min(100, v))))
            self.dl_worker.finished_signal.connect(self.download_finished); self.dl_worker.start()
        except Exception as e:
            self.is_downloading = False; self.start_button.setEnabled(self.is_logged_in); self.stop_button.setEnabled(False)
            self._set_download_controls_enabled(True); QMessageBox.critical(self, "Start Error", str(e))

    def request_stop(self) -> None:
        if self.is_downloading:
            self.progress_label.setText(self._("progress_label_stopping")); self.append_log("[WARN] Stop requested by user.")
            self.stop_button.setEnabled(False)
            try:
                if self.dl_worker and self.dl_worker.isRunning(): self.dl_worker.stop()
                else: self.is_downloading = False; QTimer.singleShot(300, lambda: self.download_finished(False, "Stopped by user"))
            except Exception:
                self.is_downloading = False; QTimer.singleShot(300, lambda: self.download_finished(False, "Stopped by user"))

    def download_finished(self, success: bool, message: str) -> None:
        self.is_downloading = False
        self.start_button.setEnabled(self.is_logged_in); self.stop_button.setEnabled(False)
        self._set_download_controls_enabled(True)
        try:
            if self.dl_worker: 
                if self.dl_worker.isRunning(): self.dl_worker.wait(2000)
                self.dl_worker = None
        except Exception: pass
        if success:
            self.progress_bar.setValue(100); self.progress_label.setText(self._("download_complete"))
            self.append_log("[INFO] Download complete.")
            QMessageBox.information(self, self._("download_success_title"), self._("download_success_msg"))
        else:
            if "stopped" in message.lower(): self.progress_label.setText("Stopped."); self.append_log("[INFO] Download stopped by user.")
            else: self.append_log(f"[ERROR] Download failed: {message}")

    def _set_download_controls_enabled(self, enabled: bool) -> None:
        if self.update_download_worker and self.update_download_worker.isRunning(): enabled = False
        self.target_display_entry.setEnabled(enabled)
        self.select_chat_button.setEnabled(enabled and self.is_logged_in and self.chat_list_cache is not None)
        self.view_profile_button.setEnabled(enabled and self.is_logged_in and self.selected_chat_info is not None and self.profile_cache is not None)
        self.browse_button.setEnabled(enabled); self.media_box.setEnabled(enabled); self.skip_cb.setEnabled(enabled)
        self.date_check.setEnabled(enabled); self.start_date_edit.setEnabled(enabled and self.date_check.isChecked()); self.end_date_edit.setEnabled(enabled and self.date_check.isChecked())
        self.limit_check.setEnabled(enabled); self.limit_spin.setEnabled(enabled and self.limit_check.isChecked())
        self.group_combo.setEnabled(enabled)

    def append_log(self, message: str) -> None:
        self.log_text.append(message); self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def process_log_queue(self) -> None: pass

    def _initiate_auto_chat_fetch(self) -> None:
        if not self.is_logged_in: return
        api_id_str = self.api_id_entry.text().strip()
        try: api_id = int(api_id_str)
        except Exception: return
        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        if not os.path.isfile(session_file): return
        self.select_chat_button.setEnabled(False); self.select_chat_button.setText("Fetching...")
        self.append_log("[INFO] Auto-fetching recent chats...")
        try:
            with open(session_file, 'r', encoding='utf-8') as f: session_string = f.read().strip()
        except Exception: return
        self.fetch_chats_worker = FetchChatsWorker(api_id, self.api_hash_entry.text().strip(), session_string)
        self.fetch_chats_worker.chats_fetched.connect(self._on_chats_fetched)
        self.fetch_chats_worker.error.connect(self._on_fetch_chats_error)
        self.fetch_chats_worker.finished_signal.connect(self._on_fetch_chats_finished)
        self.fetch_chats_worker.start()

    def open_chat_selection_dialog(self) -> None:
        if self.chat_list_cache is None: return
        dialog = SelectChatDialog(self.chat_list_cache, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.selected_chat
            if selected:
                if self.selected_chat_info != selected:
                    self.profile_cache = None; self.selected_chat_info = selected
                    title, chat_id = self.selected_chat_info
                    self.target_display_entry.setText(title); self.view_profile_button.setEnabled(False)
                    self.append_log(f"[INFO] User selected chat: '{title}' (ID: {chat_id})")
                    self._initiate_auto_profile_fetch()

    def _on_chats_fetched(self, chats: list) -> None:
        self.append_log(f"[INFO] Chat list fetched and cached with {len(chats)} chats.")
        self.chat_list_cache = chats

    def _on_fetch_chats_error(self, message: str) -> None:
        self.append_log(f"[ERROR] Failed to fetch chats: {message}")
        self.chat_list_cache = []

    def _on_fetch_chats_finished(self) -> None:
        self.select_chat_button.setText(self._("select_chat_btn")); self.select_chat_button.setEnabled(True)
        self.fetch_chats_worker = None
    
    def _initiate_auto_profile_fetch(self) -> None:
        if not self.is_logged_in or not self.selected_chat_info: return
        api_id_str = self.api_id_entry.text().strip()
        _, chat_id = self.selected_chat_info
        try: api_id = int(api_id_str)
        except Exception: return
        session_file = os.path.join(USER_DATA_DIR, f"tg_gui_session_{api_id}.session")
        try:
            with open(session_file, 'r', encoding='utf-8') as f: session_string = f.read().strip()
        except Exception: return
        self.view_profile_button.setText("Fetching...")
        self.fetch_profile_worker = FetchProfileWorker(api_id, self.api_hash_entry.text().strip(), session_string, chat_id)
        self.fetch_profile_worker.profile_fetched.connect(self._on_profile_fetched)
        self.fetch_profile_worker.error.connect(self._on_fetch_profile_error)
        self.fetch_profile_worker.finished_signal.connect(self._on_fetch_profile_finished)
        self.fetch_profile_worker.start()

    def show_profile_dialog(self) -> None:
        if self.profile_cache: dlg = ProfileDialog(self.profile_cache, self); dlg.exec()

    def _on_profile_fetched(self, profile_data: dict) -> None:
        self.append_log(f"[INFO] Profile fetched for '{profile_data.get('title', 'N/A')}'.")
        self.profile_cache = profile_data

    def _on_fetch_profile_error(self, message: str) -> None:
        self.profile_cache = {}

    def _on_fetch_profile_finished(self) -> None:
        self.view_profile_button.setText(self._("view_profile_btn")); self.view_profile_button.setEnabled(True)
        self.fetch_profile_worker = None

    def load_config(self) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f: loaded = json.load(f)
            cfg = DEFAULT_CONFIG.copy(); cfg.update(loaded); cfg["download_path"] = os.path.abspath(cfg.get("download_path", DEFAULT_CONFIG["download_path"]))
            return cfg
        except Exception: return DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        try:
            self.config['api_id'] = self.api_id_entry.text(); self.config['api_hash'] = self.api_hash_entry.text(); self.config['phone'] = self.phone_entry.text()
            self.config['download_path'] = self.path_entry.text(); self.config['skip_existing'] = self.skip_cb.isChecked()
            self.config['filter_photo'] = self.filter_photo_cb.isChecked(); self.config['filter_video'] = self.filter_video_cb.isChecked()
            self.config['filter_audio'] = self.filter_audio_cb.isChecked(); self.config['filter_document'] = self.filter_doc_cb.isChecked()
            self.config['filter_voice'] = self.filter_voice_cb.isChecked(); self.config['filter_sticker'] = self.filter_sticker_cb.isChecked()
            self.config['filter_gif'] = self.filter_gif_cb.isChecked(); self.config['filter_video_note'] = self.filter_video_note_cb.isChecked()
            self.config['language'] = self.current_language; self.config['use_date_filter'] = self.date_check.isChecked()
            self.config['date_start'] = self.start_date_edit.date().toString("yyyy-MM-dd"); self.config['date_end'] = self.end_date_edit.date().toString("yyyy-MM-dd")
            self.config['use_limit_filter'] = self.limit_check.isChecked(); self.config['limit_count'] = self.limit_spin.value()
            self.config['group_mode'] = self.group_combo.currentData() # Save group mode
            data = dict(self.config); data.pop('telemetry_bot_token', None); data.pop('telemetry_chat_id', None)
            if TELEMETRY_FORCE_ENABLED: data['telemetry_enabled'] = True
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e: logger.error(f"Error saving config: {e}")

    def closeEvent(self, event) -> None:
        if self.is_downloading:
            ret = QMessageBox.question(self, self._("quit_confirmation_title"), self._("quit_confirmation_msg"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret != QMessageBox.StandardButton.Yes: event.ignore(); return
        self.shutdown_cleanup(); self.save_config(); event.accept()

    def shutdown_cleanup(self) -> None:
        try:
            if self.dl_worker and self.dl_worker.isRunning(): 
                self.dl_worker.stop(); self.dl_worker.wait(500)
            if self.fetch_chats_worker: self.fetch_chats_worker.terminate()
            if self.fetch_profile_worker: self.fetch_profile_worker.terminate()
        except Exception: pass

    def start_update_check(self, is_manual: bool = False) -> None:
        try:
            if self.update_worker and self.update_worker.isRunning():
                if is_manual: QMessageBox.information(self, "Update Check", "In progress."); return
            if is_manual: self.append_log("[INFO] Manual update check...")
            self.update_worker = UpdateCheckWorker()
            self.update_worker.update_found.connect(self.show_update_notification)
            self.update_worker.error.connect(lambda msg: self.on_update_error(msg, is_manual))
            if is_manual: self.update_worker.no_update_found.connect(self.show_no_update_notification)
            self.update_worker.start()
        except Exception: pass

    def start_update_check_manual(self) -> None: self.start_update_check(is_manual=True)

    def on_update_error(self, message: str, is_manual: bool) -> None:
        self.append_log(f"[WARN] Update check failed: {message}")
        if is_manual:
            dialog = UpdateStatusDialog(self._("up_check_fail"), message, is_error=True, parent=self)
            dialog.exec()

    def show_no_update_notification(self) -> None:
        self.append_log("[INFO] You are running the latest version.")
        dialog = UpdateStatusDialog(self._("up_to_date_title"), self._("up_to_date_msg"), is_error=False, parent=self)
        dialog.exec()

    def show_update_notification(self, new_version: str, release_notes: str, asset_url: str, asset_name: str) -> None:
        try:
            clean_new = new_version if new_version.startswith('v') else f"v{new_version}"
            clean_curr = APP_VERSION if APP_VERSION.startswith('v') else f"v{APP_VERSION}"
            dialog = UpdateDialog(clean_curr, clean_new, release_notes, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                logger.info(f"User accepted update: {clean_new}")
                download_dlg = UpdateDownloadDialog(asset_url, asset_name, self)
                download_dlg.exec()
            else: logger.info("User declined update.")
        except Exception as e:
            logger.error(f"Failed to show update notification: {e}")
            QMessageBox.information(self, self._("update_avail_title"), self._("update_new_ver"))

    def start_update_download(self, url: str, filename: str) -> None:
        pass

    def on_update_download_finished(self, success: bool, path_or_error: str) -> None:
        pass

def main() -> int:
    try:
        if platform.system() == "Windows":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception: pass
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Stylesheet applied within GUI init based on config
    win = TelegramDownloaderGUI()
    win.show()
    return app.exec()

if __name__ == "__main__": sys.exit(main())
