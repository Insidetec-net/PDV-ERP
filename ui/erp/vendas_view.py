"""
View de Vendas — Histórico e detalhes de vendas.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QFormLayout, QDateEdit, QMessageBox, QSpacerItem,
    QSizePolicy, QFrame, QTextEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTable
from models.venda import VendaModel
from utils.formatters import format_currency, format_datetime


class VendasView(QWidget):
    """View de histórico de vendas."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.venda_model = VendaModel()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Filtros de período ===
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Período:"))

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumHeight(38)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("até"))

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setMinimumHeight(38)
        filter_layout.addWidget(self.end_date)

        search_btn = QPushButton("🔍  Buscar")
        search_btn.setMinimumHeight(38)
        search_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(search_btn)

        filter_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # Cards de resumo
        self.total_label = QLabel("Total: R$ 0,00")
        self.total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #06d6a0; background: transparent;")
        filter_layout.addWidget(self.total_label)

        self.count_label_summary = QLabel("0 vendas")
        self.count_label_summary.setStyleSheet("color: #8888aa; background: transparent; margin-left: 16px;")
        filter_layout.addWidget(self.count_label_summary)

        layout.addLayout(filter_layout)

        # === Tabela ===
        self.table = DataTable(
            columns=[
                {"key": "id", "label": "#", "width": 60, "align": "center"},
                {"key": "criado_em", "label": "Data/Hora", "width": 150,
                 "formatter": format_datetime},
                {"key": "operador_nome", "label": "Operador", "width": 120},
                {"key": "subtotal", "label": "Subtotal", "width": 110,
                 "formatter": format_currency, "align": "right"},
                {"key": "desconto", "label": "Desconto", "width": 100,
                 "formatter": format_currency, "align": "right"},
                {"key": "total", "label": "Total", "width": 110,
                 "formatter": format_currency, "align": "right"},
                {"key": "status", "label": "Status", "width": 110, "align": "center",
                 "formatter": lambda v: "✅ Finalizada" if v == "finalizada" else "❌ Cancelada" if v == "cancelada" else "⏳ Contingência"},
                {"key": "nfce_chave", "label": "NFC-e", "width": 100, "align": "center",
                 "formatter": lambda v: "✅" if v else "—"},
            ],
            page_size=25,
        )
        self.table.add_action_button("👁️", self._on_view_details, "secondary", "Detalhes")
        self.table.add_action_button("❌", self._on_cancel, "danger", "Cancelar")

        layout.addWidget(self.table)

    def refresh(self):
        """Recarrega vendas do período."""
        try:
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()
            data = self.venda_model.get_sales_by_period(start, end)
            self.table.set_data(data)

            # Resumo
            total = sum(float(v.get("total", 0)) for v in data if v.get("status") == "finalizada")
            finalizadas = sum(1 for v in data if v.get("status") == "finalizada")
            self.total_label.setText(f"Total: {format_currency(total)}")
            self.count_label_summary.setText(f"{finalizadas} venda(s)")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar vendas:\n{e}")

    def _on_view_details(self, data: dict):
        """Mostra detalhes de uma venda."""
        try:
            details = self.venda_model.get_sale_details(data["id"])
            if not details:
                return

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Venda #{details['id']}")
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(500)

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(24, 20, 24, 20)

            header = QLabel(f"🛒 Venda #{details['id']}")
            header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            header.setStyleSheet("color: #ffffff; background: transparent;")
            layout.addWidget(header)

            # Info
            info = QTextEdit()
            info.setReadOnly(True)
            info.setStyleSheet("background-color: #16213e; border: 1px solid #2a2a4a; border-radius: 8px;")

            text = f"📅 Data: {format_datetime(details['criado_em'])}\n"
            text += f"👤 Operador: {details.get('operador_nome', '—')}\n"
            text += f"👥 Cliente: {details.get('cliente_nome', 'Consumidor Final')}\n"
            text += f"📊 Status: {details['status']}\n\n"
            text += "─── ITENS ───\n"

            for item in details.get("itens", []):
                text += f"  {item['produto_nome']}  ×{item['quantidade']}"
                text += f"  {format_currency(item['preco_unitario'])}"
                text += f"  = {format_currency(item['subtotal'])}\n"

            text += f"\n─── PAGAMENTO ───\n"
            for pgto in details.get("pagamentos", []):
                text += f"  {pgto['forma']}: {format_currency(pgto['valor'])}\n"

            text += f"\n{'─' * 30}\n"
            text += f"  Subtotal: {format_currency(details['subtotal'])}\n"
            text += f"  Desconto: {format_currency(details['desconto'])}\n"
            text += f"  TOTAL:    {format_currency(details['total'])}\n"
            text += f"  Troco:    {format_currency(details['troco'])}\n"

            if details.get("nfce_chave"):
                text += f"\n─── NFC-e ───\n"
                text += f"  Chave: {details['nfce_chave']}\n"
                text += f"  Protocolo: {details.get('nfce_protocolo', '—')}\n"

            info.setPlainText(text)
            layout.addWidget(info)

            close_btn = QPushButton("Fechar")
            close_btn.setProperty("class", "secondary")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar detalhes:\n{e}")

    def _on_cancel(self, data: dict):
        """Cancela uma venda."""
        if data.get("status") != "finalizada":
            QMessageBox.information(self, "Aviso", "Apenas vendas finalizadas podem ser canceladas.")
            return

        reply = QMessageBox.question(
            self, "Cancelar Venda",
            f"Deseja cancelar a venda #{data['id']}?\n"
            "O estoque dos itens será revertido.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.venda_model.cancel_sale(data["id"], self.user["id"])
                if success:
                    QMessageBox.information(self, "Sucesso", "Venda cancelada com sucesso.")
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Aviso", "Não foi possível cancelar esta venda.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cancelar:\n{e}")
