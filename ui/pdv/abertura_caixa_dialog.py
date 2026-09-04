"""
Diálogo de Abertura de Caixa.
Exigido antes do operador iniciar as vendas no PDV.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.caixa_service import CaixaService


class AberturaCaixaDialog(QDialog):
    """Diálogo para abertura de turno (fundo de troco)."""

    def __init__(self, parent, user_id: int):
        super().__init__(parent)
        self.user_id = user_id
        self.caixa_service = CaixaService()
        self.turno_id = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Abertura de Caixa")
        self.setFixedSize(400, 250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("💰 Abertura de Caixa")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #06d6a0; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Informe o valor do fundo de troco inicial:")
        desc.setStyleSheet("color: #8888aa; background: transparent;")
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
        layout.addWidget(self.valor_input)

        layout.addStretch()

        # Botões
        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        cancel_btn = QPushButton("Cancelar (Sair)")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        open_btn = QPushButton("🔓 Abrir Caixa")
        open_btn.setProperty("class", "success")
        open_btn.setMinimumHeight(44)
        open_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        open_btn.clicked.connect(self._on_open)
        buttons.addWidget(open_btn)

        layout.addLayout(buttons)
        
        self.valor_input.setFocus()
        self.valor_input.selectAll()

    def _on_open(self):
        """Abre o caixa e salva o turno."""
        valor = self.valor_input.value()
        try:
            self.turno_id = self.caixa_service.abrir_caixa(self.user_id, valor)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o caixa:\n{e}")
