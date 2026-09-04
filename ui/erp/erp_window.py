"""
Janela principal do ERP — Layout com sidebar de navegação.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QSpacerItem, QSizePolicy,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.erp.produtos_view import ProdutosView
from ui.erp.estoque_view import EstoqueView
from ui.erp.clientes_view import ClientesView
from ui.erp.vendas_view import VendasView
from ui.erp.caixa_view import CaixaView
from ui.erp.config_view import ConfigView


class ERPWindow(QMainWindow):
    """Janela principal do ERP com sidebar e views empilhadas."""

    logout_requested = pyqtSignal()

    # Definição dos módulos do menu
    MODULES = [
        {"id": "dashboard", "icon": "📊", "label": "Dashboard", "perfil_min": "operador"},
        {"id": "produtos",  "icon": "📦", "label": "Produtos",  "perfil_min": "gerente"},
        {"id": "estoque",   "icon": "📋", "label": "Estoque",   "perfil_min": "gerente"},
        {"id": "vendas",    "icon": "🛒", "label": "Vendas",    "perfil_min": "gerente"},
        {"id": "clientes",  "icon": "👥", "label": "Clientes",  "perfil_min": "gerente"},
        {"id": "caixa",     "icon": "💰", "label": "Caixa",     "perfil_min": "gerente"},
        {"id": "notas_entrada", "icon": "📥", "label": "Importar NF-e", "perfil_min": "gerente"},
        {"id": "relatorios", "icon": "📑", "label": "Relatórios", "perfil_min": "gerente"},
        {"id": "etiquetas",  "icon": "🏷️", "label": "Etiquetas", "perfil_min": "gerente"},
        {"id": "config",    "icon": "⚙️", "label": "Configurações", "perfil_min": "admin"},
    ]

    PERFIL_LEVEL = {"operador": 0, "gerente": 1, "admin": 2}

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.user_level = self.PERFIL_LEVEL.get(user_data.get("perfil", ""), 0)
        self._sidebar_buttons = {}
        self._current_module = None
        self._setup_ui()
        self._navigate_to("dashboard")

    def _setup_ui(self):
        from config.settings import APP_NAME, APP_VERSION
        self.setWindowTitle(f"{APP_NAME} — Retaguarda (ERP)")
        self.setMinimumSize(1200, 700)
        self.showMaximized()

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === SIDEBAR ===
        sidebar = QFrame()
        sidebar.setProperty("class", "sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(4)

        # Logo/Título
        title_frame = QFrame()
        title_frame.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(8, 0, 8, 0)

        app_title = QLabel("🏪 Meu Bazar")
        app_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #ffffff; background: transparent;")
        title_layout.addWidget(app_title)

        erp_badge = QLabel("RETAGUARDA")
        erp_badge.setStyleSheet(
            "color: #7209b7; font-size: 10px; font-weight: bold; "
            "letter-spacing: 2px; background: transparent;"
        )
        title_layout.addWidget(erp_badge)

        sidebar_layout.addWidget(title_frame)
        sidebar_layout.addSpacing(20)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2a2a4a; max-height: 1px;")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(12)

        # Botões do menu
        for module in self.MODULES:
            min_level = self.PERFIL_LEVEL.get(module["perfil_min"], 0)
            if self.user_level < min_level:
                continue

            btn = QPushButton(f"  {module['icon']}  {module['label']}")
            btn.setProperty("class", "sidebar-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(42)
            btn.clicked.connect(
                lambda checked, m=module["id"]: self._navigate_to(m)
            )
            sidebar_layout.addWidget(btn)
            self._sidebar_buttons[module["id"]] = btn

        sidebar_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Separador inferior
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #2a2a4a; max-height: 1px;")
        sidebar_layout.addWidget(sep2)
        sidebar_layout.addSpacing(8)

        # Info do usuário
        user_frame = QFrame()
        user_frame.setStyleSheet("background: transparent;")
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(8, 4, 8, 4)
        user_layout.setSpacing(2)

        user_name = QLabel(f"👤 {self.user.get('nome', 'Usuário')}")
        user_name.setStyleSheet("color: #e0e0e0; font-size: 13px; font-weight: bold; background: transparent;")
        user_layout.addWidget(user_name)

        perfil_map = {"operador": "Operador", "gerente": "Gerente", "admin": "Administrador"}
        user_perfil = QLabel(perfil_map.get(self.user.get("perfil", ""), ""))
        user_perfil.setStyleSheet("color: #8888aa; font-size: 11px; background: transparent;")
        user_layout.addWidget(user_perfil)

        sidebar_layout.addWidget(user_frame)
        sidebar_layout.addSpacing(8)

        # Botão sair
        logout_btn = QPushButton("🚪  Sair")
        logout_btn.setProperty("class", "danger")
        logout_btn.setMinimumHeight(38)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._on_logout)
        sidebar_layout.addWidget(logout_btn)

        main_layout.addWidget(sidebar)

        # === CONTENT AREA ===
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #0f0f23;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header bar
        self.header = QFrame()
        self.header.setFixedHeight(56)
        self.header.setStyleSheet(
            "background-color: #0f0f23; border-bottom: 1px solid #2a2a4a;"
        )
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        self.header_title = QLabel("Dashboard")
        self.header_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.header_title.setStyleSheet("color: #ffffff; background: transparent;")
        header_layout.addWidget(self.header_title)

        header_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        content_layout.addWidget(self.header)

        # Stacked widget para as views
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        main_layout.addWidget(content_frame)

        # === Criar views ===
        self._views = {}
        self._create_views()

    def _create_views(self):
        """Cria e adiciona todas as views ao stack."""
        from ui.erp.importacao_nfe_view import ImportacaoNFeView
        from ui.erp.relatorios_view import RelatoriosView
        from ui.erp.etiquetas_view import EtiquetasView

        # Dashboard (placeholder)
        dashboard = self._create_dashboard()
        self._add_view("dashboard", dashboard)

        # Produtos
        produtos_view = ProdutosView(self.user)
        self._add_view("produtos", produtos_view)

        # Estoque
        estoque_view = EstoqueView(self.user)
        self._add_view("estoque", estoque_view)

        # Vendas
        vendas_view = VendasView(self.user)
        self._add_view("vendas", vendas_view)

        # Clientes
        clientes_view = ClientesView(self.user)
        self._add_view("clientes", clientes_view)

        # Caixa
        caixa_view = CaixaView(self.user)
        self._add_view("caixa", caixa_view)

        # Notas Entrada
        nfe_view = ImportacaoNFeView(self.user)
        self._add_view("notas_entrada", nfe_view)

        # Relatorios
        relatorios_view = RelatoriosView(self.user)
        self._add_view("relatorios", relatorios_view)

        # Etiquetas
        etiquetas_view = EtiquetasView(self.user)
        self._add_view("etiquetas", etiquetas_view)

        # Configurações
        if self.user_level >= self.PERFIL_LEVEL["admin"]:
            config_view = ConfigView(self.user)
            self._add_view("config", config_view)

    def _add_view(self, module_id: str, widget: QWidget):
        """Adiciona uma view ao stack."""
        self._views[module_id] = widget
        self.stack.addWidget(widget)

    def _create_dashboard(self) -> QWidget:
        """Cria o dashboard com cards de resumo."""
        from models.produto import ProdutoModel
        from models.configuracao import ConfiguracaoModel

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Greeting
        greeting = QLabel(f"Olá, {self.user.get('nome', '')}! 👋")
        greeting.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        greeting.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(greeting)

        subtitle = QLabel("Aqui está o resumo do seu negócio")
        subtitle.setStyleSheet("color: #8888aa; font-size: 14px; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        try:
            produto_model = ProdutoModel()
            total_produtos = produto_model.count(where="ativo = 1")
            low_stock = len(produto_model.get_low_stock())
            
            from models.relatorio import RelatorioModel
            from datetime import date
            from utils.formatters import format_currency
            
            relatorio = RelatorioModel()
            hoje = date.today().strftime('%Y-%m-%d')
            dados_hoje = relatorio.get_vendas_por_periodo(hoje, hoje)
            
            if dados_hoje:
                vendas_hoje = str(dados_hoje[0]['total_vendas'])
                faturamento_hoje = format_currency(dados_hoje[0]['receita_total'])
            else:
                vendas_hoje = "0"
                faturamento_hoje = "R$ 0,00"
                
            # Busca o faturamento acumulado (total)
            from database.connection import execute_query
            res_total = execute_query("SELECT SUM(total) as fat_total FROM vendas WHERE status = 'finalizada'")
            if res_total and res_total[0]['fat_total']:
                faturamento_total = format_currency(res_total[0]['fat_total'])
            else:
                faturamento_total = "R$ 0,00"
                
        except Exception as e:
            print(f"Erro ao carregar dash: {e}")
            total_produtos = 0
            low_stock = 0
            vendas_hoje = "0"
            faturamento_hoje = "R$ 0,00"
            faturamento_total = "R$ 0,00"

        cards_data = [
            ("📦", "Produtos Ativos", str(total_produtos), "#4361ee"),
            ("⚠️", "Estoque Baixo", str(low_stock), "#ef476f" if low_stock > 0 else "#06d6a0"),
            ("🛒", "Vendas Hoje", vendas_hoje, "#06d6a0"),
            ("💰", "Fat. do Dia", faturamento_hoje, "#fca311"),
            ("💎", "Faturamento Total", faturamento_total, "#ffd166"),
        ]

        for icon, title, value, color in cards_data:
            card = QFrame()
            card.setProperty("class", "card")
            card.setMinimumHeight(120)
            card.setStyleSheet(
                f"background-color: #1a1a2e; border: 1px solid #2a2a4a; "
                f"border-radius: 12px; border-left: 4px solid {color};"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 16, 20, 16)

            card_title = QLabel(f"{icon}  {title}")
            card_title.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
            card_layout.addWidget(card_title)

            card_value = QLabel(value)
            card_value.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
            card_value.setStyleSheet(f"color: {color}; background: transparent;")
            card_layout.addWidget(card_value)

            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        # Atalhos rápidos
        layout.addSpacing(16)
        shortcuts_label = QLabel("⚡ Atalhos Rápidos")
        shortcuts_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        shortcuts_label.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(shortcuts_label)

        shortcuts_layout = QHBoxLayout()
        shortcuts_layout.setSpacing(12)

        shortcuts = [
            ("📦 Novo Produto", "produtos"),
            ("📋 Ver Estoque", "estoque"),
            ("🛒 Histórico Vendas", "vendas"),
            ("⚙️ Configurações", "config"),
        ]

        for label, target in shortcuts:
            btn = QPushButton(label)
            btn.setProperty("class", "secondary")
            btn.setMinimumHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=target: self._navigate_to(t))
            shortcuts_layout.addWidget(btn)

        layout.addLayout(shortcuts_layout)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        return widget

    def _navigate_to(self, module_id: str):
        """Navega para um módulo."""
        if module_id not in self._views:
            return

        # Atualizar sidebar
        for mid, btn in self._sidebar_buttons.items():
            if mid == module_id:
                btn.setProperty("class", "sidebar-btn-active")
            else:
                btn.setProperty("class", "sidebar-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Atualizar header
        for mod in self.MODULES:
            if mod["id"] == module_id:
                self.header_title.setText(f"{mod['icon']}  {mod['label']}")
                break

        # Trocar view
        self.stack.setCurrentWidget(self._views[module_id])
        self._current_module = module_id

        # Refresh da view se tiver método refresh
        view = self._views[module_id]
        if hasattr(view, "refresh"):
            view.refresh()

    def _on_logout(self):
        """Logout — volta para a tela de login."""
        reply = QMessageBox.question(
            self, "Sair",
            "Deseja realmente sair do sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()
            self.close()
