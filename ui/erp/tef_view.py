"""
View de TEF (Transferência Eletrônica Financeira) — Listagem e gestão de transações de cartão.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QFormLayout, QDateEdit, QMessageBox, QSpacerItem,
    QSizePolicy, QFrame, QTextEdit, QComboBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTable
from database.connection import execute_query
from utils.formatters import format_currency, format_datetime


class TefView(QWidget):
    """View de transações TEF — cartões de crédito/débito."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Filtros ===
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #2a2a4a; "
            "border-radius: 8px;"
        )
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        filter_layout.addWidget(QLabel("Período:"))

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumHeight(36)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("até"))

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setMinimumHeight(36)
        filter_layout.addWidget(self.end_date)

        filter_layout.addWidget(QLabel("Bandeira:"))
        self.bandeira_combo = QComboBox()
        self.bandeira_combo.addItems([
            "Todas", "Visa", "Mastercard", "Elo", "Amex", "Hipercard", "Outros"
        ])
        self.bandeira_combo.setMinimumHeight(36)
        self.bandeira_combo.setMinimumWidth(140)
        filter_layout.addWidget(self.bandeira_combo)

        filter_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Todas", "Aprovada", "Cancelada"
        ])
        self.status_combo.setMinimumHeight(36)
        self.status_combo.setMinimumWidth(130)
        filter_layout.addWidget(self.status_combo)

        search_btn = QPushButton("🔍  Filtrar")
        search_btn.setMinimumHeight(36)
        search_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(search_btn)

        filter_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        layout.addWidget(filter_frame)

        # === Cards de Resumo ===
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)

        # Card Total Aprovado
        aprov_frame = QFrame()
        aprov_frame.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #2a2a4a; "
            "border-radius: 12px; border-left: 4px solid #06d6a0;"
        )
        aprov_layout = QVBoxLayout(aprov_frame)
        aprov_layout.setContentsMargins(20, 14, 20, 14)
        aprov_title = QLabel("✅  Total Aprovado")
        aprov_title.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        aprov_layout.addWidget(aprov_title)
        self.total_aprovado_label = QLabel("R$ 0,00")
        self.total_aprovado_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.total_aprovado_label.setStyleSheet("color: #06d6a0; background: transparent;")
        aprov_layout.addWidget(self.total_aprovado_label)
        summary_layout.addWidget(aprov_frame)

        # Card Total Cancelado
        cancel_frame = QFrame()
        cancel_frame.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #2a2a4a; "
            "border-radius: 12px; border-left: 4px solid #ef476f;"
        )
        cancel_layout = QVBoxLayout(cancel_frame)
        cancel_layout.setContentsMargins(20, 14, 20, 14)
        cancel_title = QLabel("❌  Total Cancelado")
        cancel_title.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        cancel_layout.addWidget(cancel_title)
        self.total_cancelado_label = QLabel("R$ 0,00")
        self.total_cancelado_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.total_cancelado_label.setStyleSheet("color: #ef476f; background: transparent;")
        cancel_layout.addWidget(self.total_cancelado_label)
        summary_layout.addWidget(cancel_frame)

        # Card Qtd Transações
        qtd_frame = QFrame()
        qtd_frame.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #2a2a4a; "
            "border-radius: 12px; border-left: 4px solid #4361ee;"
        )
        qtd_layout = QVBoxLayout(qtd_frame)
        qtd_layout.setContentsMargins(20, 14, 20, 14)
        qtd_title = QLabel("📊  Qtd Transações")
        qtd_title.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        qtd_layout.addWidget(qtd_title)
        self.qtd_label = QLabel("0")
        self.qtd_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.qtd_label.setStyleSheet("color: #4361ee; background: transparent;")
        qtd_layout.addWidget(self.qtd_label)
        summary_layout.addWidget(qtd_frame)

        # Card Líquido
        liquido_frame = QFrame()
        liquido_frame.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #2a2a4a; "
            "border-radius: 12px; border-left: 4px solid #fca311;"
        )
        liquido_layout = QVBoxLayout(liquido_frame)
        liquido_layout.setContentsMargins(20, 14, 20, 14)
        liquido_title = QLabel("💰  Líquido")
        liquido_title.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        liquido_layout.addWidget(liquido_title)
        self.liquido_label = QLabel("R$ 0,00")
        self.liquido_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.liquido_label.setStyleSheet("color: #fca311; background: transparent;")
        liquido_layout.addWidget(self.liquido_label)
        summary_layout.addWidget(liquido_frame)

        layout.addLayout(summary_layout)

        # === Tabela ===
        self.table = DataTable(
            columns=[
                {"key": "nsu", "label": "NSU", "width": 120, "align": "center"},
                {"key": "data_hora", "label": "Data/Hora", "width": 150,
                 "formatter": format_datetime},
                {"key": "bandeira", "label": "Bandeira", "width": 100, "align": "center"},
                {"key": "forma", "label": "Forma", "width": 110, "align": "center",
                 "formatter": self._format_forma},
                {"key": "valor", "label": "Valor", "width": 110,
                 "formatter": format_currency, "align": "right"},
                {"key": "parcelas", "label": "Parc.", "width": 50, "align": "center"},
                {"key": "autorizacao", "label": "Autorização", "width": 120, "align": "center"},
                {"key": "venda_id", "label": "Venda", "width": 60, "align": "center"},
                {"key": "status", "label": "Status", "width": 100, "align": "center",
                 "formatter": self._format_status},
            ],
            page_size=25,
        )
        self.table.add_action_button("🔍", self._on_consultar_nsu, "secondary", "Consultar NSU")
        self.table.add_action_button("↩️", self._on_cancelar, "danger", "Cancelar (Estorno)")

        layout.addWidget(self.table)

    def refresh(self):
        """Recarrega transações TEF com filtros aplicados."""
        try:
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()
            bandeira = self.bandeira_combo.currentText()
            status_filtro = self.status_combo.currentText()

            query = """
                SELECT
                    pv.nsu,
                    v.criado_em AS data_hora,
                    pv.bandeira,
                    pv.forma,
                    pv.valor,
                    pv.parcelas,
                    pv.autorizacao,
                    pv.venda_id,
                    v.status
                FROM pagamentos_venda pv
                INNER JOIN vendas v ON pv.venda_id = v.id
                WHERE pv.forma IN ('cartao_credito', 'cartao_debito')
                  AND DATE(v.criado_em) BETWEEN %s AND %s
            """
            params = [start, end]

            if bandeira != "Todas":
                query += " AND pv.bandeira = %s"
                params.append(bandeira)

            if status_filtro == "Aprovada":
                query += " AND v.status = 'finalizada'"
            elif status_filtro == "Cancelada":
                query += " AND v.status = 'cancelada'"

            query += " ORDER BY v.criado_em DESC"

            data = execute_query(query, tuple(params))
            self.table.set_data(data)

            # Resumo
            total_aprovado = sum(
                float(d["valor"]) for d in data if d["status"] == "finalizada"
            )
            total_cancelado = sum(
                float(d["valor"]) for d in data if d["status"] == "cancelada"
            )
            self.total_aprovado_label.setText(format_currency(total_aprovado))
            self.total_cancelado_label.setText(format_currency(total_cancelado))
            self.qtd_label.setText(str(len(data)))
            self.liquido_label.setText(format_currency(total_aprovado - total_cancelado))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar transações TEF:\n{e}")

    def _on_consultar_nsu(self, data: dict):
        """Consulta detalhes de uma transação pelo NSU."""
        nsu = data.get("nsu", "")
        if not nsu:
            QMessageBox.information(self, "Consulta NSU", "NSU não disponível para esta transação.")
            return

        try:
            query = """
                SELECT
                    pv.*,
                    v.criado_em,
                    v.total AS venda_total,
                    v.status AS venda_status,
                    u.nome AS operador_nome
                FROM pagamentos_venda pv
                INNER JOIN vendas v ON pv.venda_id = v.id
                INNER JOIN usuarios u ON v.usuario_id = u.id
                WHERE pv.nsu = %s
                  AND pv.forma IN ('cartao_credito', 'cartao_debito')
                LIMIT 1
            """
            result = execute_query(query, (nsu,))
            if not result:
                QMessageBox.warning(self, "Consulta NSU", f"Transação com NSU {nsu} não encontrada.")
                return

            row = result[0]

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Consulta NSU — {nsu}")
            dialog.setMinimumWidth(500)
            dialog.setMinimumHeight(400)

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(24, 20, 24, 20)

            header = QLabel(f"🔍 Transação NSU: {nsu}")
            header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            header.setStyleSheet("color: #ffffff; background: transparent;")
            layout.addWidget(header)

            info = QTextEdit()
            info.setReadOnly(True)
            info.setStyleSheet(
                "background-color: #16213e; border: 1px solid #2a2a4a; "
                "border-radius: 8px; color: #e0e0e0; font-size: 13px;"
            )

            texto = f"""NSU: {row['nsu']}
Data/Hora: {format_datetime(row['criado_em'])}
Bandeira: {row['bandeira'] or '—'}
Forma: {self._format_forma(row['forma'])}
Valor: {format_currency(row['valor'])}
Parcelas: {row['parcelas']}
Autorização: {row['autorizacao'] or '—'}

─── VENDA ───
Venda #{row['venda_id']}
Total Venda: {format_currency(row['venda_total'])}
Status: {self._format_status(row['venda_status'])}
Operador: {row['operador_nome'] or '—'}
"""
            info.setPlainText(texto)
            layout.addWidget(info)

            close_btn = QPushButton("Fechar")
            close_btn.setProperty("class", "secondary")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao consultar NSU:\n{e}")

    def _on_cancelar(self, data: dict):
        """Cancela (estorna) uma transação TEF."""
        nsu = data.get("nsu", "")
        status = data.get("status", "")

        if status == "cancelada":
            QMessageBox.information(
                self, "Aviso",
                "Esta transação já está cancelada."
            )
            return

        reply = QMessageBox.question(
            self, "Estornar Transação",
            f"Deseja realmente estornar a transação NSU {nsu}?\n"
            f"Valor: {format_currency(data.get('valor', 0))}\n\n"
            f"Isso cancelará a venda associada.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from database.connection import db_transaction

                venda_id = data.get("venda_id")

                with db_transaction() as (conn, cursor):
                    # Cancelar a venda
                    cursor.execute(
                        "UPDATE vendas SET status = 'cancelada' WHERE id = %s",
                        (venda_id,)
                    )

                QMessageBox.information(
                    self, "Sucesso",
                    f"Transação NSU {nsu} estornada com sucesso.\nVenda #{venda_id} cancelada."
                )
                self.refresh()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao estornar transação:\n{e}")

    @staticmethod
    def _format_status(status: str) -> str:
        """Formata o status com emoji."""
        if status == "finalizada":
            return "✅ Aprovada"
        elif status == "cancelada":
            return "❌ Cancelada"
        elif status == "contingencia":
            return "⏳ Contingência"
        return status or "—"

    @staticmethod
    def _format_forma(forma: str) -> str:
        """Forma de pagamento legível."""
        formas = {
            "cartao_credito": "💳 Crédito",
            "cartao_debito": "💳 Débito",
            "dinheiro": "💵 Dinheiro",
            "pix": "⚡ PIX",
            "cheque": "📄 Cheque",
            "outros": "📦 Outros",
        }
        return formas.get(forma, forma or "—")
