"""
View de Estoque — Movimentações, alertas e histórico.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QFormLayout, QDoubleSpinBox, QComboBox, QLineEdit,
    QMessageBox, QSpacerItem, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTable
from models.produto import ProdutoModel
from models.estoque import EstoqueModel
from utils.formatters import format_currency, format_datetime, format_quantity


class EstoqueView(QWidget):
    """View de gerenciamento de estoque."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.produto_model = ProdutoModel()
        self.estoque_model = EstoqueModel()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Toolbar ===
        toolbar = QHBoxLayout()

        entry_btn = QPushButton("📥  Entrada Manual")
        entry_btn.setMinimumHeight(40)
        entry_btn.setProperty("class", "success")
        entry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        entry_btn.clicked.connect(self._on_entry)
        toolbar.addWidget(entry_btn)

        adjust_btn = QPushButton("🔧  Ajuste de Inventário")
        adjust_btn.setProperty("class", "secondary")
        adjust_btn.setMinimumHeight(40)
        adjust_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        adjust_btn.clicked.connect(self._on_adjust)
        toolbar.addWidget(adjust_btn)

        toolbar.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # Toggle: estoque baixo vs todos
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("📋 Todos os Produtos", "all")
        self.filter_combo.addItem("⚠️ Estoque Baixo", "low")
        self.filter_combo.addItem("📜 Histórico Movimentações", "history")
        self.filter_combo.setMinimumWidth(220)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_combo)

        layout.addLayout(toolbar)

        # === Alerta de estoque baixo ===
        self.alert_frame = QFrame()
        self.alert_frame.setStyleSheet(
            "background-color: rgba(239, 71, 111, 0.1); "
            "border: 1px solid #ef476f; border-radius: 8px; padding: 12px;"
        )
        self.alert_frame.setVisible(False)
        alert_layout = QHBoxLayout(self.alert_frame)
        self.alert_label = QLabel("⚠️ Existem produtos com estoque baixo!")
        self.alert_label.setStyleSheet("color: #ef476f; font-weight: bold; background: transparent;")
        alert_layout.addWidget(self.alert_label)
        layout.addWidget(self.alert_frame)

        # === Tabela de Produtos com Estoque ===
        self.stock_table = DataTable(
            columns=[
                {"key": "codigo_interno", "label": "Código", "width": 100},
                {"key": "nome", "label": "Produto"},
                {"key": "unidade", "label": "UN", "width": 60, "align": "center"},
                {"key": "estoque_atual", "label": "Estoque Atual", "width": 120,
                 "formatter": lambda v: format_quantity(v) if v else "0", "align": "center"},
                {"key": "estoque_minimo", "label": "Mínimo", "width": 100,
                 "formatter": lambda v: format_quantity(v) if v else "0", "align": "center"},
                {"key": "preco_custo", "label": "Custo Unit.", "width": 110,
                 "formatter": format_currency, "align": "right"},
            ],
            page_size=30,
        )
        layout.addWidget(self.stock_table)

        # === Tabela de Histórico (oculta por padrão) ===
        self.history_table = DataTable(
            columns=[
                {"key": "criado_em", "label": "Data", "width": 140,
                 "formatter": format_datetime},
                {"key": "produto_nome", "label": "Produto"},
                {"key": "tipo", "label": "Tipo", "width": 120, "align": "center"},
                {"key": "quantidade", "label": "Qtd", "width": 80,
                 "formatter": lambda v: format_quantity(v), "align": "center"},
                {"key": "estoque_anterior", "label": "Antes", "width": 80,
                 "formatter": lambda v: format_quantity(v), "align": "center"},
                {"key": "estoque_posterior", "label": "Depois", "width": 80,
                 "formatter": lambda v: format_quantity(v), "align": "center"},
                {"key": "usuario_nome", "label": "Usuário", "width": 120},
                {"key": "observacao", "label": "Obs.", "width": 200},
            ],
            page_size=30,
            show_actions=False,
        )
        self.history_table.setVisible(False)
        layout.addWidget(self.history_table)

    def refresh(self):
        """Recarrega dados conforme o filtro selecionado."""
        filter_type = self.filter_combo.currentData()
        try:
            if filter_type == "low":
                data = self.produto_model.get_low_stock()
                self.stock_table.set_data(data)
                self.stock_table.setVisible(True)
                self.history_table.setVisible(False)
            elif filter_type == "history":
                data = self.estoque_model.get_history(limit=200)
                self.history_table.set_data(data)
                self.stock_table.setVisible(False)
                self.history_table.setVisible(True)
            else:
                data = self.produto_model.get_products_with_category(active_only=True)
                self.stock_table.set_data(data)
                self.stock_table.setVisible(True)
                self.history_table.setVisible(False)

            # Verificar alertas
            low = self.produto_model.get_low_stock()
            if low:
                self.alert_frame.setVisible(True)
                self.alert_label.setText(
                    f"⚠️ {len(low)} produto(s) com estoque abaixo do mínimo!"
                )
            else:
                self.alert_frame.setVisible(False)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar estoque:\n{e}")

    def _on_filter_changed(self):
        self.refresh()

    def _on_entry(self):
        """Abre diálogo de entrada manual de estoque."""
        dialog = StockMovementDialog(self, tipo="entrada", user=self.user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_adjust(self):
        """Abre diálogo de ajuste de inventário."""
        dialog = StockMovementDialog(self, tipo="ajuste", user=self.user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()


class StockMovementDialog(QDialog):
    """Diálogo para registrar movimentação de estoque."""

    def __init__(self, parent, tipo: str = "entrada", user: dict = None):
        super().__init__(parent)
        self.tipo = tipo
        self.user = user
        self.produto_model = ProdutoModel()
        self.estoque_model = EstoqueModel()
        self._selected_product = None
        self._setup_ui()

    def _setup_ui(self):
        title = "📥 Entrada de Estoque" if self.tipo == "entrada" else "🔧 Ajuste de Inventário"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QLabel(title)
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(12)

        # Busca de produto
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome ou código...")
        self.search_input.setMinimumHeight(40)
        self.search_input.returnPressed.connect(self._search_product)
        form.addRow("Produto:", self.search_input)

        self.product_label = QLabel("Nenhum produto selecionado")
        self.product_label.setStyleSheet("color: #8888aa; font-style: italic; background: transparent;")
        form.addRow("", self.product_label)

        # Quantidade
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setDecimals(3)
        self.qty_input.setMaximum(999999.999)
        self.qty_input.setMinimumHeight(38)
        form.addRow("Quantidade:", self.qty_input)

        # Observação
        self.obs_input = QLineEdit()
        self.obs_input.setPlaceholderText("Motivo da movimentação")
        self.obs_input.setMinimumHeight(38)
        form.addRow("Observação:", self.obs_input)

        layout.addLayout(form)

        # Botões
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Registrar")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(42)
        save_btn.clicked.connect(self._on_save)
        buttons.addWidget(save_btn)

        layout.addLayout(buttons)

    def _search_product(self):
        term = self.search_input.text().strip()
        if not term:
            return

        # Tentar por código primeiro
        product = self.produto_model.get_by_any_code(term)
        if not product:
            results = self.produto_model.search_products(term, limit=1)
            product = results[0] if results else None

        if product:
            self._selected_product = product
            self.product_label.setText(
                f"✅ {product['nome']} (Estoque: {format_quantity(product['estoque_atual'])})"
            )
            self.product_label.setStyleSheet("color: #06d6a0; background: transparent;")
        else:
            self._selected_product = None
            self.product_label.setText("❌ Produto não encontrado")
            self.product_label.setStyleSheet("color: #ef476f; background: transparent;")

    def _on_save(self):
        if not self._selected_product:
            QMessageBox.warning(self, "Aviso", "Selecione um produto.")
            return

        qty = self.qty_input.value()
        if qty <= 0:
            QMessageBox.warning(self, "Aviso", "Informe uma quantidade válida.")
            return

        try:
            self.estoque_model.register_movement(
                produto_id=self._selected_product["id"],
                usuario_id=self.user["id"],
                tipo=self.tipo,
                quantidade=qty,
                observacao=self.obs_input.text().strip() or None,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar:\n{e}")
