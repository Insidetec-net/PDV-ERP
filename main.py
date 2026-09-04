"""
Entry point do Sistema Meu Bazar.
"""

import sys
import os
import logging
from pathlib import Path

# Configurar locale
if sys.platform == 'darwin':
    os.environ.setdefault('LANG', 'en_US.UTF-8')
    os.environ.setdefault('LC_ALL', 'en_US.UTF-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("SistemaMeuBazar")


def main():
    from config.settings import APP_NAME, APP_VERSION, LOG_DIR, PROJECT_ROOT

    log_file = LOG_DIR / "sistema.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logging.getLogger().addHandler(file_handler)

    logger.info(f"Iniciando {APP_NAME} v{APP_VERSION}")

    from PyQt6.QtWidgets import QApplication, QMessageBox
    app = QApplication(sys.argv)

    from database.connection import test_connection
    if not test_connection():
        logger.error("MySQL não conectou.")
        from ui.setup_dialog import SetupDialog
        setup_dlg = SetupDialog()
        if setup_dlg.exec():
            if not test_connection():
                QMessageBox.critical(None, "Erro", "Conexão falhou.")
                sys.exit(1)
        else:
            sys.exit(1)

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    theme_path = PROJECT_ROOT / "ui/themes/dark_theme.qss"
    if theme_path.exists():
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    from ui.login_window import LoginWindow
    from ui.erp.erp_window import ERPWindow

    login_win = LoginWindow()
    active_windows = []

    def on_login_success(user_data: dict, mode: str):
        logger.info(f"Login: {user_data['login']} ({mode})")
        login_win.close()
        
        if mode == "erp":
            erp_win = ERPWindow(user_data)
            erp_win.logout_requested.connect(on_logout)
            erp_win.show()
            active_windows.append(erp_win)
        elif mode == "pdv":
            from ui.pdv.pdv_window import PDVWindow
            pdv_win = PDVWindow(user_data, on_logout)
            pdv_win.show()
            active_windows.append(pdv_win)

    def on_logout():
        for win in active_windows:
            try:
                win.close()
            except:
                pass
        active_windows.clear()
        
        login_win.login_input.clear()
        login_win.senha_input.clear()
        login_win.status_label.clear()
        login_win.login_btn.setVisible(True)
        login_win.login_btn.setEnabled(True)
        login_win.login_input.setEnabled(True)
        login_win.senha_input.setEnabled(True)
        login_win.mode_frame.setVisible(False)
        login_win.login_input.setFocus()
        login_win.show()

    login_win.login_success.connect(on_login_success)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
