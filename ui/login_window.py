"""
Tela de Login — Autenticação e seleção PDV/ERP.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from models.usuario import UsuarioModel
from models.configuracao import ConfiguracaoModel


class LoginWindow(QWidget):
    """Tela de login com campos de usuário/senha e seleção PDV ou ERP."""

    login_success = pyqtSignal(dict, str)  # (user_data, mode: 'pdv'|'erp')

    def __init__(self):
        super().__init__()
        self.usuario_model = UsuarioModel()
        self.config_model = ConfiguracaoModel()
        self._authenticated_user = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Sistema Meu Bazar — Login")
        self.setFixedSize(480, 600)
        self.setProperty("class", "card")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)

        # === Logo / Título ===
        main_layout.addSpacerItem(
            QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Tentar carregar logo da empresa
        logo_path = self.config_model.get_value("empresa_logo_path") or ""
        if logo_path:
            try:
                logo_label = QLabel()
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    logo_label.setPixmap(
                        pixmap.scaledToHeight(80, Qt.TransformationMode.SmoothTransformation)
                    )
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    main_layout.addWidget(logo_label)
                    main_layout.addSpacing(16)
            except Exception:
                pass

        # Nome do sistema
        title = QLabel("🏪 Sistema Meu Bazar")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        main_layout.addWidget(title)

        # Nome da empresa (se configurado)
        empresa_nome = self.config_model.get_value("empresa_nome_fantasia") or ""
        if empresa_nome:
            empresa_label = QLabel(empresa_nome)
            empresa_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empresa_label.setStyleSheet("color: #4361ee; font-size: 14px; background: transparent;")
            main_layout.addWidget(empresa_label)

        main_layout.addSpacing(40)

        # === Formulário ===
        form_frame = QFrame()
        form_frame.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(16)

        # Login
        login_label = QLabel("Usuário")
        login_label.setStyleSheet("color: #8888aa; font-size: 12px; font-weight: bold; background: transparent;")
        form_layout.addWidget(login_label)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Digite seu login")
        self.login_input.setMinimumHeight(44)
        self.login_input.returnPressed.connect(lambda: self.senha_input.setFocus())
        form_layout.addWidget(self.login_input)

        # Senha
        senha_label = QLabel("Senha")
        senha_label.setStyleSheet("color: #8888aa; font-size: 12px; font-weight: bold; background: transparent;")
        form_layout.addWidget(senha_label)

        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Digite sua senha")
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha_input.setMinimumHeight(44)
        self.senha_input.returnPressed.connect(self._on_login)
        form_layout.addWidget(self.senha_input)

        main_layout.addWidget(form_frame)
        main_layout.addSpacing(24)

        # === Botão Login ===
        self.login_btn = QPushButton("🔐  Entrar")
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.login_btn.clicked.connect(self._on_login)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(self.login_btn)

        main_layout.addSpacing(16)

        # === Botões PDV / ERP (aparecem após login) ===
        self.mode_frame = QFrame()
        self.mode_frame.setStyleSheet("background: transparent;")
        self.mode_frame.setVisible(False)
        mode_layout = QHBoxLayout(self.mode_frame)
        mode_layout.setSpacing(12)

        self.pdv_btn = QPushButton("🛒  Abrir PDV")
        self.pdv_btn.setMinimumHeight(48)
        self.pdv_btn.setProperty("class", "success")
        self.pdv_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.pdv_btn.clicked.connect(lambda: self._open_mode("pdv"))
        self.pdv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mode_layout.addWidget(self.pdv_btn)

        self.erp_btn = QPushButton("📊  Abrir ERP")
        self.erp_btn.setMinimumHeight(48)
        self.erp_btn.setProperty("class", "accent")
        self.erp_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.erp_btn.clicked.connect(lambda: self._open_mode("erp"))
        self.erp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mode_layout.addWidget(self.erp_btn)

        main_layout.addWidget(self.mode_frame)

        # === Status ===
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #ef476f; font-size: 13px; background: transparent;")
        main_layout.addWidget(self.status_label)

        main_layout.addSpacerItem(
            QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Versão
        from config.settings import APP_VERSION
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #555577; font-size: 11px; background: transparent;")
        main_layout.addWidget(version_label)

        # Foco inicial
        self.login_input.setFocus()

    def _on_login(self):
        """Autentica o usuário."""
        login = self.login_input.text().strip()
        senha = self.senha_input.text().strip()

        if not login or not senha:
            self.status_label.setText("Preencha login e senha.")
            return

        self.status_label.setText("Autenticando...")
        self.login_btn.setEnabled(False)

        try:
            user = self.usuario_model.authenticate(login, senha)
        except Exception as e:
            self.status_label.setText(f"Erro de conexão: {e}")
            self.login_btn.setEnabled(True)
            return

        if user:
            self._authenticated_user = user
            self.status_label.setText("")
            self.status_label.setStyleSheet(
                "color: #06d6a0; font-size: 13px; background: transparent;"
            )
            self.status_label.setText(f"✅ Bem-vindo, {user['nome']}!")

            # Mostrar botões conforme perfil
            self.login_btn.setVisible(False)
            self.login_input.setEnabled(False)
            self.senha_input.setEnabled(False)
            self.mode_frame.setVisible(True)

            # Operador só pode abrir PDV
            if user["perfil"] == "operador":
                self.erp_btn.setEnabled(False)
                self.erp_btn.setToolTip("Acesso restrito ao administrador")
        else:
            self.status_label.setStyleSheet(
                "color: #ef476f; font-size: 13px; background: transparent;"
            )
            self.status_label.setText("❌ Login ou senha incorretos.")
            self.senha_input.clear()
            self.senha_input.setFocus()
            self.login_btn.setEnabled(True)

    def _open_mode(self, mode: str):
        """Emite sinal de login bem-sucedido com o modo selecionado."""
        if self._authenticated_user:
            # Verificar permissão para ERP
            if mode == "erp" and self._authenticated_user["perfil"] == "operador":
                QMessageBox.warning(
                    self, "Acesso Negado",
                    "Operadores de caixa não têm acesso ao ERP."
                )
                return
            self.login_success.emit(self._authenticated_user, mode)
