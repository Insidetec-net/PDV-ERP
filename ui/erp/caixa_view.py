"""
View de Caixa — Turnos, sangrias, suprimentos e fluxo de caixa.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QSpacerItem, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTable
from models.caixa import CaixaModel
from utils.formatters import format_currency, format_datetime


class CaixaView(QWidget):
    """View de fluxo de caixa — turnos e movimentações."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.caixa_model = CaixaModel()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Tabela de Turnos ===
        self.table = DataTable(
            columns=[
                {"key": "id", "label": "#", "width": 60, "align": "center"},
                {"key": "abertura", "label": "Abertura", "width": 150,
                 "formatter": format_datetime},
                {"key": "fechamento", "label": "Fechamento", "width": 150,
                 "formatter": lambda v: format_datetime(v) if v else "— aberto —"},
                {"key": "valor_abertura", "label": "Fundo", "width": 100,
                 "formatter": format_currency, "align": "right"},
                {"key": "total_vendas", "label": "Vendas", "width": 110,
                 "formatter": format_currency, "align": "right"},
                {"key": "qtd_vendas", "label": "Qtd", "width": 60, "align": "center"},
                {"key": "total_sangrias", "label": "Sangrias", "width": 100,
                 "formatter": format_currency, "align": "right"},
                {"key": "total_suprimentos", "label": "Suprim.", "width": 100,
                 "formatter": format_currency, "align": "right"},
                {"key": "diferenca", "label": "Diferença", "width": 100,
                 "formatter": lambda v: format_currency(v) if v is not None else "—",
                 "align": "right"},
                {"key": "status", "label": "Status", "width": 90, "align": "center",
                 "formatter": lambda v: "🟢 Aberto" if v == "aberto" else "⚫ Fechado"},
            ],
            page_size=20,
            show_actions=False,
        )
        layout.addWidget(self.table)

    def refresh(self):
        try:
            data = self.caixa_model.get_all(order_by="abertura DESC", limit=100)
            self.table.set_data(data)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar turnos:\n{e}")
