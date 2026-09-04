"""
Widget de Visualização do Cupom Fiscal no PDV.
Exibe resumo da venda finalizada com opções de impressão, envio por e-mail
e fechamento (retorno ao PDV).
"""

import os
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from utils.formatters import format_currency
from services.fiscal_service import FiscalService


# Mapeamento interno para nomes legíveis de formas de pagamento
FORMA_PAGAMENTO_DISPLAY = {
    "dinheiro": "Dinheiro",
    "pix": "PIX",
    "credito": "Cartão de Crédito",
    "debito": "Cartão de Débito",
    "crediario": "Crediário",
}


class CupomWidget(QWidget):
    """
    Widget de visualização do cupom fiscal após finalização da venda.

    Signals:
        fechar_clicked: Emitido quando o usuário clica em "Fechar" (volta ao PDV).
    """

    fechar_clicked = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        venda_id: int = 0,
        itens: Optional[list] = None,
        pagamentos: Optional[list] = None,
        total: float = 0.0,
        troco: float = 0.0,
    ):
        super().__init__(parent)
        self.venda_id = venda_id
        self.itens = itens or []
        self.pagamentos = pagamentos or []
        self.total = total
        self.troco = troco

        self.fiscal_service = FiscalService()
        self._setup_ui()

    def _setup_ui(self):
        """Constrói a interface do widget."""
        self.setStyleSheet("background-color: #0f0f23;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # === HEADER ===
        header = QLabel("🧾 Cupom Fiscal — Venda Finalizada")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff; background: transparent;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Número da venda e data/hora
        info_lbl = QLabel(
            f"Venda #{self.venda_id} — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        info_lbl.setFont(QFont("Segoe UI", 11))
        info_lbl.setStyleSheet("color: #8888aa; background: transparent;")
        info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_lbl)

        # === TABELA DE ITENS ===
        itens_group = QGroupBox("Itens")
        itens_group.setStyleSheet(
            "QGroupBox { color: #e0e0e0; border: 1px solid #2a2a4a; "
            "border-radius: 6px; margin-top: 8px; font-weight: bold; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        itens_layout = QVBoxLayout(itens_group)

        self.itens_table = QTableWidget(0, 5)
        self.itens_table.setHorizontalHeaderLabels(["Item", "Produto", "Qtd", "V. Unit", "Subtotal"])
        self.itens_table.setAlternatingRowColors(True)
        self.itens_table.verticalHeader().setVisible(False)
        self.itens_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.itens_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.itens_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header_v = self.itens_table.horizontalHeader()
        header_v.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_v.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_v.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_v.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_v.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        itens_layout.addWidget(self.itens_table)

        main_layout.addWidget(itens_group)

        # === TOTAIS E PAGAMENTOS (HORIZONTAL) ===
        bottom_split = QHBoxLayout()
        bottom_split.setSpacing(16)

        # --- Totais (Esquerda) ---
        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "QFrame { background-color: #1a1a2e; border: 1px solid #2a2a4a; "
            "border-radius: 8px; }"
        )
        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(16, 16, 16, 16)

        ttl_header = QLabel("RESUMO")
        ttl_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        ttl_header.setStyleSheet("color: #8888aa; background: transparent;")
        totals_layout.addWidget(ttl_header)

        itens_count = sum(item.get("qtd", item.get("quantidade", 1)) for item in self.itens)
        count_lbl = QLabel(f"Total de itens: {itens_count:.0f}" if itens_count == int(itens_count) else f"Total de itens: {itens_count}")
        count_lbl.setFont(QFont("Segoe UI", 12))
        count_lbl.setStyleSheet("color: #e0e0e0; background: transparent;")
        totals_layout.addWidget(count_lbl)

        total_lbl = QLabel(format_currency(self.total))
        total_lbl.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        total_lbl.setStyleSheet("color: #06d6a0; background: transparent;")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_layout.addWidget(total_lbl)

        if self.troco > 0:
            troco_lbl = QLabel(f"Troco: {format_currency(self.troco)}")
            troco_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            troco_lbl.setStyleSheet("color: #ffd166; background: transparent;")
            troco_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            totals_layout.addWidget(troco_lbl)

        totals_layout.addStretch()
        bottom_split.addWidget(totals_frame, stretch=2)

        # --- Pagamentos (Direita) ---
        pgto_frame = QFrame()
        pgto_frame.setStyleSheet(
            "QFrame { background-color: #1a1a2e; border: 1px solid #2a2a4a; "
            "border-radius: 8px; }"
        )
        pgto_layout = QVBoxLayout(pgto_frame)
        pgto_layout.setContentsMargins(16, 16, 16, 16)

        pgto_header = QLabel("PAGAMENTOS")
        pgto_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        pgto_header.setStyleSheet("color: #8888aa; background: transparent;")
        pgto_layout.addWidget(pgto_header)

        for pgto in self.pagamentos:
            forma_key = pgto.get("forma", "dinheiro")
            forma_display = pgto.get("display", FORMA_PAGAMENTO_DISPLAY.get(forma_key, forma_key.upper()))
            valor = float(pgto.get("valor", 0))

            row = QHBoxLayout()
            nome_lbl = QLabel(forma_display)
            nome_lbl.setFont(QFont("Segoe UI", 12))
            nome_lbl.setStyleSheet("color: #e0e0e0; background: transparent;")
            row.addWidget(nome_lbl)

            row.addStretch()

            valor_lbl = QLabel(format_currency(valor))
            valor_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            valor_lbl.setStyleSheet("color: #06d6a0; background: transparent;")
            valor_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(valor_lbl)

            pgto_layout.addLayout(row)

        pgto_layout.addStretch()
        bottom_split.addWidget(pgto_frame, stretch=2)

        main_layout.addLayout(bottom_split)

        # === BOTÕES DE AÇÃO ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        # Botão Imprimir
        self.imprimir_btn = QPushButton("🖨️ Imprimir")
        self.imprimir_btn.setMinimumHeight(48)
        self.imprimir_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.imprimir_btn.setStyleSheet(
            "QPushButton { background-color: #06d6a0; color: #0f0f23; "
            "border: none; border-radius: 6px; padding: 8px 20px; } "
            "QPushButton:hover { background-color: #05b88a; } "
            "QPushButton:pressed { background-color: #04a078; }"
        )
        self.imprimir_btn.clicked.connect(self._on_imprimir)
        btn_layout.addWidget(self.imprimir_btn)

        # Botão Enviar por E-mail
        self.email_btn = QPushButton("📧 Enviar por E-mail")
        self.email_btn.setMinimumHeight(48)
        self.email_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.email_btn.setStyleSheet(
            "QPushButton { background-color: #4361ee; color: #ffffff; "
            "border: none; border-radius: 6px; padding: 8px 20px; } "
            "QPushButton:hover { background-color: #3a56d4; } "
            "QPushButton:pressed { background-color: #2f48b8; }"
        )
        self.email_btn.clicked.connect(self._on_enviar_email)
        btn_layout.addWidget(self.email_btn)

        # Botão Fechar
        self.fechar_btn = QPushButton("✓ Fechar")
        self.fechar_btn.setMinimumHeight(48)
        self.fechar_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.fechar_btn.setStyleSheet(
            "QPushButton { background-color: #ef476f; color: #ffffff; "
            "border: none; border-radius: 6px; padding: 8px 20px; } "
            "QPushButton:hover { background-color: #d63d63; } "
            "QPushButton:pressed { background-color: #be3457; }"
        )
        self.fechar_btn.clicked.connect(self._on_fechar)
        btn_layout.addWidget(self.fechar_btn)

        main_layout.addLayout(btn_layout)

        # Popula a tabela de itens
        self._populate_itens()

    def _populate_itens(self):
        """Preenche a tabela de itens com os dados da venda."""
        self.itens_table.setRowCount(0)
        for idx, item in enumerate(self.itens, start=1):
            row = self.itens_table.rowCount()
            self.itens_table.insertRow(row)

            # Número do item
            item_num = QTableWidgetItem(str(idx).zfill(3))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.itens_table.setItem(row, 0, item_num)

            # Nome do produto
            nome = item.get("nome", item.get("descricao", "PRODUTO"))
            self.itens_table.setItem(row, 1, QTableWidgetItem(nome))

            # Quantidade
            qtd = item.get("qtd", item.get("quantidade", 1))
            qtd_item = QTableWidgetItem(str(qtd))
            qtd_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.itens_table.setItem(row, 2, qtd_item)

            # Valor unitário
            v_unit = float(item.get("v_unit", item.get("preco_unitario", 0)))
            v_item = QTableWidgetItem(format_currency(v_unit))
            v_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.itens_table.setItem(row, 3, v_item)

            # Subtotal
            subtotal = float(item.get("subtotal", qtd * v_unit))
            sub_item = QTableWidgetItem(format_currency(subtotal))
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.itens_table.setItem(row, 4, sub_item)

    def _on_imprimir(self):
        """Gera PDF do cupom via FiscalService."""
        try:
            # Preparar itens no formato esperado pelo FiscalService
            itens_pdf = []
            for item in self.itens:
                itens_pdf.append({
                    "nome": item.get("nome", item.get("descricao", "PRODUTO")),
                    "quantidade": item.get("qtd", item.get("quantidade", 1)),
                    "preco_unitario": float(item.get("v_unit", item.get("preco_unitario", 0))),
                })

            # Preparar pagamentos no formato esperado
            pgtos_pdf = []
            for pgto in self.pagamentos:
                pgtos_pdf.append({
                    "forma": pgto.get("forma", "dinheiro"),
                    "valor": float(pgto.get("valor", 0)),
                })

            # Gerar PDF na Área de Trabalho
            filename = f"Cupom_Venda_{self.venda_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)

            self.fiscal_service.gerar_danfe_fake_pdf(
                venda_id=self.venda_id,
                itens=itens_pdf,
                pagamentos=pgtos_pdf,
                total=self.total,
                output_path=output_path,
            )

            QMessageBox.information(
                self,
                "Impressão",
                f"Cupom gerado com sucesso!\n\nArquivo: {output_path}",
            )

            # Tentar abrir o PDF gerado
            try:
                import platform
                import subprocess
                if platform.system() == "Darwin":
                    subprocess.call(("open", output_path))
                elif platform.system() == "Windows":
                    os.startfile(output_path)
                else:
                    subprocess.call(("xdg-open", output_path))
            except Exception:
                pass  # Falha ao abrir não é crítica

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na Impressão",
                f"Não foi possível gerar o PDF do cupom:\n{e}",
            )

    def _on_enviar_email(self):
        """Placeholder para envio de cupom por e-mail."""
        QMessageBox.information(
            self,
            "Enviar por E-mail",
            "Funcionalidade de envio por e-mail ainda não implementada.\n\n"
            "Em produção, o DANFE seria anexado e enviado ao cliente.",
        )

    def _on_fechar(self):
        """Emite sinal para retornar ao PDV."""
        self.fechar_clicked.emit()
