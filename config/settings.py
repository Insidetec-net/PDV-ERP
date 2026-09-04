"""
Configurações gerais do Sistema Meu Bazar.
Detecção automática de SO e caminhos multiplataforma.
"""

import os
import sys
import json
import platform
from pathlib import Path


def get_app_dir() -> Path:
    """
    Retorna o diretório de dados da aplicação, conforme o SO.
    - macOS: ~/Library/Application Support/SistemaMeuBazar/
    - Windows: %APPDATA%/SistemaMeuBazar/
    """
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    elif system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".local" / "share"

    app_dir = base / "SistemaMeuBazar"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_project_root() -> Path:
    """Retorna o diretório raiz do projeto."""
    return Path(__file__).resolve().parent.parent


# === Diretórios ===
PROJECT_ROOT = get_project_root()
APP_DIR = get_app_dir()
ASSETS_DIR = PROJECT_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
LOGO_DIR = ASSETS_DIR / "logo"
BACKUP_DIR = APP_DIR / "backups"
XML_DIR = APP_DIR / "xml_nfe"
LOG_DIR = APP_DIR / "logs"

# Criar diretórios se não existirem
for d in [ASSETS_DIR, ICONS_DIR, LOGO_DIR, BACKUP_DIR, XML_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# === Banco de Dados ===
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "sistema_meu_bazar",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "pool_name": "meu_bazar_pool",
    "pool_size": 10,
    "pool_reset_session": True,
    "autocommit": False,
    "use_pure": True,
}


# === Arquivo de configuração local (override) ===
CONFIG_FILE = APP_DIR / "config.json"


def load_local_config():
    """
    Carrega configurações locais do config.json (se existir).
    Permite sobrescrever host, porta, usuário e senha do MySQL
    sem alterar o código fonte.
    """
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                local = json.load(f)
                if "database" in local:
                    DB_CONFIG.update(local["database"])
        except (json.JSONDecodeError, IOError):
            pass


def save_local_config(db_config: dict = None):
    """Salva configurações locais no config.json."""
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    if db_config:
        config["database"] = db_config

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# Carregar config local ao importar o módulo
load_local_config()


# === Versão do Sistema ===
APP_NAME = "Sistema Meu Bazar"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Sistema de gestão para bazar físico — PDV + ERP"

# === Plataforma ===
IS_MACOS = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
PLATFORM = platform.system()
