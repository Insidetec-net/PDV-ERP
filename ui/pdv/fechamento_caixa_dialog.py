"""
Diálogo de Fechamento de Caixa.
Operador informa com quanto de dinheiro o caixa está encerrando.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDoubleSpinBox, QMessageBox, QFrame, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.caixa_service import CaixaService
from utils.formatters import format_currency


class FechamentoCaixaDialog(QDialog):
    """Diálogo para fechamento de turno de caixa."""

    def __init__(self, parent, turno_id: int):
        super().__init__(parent)
        self.turno_id = turno_id
        self.caixa_service = CaixaService()
        self.esperado_sistema = 0.0
        self._setup_ui()
        self._load_totals()

    def _setup_ui(self):
        self.setWindowTitle("Fechamento de Caixa")
        self.setFixedSize(450, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("🔒 Fechamento de Caixa")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #ef476f; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Resumo
        resumo_frame = QFrame()
        resumo_frame.setProperty("class", "card")
        resumo_layout = QFormLayout(resumo_frame)
        resumo_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.lbl_abertura = QLabel("R$ 0,00")
        self.lbl_vendas = QLabel("R$ 0,00")
        self.lbl_sangrias = QLabel("R$ 0,00")
        self.lbl_suprimentos = QLabel("R$ 0,00")
        self.lbl_sistema = QLabel("R$ 0,00")
        self.lbl_sistema.setStyleSheet("color: #06d6a0; font-weight: bold;")
        
        resumo_layout.addRow("Fundo Inicial (+):", self.lbl_abertura)
        resumo_layout.addRow("Vendas Dinheiro (+):", self.lbl_vendas)
        resumo_layout.addRow("Suprimentos (+):", self.lbl_suprimentos)
        resumo_layout.addRow("Sangrias (-):", self.lbl_sangrias)
        resumo_layout.addRow("Total no Sistema:", self.lbl_sistema)

        layout.addWidget(resumo_frame)

        desc = QLabel("Conte a gaveta e informe o valor total em DINHEIRO:")
        desc.setStyleSheet("color: #8888aa; background: transparent; margin-top: 8px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Input de valor
        self.valor_input = QDoubleSpinBox()
        self.valor_input.setPrefix("R$ ")
        self.valor_input.setDecimals(2)
        self.valor_input.setMaximum(99999.99)
        self.valor_input.setMinimumHeight(50)
        self.valor_input.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.valor_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.valor_input.valueChanged.connect(self._calculate_diff)
        layout.addWidget(self.valor_input)

        # Diferença
        self.lbl_diferenca = QLabel("Diferença: R$ 0,00")
        self.lbl_diferenca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_diferenca.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_diferenca)

        layout.addStretch()

        # Botões
        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        close_btn = QPushButton("🔒 Confirmar Fechamento")
        close_btn.setProperty("class", "danger")
        close_btn.setMinimumHeight(44)
        close_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_btn.clicked.connect(self._on_close)
        buttons.addWidget(close_btn)

        layout.addLayout(buttons)

    def _load_totals(self):
        try:
            self.turno_data = self.caixa_service.model.get_by_id(self.turno_id)
            if not self.turno_data:
                raise ValueError("Turno não encontrado.")
            
            # Busca o total real de vendas pagas em dinheiro durante o turno
            vendas_dinheiro = self.caixa_service.model.get_total_vendas_dinheiro(self.turno_id)
            
            self.lbl_abertura.setText(format_currency(self.turno_data['valor_abertura']))
            self.lbl_sangrias.setText(format_currency(self.turno_data['total_sangrias']))
            self.lbl_suprimentos.setText(format_currency(self.turno_data['total_suprimentos']))
            self.lbl_vendas.setText(format_currency(vendas_dinheiro))
            
            self.esperado_sistema = float(self.turno_data['valor_abertura']) + vendas_dinheiro + float(self.turno_data['total_suprimentos']) - float(self.turno_data['total_sangrias'])
            self.lbl_sistema.setText(format_currency(self.esperado_sistema))
            
            self.valor_input.setValue(self.esperado_sistema)
            self.valor_input.setFocus()
            self.valor_input.selectAll()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar totais do caixa:\n{e}")

    def _calculate_diff(self):
        informado = self.valor_input.value()
        diferenca = informado - self.esperado_sistema
        self.lbl_diferenca.setText(f"Diferença: {format_currency(diferenca)}")
        if diferenca < 0:
            self.lbl_diferenca.setStyleSheet("color: #ef476f;") # Quebra
        elif diferenca > 0:
            self.lbl_diferenca.setStyleSheet("color: #06d6a0;") # Sobra
        else:
            self.lbl_diferenca.setStyleSheet("color: #8888aa;") # Zerado

    def _on_close(self):
        """Encerra o caixa e registra a diferença."""
        informado = self.valor_input.value()
        diferenca = informado - self.esperado_sistema
        
        if diferenca != 0:
            reply = QMessageBox.question(
                self, "Atenção",
                f"O caixa apresenta uma diferença de {format_currency(diferenca)}.\nDeseja fechar mesmo assim?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            self.caixa_service.fechar_caixa(self.turno_id, informado)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível fechar o caixa:\n{e}")
