"""
Diálogo de Pagamento do PDV.
Suporta pagamentos múltiplos (ex: dinheiro + cartão), cálculo de troco
e finalização da venda.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent

from utils.formatters import format_currency
from services.venda_service import VendaService


class PagamentoDialog(QDialog):
    """Diálogo de finalização de venda."""

    def __init__(self, parent, user_id: int, turno_id: int, carrinho: list, total: float):
        super().__init__(parent)
        self.user_id = user_id
        self.turno_id = turno_id
        self.carrinho = carrinho
        self.total = total
        self.pagamentos = []  # Lista de dicts: {'forma': str, 'valor': float}
        self.falta_pagar = total
        self.venda_id = None
        self.troco = 0.0
        
        self.venda_service = VendaService()
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Pagamento")
        self.setFixedSize(650, 500)
        self.setModal(True)
        self.setStyleSheet("background-color: #0f0f23;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("💸 Finalizar Venda (Pagamento)")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(header)

        # Content split
        h_split = QHBoxLayout()
        h_split.setSpacing(20)

        # === ESQUERDA (Lançar Pagamento) ===
        left = QVBoxLayout()
        left.setSpacing(12)

        total_lbl = QLabel(f"Total: {format_currency(self.total)}")
        total_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        total_lbl.setStyleSheet("color: #06d6a0; background: transparent;")
        left.addWidget(total_lbl)

        self.falta_lbl = QLabel(f"Falta: {format_currency(self.falta_pagar)}")
        self.falta_lbl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.falta_lbl.setStyleSheet("color: #ef476f; background: transparent;")
        left.addWidget(self.falta_lbl)

        # Forma de Pagamento
        left.addWidget(QLabel("Forma (F2):"))
        self.forma_combo = QComboBox()
        self.forma_combo.addItems([
            "Dinheiro", "PIX", "Cartão de Crédito", "Cartão de Débito", "Crediário"
        ])
        self.forma_combo.setMinimumHeight(44)
        self.forma_combo.setFont(QFont("Segoe UI", 12))
        left.addWidget(self.forma_combo)

        # Valor
        left.addWidget(QLabel("Valor Recebido:"))
        self.valor_input = QDoubleSpinBox()
        self.valor_input.setPrefix("R$ ")
        self.valor_input.setDecimals(2)
        self.valor_input.setMaximum(99999.99)
        self.valor_input.setMinimumHeight(44)
        self.valor_input.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.valor_input.setValue(self.falta_pagar)
        self.valor_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        left.addWidget(self.valor_input)

        add_btn = QPushButton("Lançar (Enter)")
        add_btn.setProperty("class", "secondary")
        add_btn.setMinimumHeight(44)
        add_btn.clicked.connect(self._add_payment)
        left.addWidget(add_btn)

        left.addStretch()
        h_split.addLayout(left, stretch=4)

        # === DIREITA (Pagamentos Lançados e Troco) ===
        right = QVBoxLayout()
        right.setSpacing(12)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Forma", "Valor", ""])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        header_v = self.table.horizontalHeader()
        header_v.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_v.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_v.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        right.addWidget(self.table)

        self.troco_lbl = QLabel("Troco: R$ 0,00")
        self.troco_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.troco_lbl.setStyleSheet("color: #ffd166; background: transparent;")
        self.troco_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.troco_lbl)

        h_split.addLayout(right, stretch=6)
        layout.addLayout(h_split)

        # === BOTÕES FINAIS ===
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Voltar ao Caixa (Esc)")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(48)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.finalizar_btn = QPushButton("Finalizar Venda (F4)")
        self.finalizar_btn.setProperty("class", "success")
        self.finalizar_btn.setMinimumHeight(48)
        self.finalizar_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.finalizar_btn.clicked.connect(self._on_finalize)
        self.finalizar_btn.setEnabled(False)
        btn_layout.addWidget(self.finalizar_btn)

        layout.addLayout(btn_layout)

        # Focar no input de valor
        self.valor_input.setFocus()
        self.valor_input.selectAll()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F2:
            self.forma_combo.showPopup()
        elif event.key() == Qt.Key.Key_F4:
            if self.finalizar_btn.isEnabled():
                self._on_finalize()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.valor_input.hasFocus():
                self._add_payment()
            elif self.finalizar_btn.isEnabled():
                self._on_finalize()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _add_payment(self):
        valor = self.valor_input.value()
        if valor <= 0:
            return

        forma = self.forma_combo.currentText()
        
        # Mapear forma pro ENUM do banco
        forma_map = {
            "Dinheiro": "dinheiro",
            "PIX": "pix",
            "Cartão de Crédito": "credito",
            "Cartão de Débito": "debito",
            "Crediário": "crediario"
        }
        
        self.pagamentos.append({
            "forma": forma_map.get(forma, "dinheiro"),
            "valor": valor,
            "display": forma
        })
        self._update_payments()

    def _remove_payment(self, index: int):
        if 0 <= index < len(self.pagamentos):
            self.pagamentos.pop(index)
            self._update_payments()

    def _update_payments(self):
        self.table.setRowCount(0)
        total_pago = 0.0

        for i, pgto in enumerate(self.pagamentos):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(pgto["display"]))
            
            v_item = QTableWidgetItem(format_currency(pgto["valor"]))
            v_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, v_item)
            
            # Botão remover
            del_btn = QPushButton("❌")
            del_btn.setMaximumWidth(40)
            del_btn.setStyleSheet("color: red; border: none; background: transparent;")
            del_btn.clicked.connect(lambda checked, idx=i: self._remove_payment(idx))
            self.table.setCellWidget(i, 2, del_btn)
            
            total_pago += pgto["valor"]

        # Recalcular Falta / Troco
        if total_pago < self.total:
            self.falta_pagar = self.total - total_pago
            self.falta_lbl.setText(f"Falta: {format_currency(self.falta_pagar)}")
            self.falta_lbl.setStyleSheet("color: #ef476f; background: transparent;")
            self.troco_lbl.setText("Troco: R$ 0,00")
            self.finalizar_btn.setEnabled(False)
            
            self.valor_input.setValue(self.falta_pagar)
            self.valor_input.setFocus()
            self.valor_input.selectAll()
        else:
            self.falta_pagar = 0
            self.falta_lbl.setText("Falta: R$ 0,00")
            self.falta_lbl.setStyleSheet("color: #8888aa; background: transparent;")
            
            troco = total_pago - self.total
            self.troco_lbl.setText(f"Troco: {format_currency(troco)}")
            self.finalizar_btn.setEnabled(True)
            self.finalizar_btn.setFocus()

    def _on_finalize(self):
        """Finaliza a venda via VendaService (create_sale + NFC-e)."""
        try:
            # 1. Preparar itens
            itens = []
            for item in self.carrinho:
                itens.append({
                    "produto_id": item["id"],
                    "quantidade": item["qtd"],
                    "preco_unitario": item["v_unit"]
                })
            
            # 2. Preparar pagamentos (limpar 'display')
            pgtos_db = []
            for pgto in self.pagamentos:
                pgtos_db.append({
                    "forma": pgto["forma"],
                    "valor": pgto["valor"]
                })

            # 3. Finalizar venda via service (create_sale + NFC-e)
            result = self.venda_service.finalizar_venda(
                turno_id=self.turno_id,
                usuario_id=self.user_id,
                items=itens,
                pagamentos=pgtos_db,
                cliente_id=None,
                desconto=0.0,
            )
            
            venda_id = result["venda_id"]
            nfce_dados = result["nfce_dados"]
            self.venda_id = venda_id
            self.troco = max(0.0, total_pago - self.total)
            
            # 4. Mensagem de NFC-e
            msg_fiscal = ""
            if nfce_dados.get("status") in ("sucesso", "processando"):
                msg_fiscal = "\nNFC-e enviada com sucesso!"
            elif nfce_dados.get("status") == "nao_configurada":
                msg_fiscal = "\nNFC-e não configurada."
            else:
                msg_fiscal = f"\n⚠️ Falha na NFC-e: {nfce_dados.get('mensagem', 'Erro desconhecido')}"

            QMessageBox.information(
                self, "Venda Finalizada", 
                f"Venda {venda_id} concluída com sucesso!{msg_fiscal}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Finalizar", f"Houve um erro ao processar a venda:\n{e}")
