"""
View de Configurações — White-label, dados da empresa, fiscal, sistema.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QGroupBox, QFormLayout, QMessageBox,
    QScrollArea, QFrame, QSpacerItem, QSizePolicy, QFileDialog,
    QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from models.configuracao import ConfiguracaoModel


class ConfigView(QWidget):
    """View de configurações do sistema (white-label)."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.config_model = ConfiguracaoModel()
        self._inputs = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Tabs ===
        tabs = QTabWidget()

        # --- Tab 1: Empresa ---
        empresa_tab = self._create_empresa_tab()
        tabs.addTab(empresa_tab, "🏢  Empresa")

        # --- Tab 2: Fiscal ---
        fiscal_tab = self._create_fiscal_tab()
        tabs.addTab(fiscal_tab, "📋  Fiscal")

        # --- Tab 3: Sistema ---
        sistema_tab = self._create_sistema_tab()
        tabs.addTab(sistema_tab, "⚙️  Sistema")

        layout.addWidget(tabs)

        # === Botão Salvar ===
        save_btn = QPushButton("💾  Salvar Configurações")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(48)
        save_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

    def _create_empresa_tab(self) -> QWidget:
        """Cria a tab de dados da empresa."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Logo
        logo_group = QGroupBox("Logo da Empresa")
        logo_layout = QVBoxLayout(logo_group)

        self.logo_preview = QLabel("Nenhuma logo definida")
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setMinimumHeight(80)
        self.logo_preview.setStyleSheet("color: #8888aa; background: transparent;")
        logo_layout.addWidget(self.logo_preview)

        logo_btn = QPushButton("📁  Selecionar Logo")
        logo_btn.setProperty("class", "secondary")
        logo_btn.clicked.connect(self._select_logo)
        logo_layout.addWidget(logo_btn)

        layout.addWidget(logo_group)

        # Dados cadastrais
        dados_group = QGroupBox("Dados Cadastrais")
        form = QFormLayout(dados_group)
        form.setSpacing(10)

        fields = [
            ("empresa_razao_social", "Razão Social *"),
            ("empresa_nome_fantasia", "Nome Fantasia *"),
            ("empresa_cnpj", "CNPJ *"),
            ("empresa_ie", "Inscrição Estadual"),
            ("empresa_im", "Inscrição Municipal"),
            ("empresa_telefone", "Telefone"),
            ("empresa_email", "E-mail"),
        ]

        for key, label in fields:
            inp = QLineEdit()
            inp.setMinimumHeight(36)
            self._inputs[key] = inp
            form.addRow(f"{label}:", inp)

        layout.addWidget(dados_group)

        # Endereço
        end_group = QGroupBox("Endereço")
        end_form = QFormLayout(end_group)
        end_form.setSpacing(10)

        end_fields = [
            ("empresa_endereco", "Logradouro"),
            ("empresa_numero", "Número"),
            ("empresa_complemento", "Complemento"),
            ("empresa_bairro", "Bairro"),
            ("empresa_cidade", "Cidade"),
            ("empresa_uf", "UF"),
            ("empresa_cep", "CEP"),
            ("empresa_codigo_municipio", "Cód. Município IBGE"),
        ]

        for key, label in end_fields:
            inp = QLineEdit()
            inp.setMinimumHeight(36)
            self._inputs[key] = inp
            end_form.addRow(f"{label}:", inp)

        layout.addWidget(end_group)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(widget)
        return scroll

    def _create_fiscal_tab(self) -> QWidget:
        """Cria a tab de configurações fiscais."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # API Fiscal
        api_group = QGroupBox("API Fiscal (Focus NFe)")
        api_form = QFormLayout(api_group)
        api_form.setSpacing(10)

        api_fields = [
            ("fiscal_api_token", "Token da API"),
            ("fiscal_csc_id", "ID do CSC"),
            ("fiscal_csc_token", "Token CSC"),
            ("fiscal_serie_nfce", "Série NFC-e"),
        ]

        for key, label in api_fields:
            inp = QLineEdit()
            inp.setMinimumHeight(36)
            if "token" in key.lower():
                inp.setEchoMode(QLineEdit.EchoMode.Password)
            self._inputs[key] = inp
            api_form.addRow(f"{label}:", inp)

        # Ambiente
        self.ambiente_combo = QComboBox()
        self.ambiente_combo.addItem("🧪 Homologação (teste)", "2")
        self.ambiente_combo.addItem("🏭 Produção", "1")
        self._inputs["fiscal_ambiente"] = self.ambiente_combo
        api_form.addRow("Ambiente:", self.ambiente_combo)

        layout.addWidget(api_group)

        # Tributação
        trib_group = QGroupBox("Tributação Padrão (Lucro Presumido)")
        trib_form = QFormLayout(trib_group)
        trib_form.setSpacing(10)

        # Regime
        regime_combo = QComboBox()
        regime_combo.addItem("3 — Lucro Presumido", "3")
        regime_combo.addItem("1 — Simples Nacional", "1")
        self._inputs["empresa_regime_tributario"] = regime_combo
        trib_form.addRow("Regime:", regime_combo)

        trib_fields = [
            ("fiscal_aliquota_icms", "Alíquota ICMS (%)"),
            ("fiscal_aliquota_pis", "Alíquota PIS (%)"),
            ("fiscal_aliquota_cofins", "Alíquota COFINS (%)"),
            ("fiscal_cst_icms_padrao", "CST ICMS Padrão"),
            ("fiscal_cst_pis_padrao", "CST PIS Padrão"),
            ("fiscal_cst_cofins_padrao", "CST COFINS Padrão"),
            ("fiscal_cfop_padrao", "CFOP Padrão"),
        ]

        for key, label in trib_fields:
            inp = QLineEdit()
            inp.setMinimumHeight(36)
            self._inputs[key] = inp
            trib_form.addRow(f"{label}:", inp)

        layout.addWidget(trib_group)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(widget)
        return scroll

    def _create_sistema_tab(self) -> QWidget:
        """Cria a tab de configurações do sistema."""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        sys_group = QGroupBox("Preferências do Sistema")
        sys_form = QFormLayout(sys_group)
        sys_form.setSpacing(10)

        sys_fields = [
            ("sistema_markup_padrao", "Markup Padrão (%)"),
            ("sistema_estoque_minimo", "Estoque Mínimo Padrão"),
            ("sistema_backup_horario", "Horário do Backup"),
        ]

        for key, label in sys_fields:
            inp = QLineEdit()
            inp.setMinimumHeight(36)
            self._inputs[key] = inp
            sys_form.addRow(f"{label}:", inp)

        # Impressão
        imp_fields = [
            ("impressao_impressora", "Impressora Padrão"),
            ("impressao_largura_cupom", "Largura Cupom (mm)"),
        ]

        for key, label in imp_fields:
            inp = QLineEdit()
            inp.setMinimumHeight(36)
            self._inputs[key] = inp
            sys_form.addRow(f"{label}:", inp)

        layout.addWidget(sys_group)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        return widget

    def refresh(self):
        """Carrega valores atuais do banco."""
        try:
            configs = self.config_model.get_all_as_dict()
            for key, inp in self._inputs.items():
                value = configs.get(key, "")
                if isinstance(inp, QComboBox):
                    idx = inp.findData(value)
                    if idx >= 0:
                        inp.setCurrentIndex(idx)
                elif isinstance(inp, QLineEdit):
                    inp.setText(value or "")

            # Logo preview
            logo_path = configs.get("empresa_logo_path", "")
            if logo_path:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    self.logo_preview.setPixmap(
                        pixmap.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
                    )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar configurações:\n{e}")

    def _select_logo(self):
        """Abre diálogo para selecionar logo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Logo",
            "", "Imagens (*.png *.jpg *.jpeg *.bmp)",
        )
        if file_path:
            self._inputs.setdefault("empresa_logo_path", QLineEdit())
            if isinstance(self._inputs.get("empresa_logo_path"), QLineEdit):
                self._inputs["empresa_logo_path"].setText(file_path)
            else:
                self._inputs["empresa_logo_path"] = file_path

            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.logo_preview.setPixmap(
                    pixmap.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
                )

            # Salvar imediatamente
            self.config_model.set_value("empresa_logo_path", file_path)

    def _on_save(self):
        """Salva todas as configurações."""
        try:
            updates = {}
            for key, inp in self._inputs.items():
                if isinstance(inp, QComboBox):
                    updates[key] = inp.currentData() or ""
                elif isinstance(inp, QLineEdit):
                    updates[key] = inp.text().strip()
                elif isinstance(inp, str):
                    updates[key] = inp

            self.config_model.update_batch(updates)
            QMessageBox.information(
                self, "Sucesso",
                "✅ Configurações salvas com sucesso!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{e}")
