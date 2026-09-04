"""
Widget de Informações do Turno (Caixa) no PDV.
Exibe dados do turno atual e permite sangria, suprimento e fechamento.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QDialog, QDoubleSpinBox,
    QLineEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent

from utils.formatters import format_currency, format_datetime


# === Diálogos de Movimentação de Caixa ===

class ValorMovimentacaoDialog(QDialog):
    """Diálogo genérico para informar valor de sangria/suprimento."""

    def __init__(self, parent, titulo: str, label_valor: str, label_motivo: str = "Motivo/Observação (opcional)"):
        super().__init__(parent)
        self.valor = 0.0
        self.motivo = ""
        self._setup_ui(titulo, label_valor, label_motivo)

    def _setup_ui(self, titulo: str, label_valor: str, label_motivo: str):
        self.setWindowTitle(titulo)
        self.setFixedSize(420, 280)
        self.setModal(True)
        self.setStyleSheet("background-color: #1a1a2e; color: #e0e0e0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Título
        title = QLabel(titulo)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #06d6a0; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Valor
        valor_lbl = QLabel(label_valor)
        valor_lbl.setStyleSheet("color: #8888aa; background: transparent;")
        layout.addWidget(valor_lbl)

        self.valor_input = QDoubleSpinBox()
        self.valor_input.setPrefix("R$ ")
        self.valor_input.setDecimals(2)
        self.valor_input.setMaximum(99999.99)
        self.valor_input.setMinimumHeight(48)
        self.valor_input.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.valor_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.valor_input.setStyleSheet(
            "background-color: #0f0f23; border: 1px solid #4361ee; border-radius: 6px;"
        )
        layout.addWidget(self.valor_input)

        # Motivo
        motivo_lbl = QLabel(label_motivo)
        motivo_lbl.setStyleSheet("color: #8888aa; background: transparent;")
        layout.addWidget(motivo_lbl)

        self.motivo_input = QLineEdit()
        self.motivo_input.setPlaceholderText("Ex: Troco, sangria para depósito...")
        self.motivo_input.setMinimumHeight(36)
        self.motivo_input.setStyleSheet(
            "background-color: #0f0f23; border: 1px solid #2a2a4a; border-radius: 6px; padding: 8px;"
        )
        layout.addWidget(self.motivo_input)

        layout.addStretch()

        # Botões
        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet(
            "background-color: #2a2a4a; color: #e0e0e0; padding: 8px; "
            "border-radius: 6px; font-weight: bold;"
        )
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirmar")
        confirm_btn.setMinimumHeight(44)
        confirm_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        confirm_btn.setStyleSheet(
            "background-color: #06d6a0; color: #000; padding: 8px; "
            "border-radius: 6px; font-weight: bold;"
        )
        confirm_btn.clicked.connect(self._on_confirm)
        buttons.addWidget(confirm_btn)

        layout.addLayout(buttons)

        self.valor_input.setFocus()
        self.valor_input.selectAll()

    def _on_confirm(self):
        self.valor = self.valor_input.value()
        self.motivo = self.motivo_input.text().strip()
        if self.valor <= 0:
            QMessageBox.warning(self, "Atenção", "Informe um valor maior que zero.")
            return
        self.accept()


# === Widget Principal do Turno ===

class TurnoWidget(QWidget):
    """
    Widget de informações do turno/caixa.

    Signals:
        sangria_requested: Emitido ao confirmar sangria (valor, motivo)
        suprimento_requested: Emitido ao confirmar suprimento (valor, motivo)
        fechar_turno_requested: Emitido ao solicitar fechamento do turno
    """

    sangria_requested = pyqtSignal(float, str)
    suprimento_requested = pyqtSignal(float, str)
    fechar_turno_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.turno_data = None
        self._setup_ui()

    def _setup_ui(self):
        """Constrói a interface do widget."""
        self.setProperty("class", "card")
        self.setStyleSheet("""
            #info_label { color: #8888aa; font-size: 11px; background: transparent; }
            #info_value { color: #e0e0e0; font-size: 13px; background: transparent; }
            #resumo_label { color: #06d6a0; font-size: 14px; font-weight: bold; background: transparent; }
            #resumo_value { color: #ffffff; font-size: 20px; font-weight: bold; background: transparent; }
            #status_aberto { color: #06d6a0; font-size: 12px; font-weight: bold; background: transparent; }
            #status_fechado { color: #ef476f; font-size: 12px; font-weight: bold; background: transparent; }
            QFrame#turno_frame {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 10px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Frame principal
        self.frame = QFrame()
        self.frame.setObjectName("turno_frame")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(16, 12, 16, 12)
        frame_layout.setSpacing(12)

        # === Cabeçalho ===
        header_layout = QHBoxLayout()
        self.turno_num_lbl = QLabel("Turno: ---")
        self.turno_num_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.turno_num_lbl.setStyleSheet("color: #4361ee; background: transparent;")
        header_layout.addWidget(self.turno_num_lbl)

        header_layout.addStretch()

        self.status_lbl = QLabel("● FECHADO")
        self.status_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_lbl.setStyleSheet("color: #ef476f; background: transparent;")
        header_layout.addWidget(self.status_lbl)

        frame_layout.addLayout(header_layout)

        # === Informações do Turno ===
        info_grid = QGridLayout()
        info_grid.setSpacing(6)

        # Linha 1: Operador
        operador_lbl = QLabel("Operador:")
        operador_lbl.setObjectName("info_label")
        info_grid.addWidget(operador_lbl, 0, 0)
        self.operador_val = QLabel("---")
        self.operador_val.setObjectName("info_value")
        info_grid.addWidget(self.operador_val, 0, 1)

        # Linha 2: Abertura
        abertura_lbl = QLabel("Abertura:")
        abertura_lbl.setObjectName("info_label")
        info_grid.addWidget(abertura_lbl, 1, 0)
        self.abertura_val = QLabel("---")
        self.abertura_val.setObjectName("info_value")
        info_grid.addWidget(self.abertura_val, 1, 1)

        frame_layout.addLayout(info_grid)

        # === Separador ===
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #2a2a4a; max-height: 1px;")
        frame_layout.addWidget(separator)

        # === Resumo do Turno ===
        resumo_title = QLabel("📊 RESUMO DO TURNO")
        resumo_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        resumo_title.setStyleSheet("color: #8888aa; background: transparent;")
        frame_layout.addWidget(resumo_title)

        resumo_grid = QGridLayout()
        resumo_grid.setSpacing(8)

        # Total Vendas
        total_vendas_lbl = QLabel("Total Vendas:")
        total_vendas_lbl.setObjectName("info_label")
        resumo_grid.addWidget(total_vendas_lbl, 0, 0)
        self.total_vendas_val = QLabel("R$ 0,00")
        self.total_vendas_val.setObjectName("resumo_value")
        self.total_vendas_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        resumo_grid.addWidget(self.total_vendas_val, 0, 1)

        # Qtd Vendas
        qtd_lbl = QLabel("Qtd Vendas:")
        qtd_lbl.setObjectName("info_label")
        resumo_grid.addWidget(qtd_lbl, 1, 0)
        self.qtd_vendas_val = QLabel("0")
        self.qtd_vendas_val.setObjectName("resumo_value")
        self.qtd_vendas_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        resumo_grid.addWidget(self.qtd_vendas_val, 1, 1)

        # Saldo Atual
        saldo_lbl = QLabel("Saldo Atual:")
        saldo_lbl.setObjectName("info_label")
        resumo_grid.addWidget(saldo_lbl, 2, 0)
        self.saldo_val = QLabel("R$ 0,00")
        self.saldo_val.setObjectName("resumo_value")
        self.saldo_val.setStyleSheet("color: #06d6a0; font-size: 22px; font-weight: bold; background: transparent;")
        self.saldo_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        resumo_grid.addWidget(self.saldo_val, 2, 1)

        frame_layout.addLayout(resumo_grid)

        # === Separador ===
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: #2a2a4a; max-height: 1px;")
        frame_layout.addWidget(separator2)

        # === Botões de Ação ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # Botão Sangria
        self.sangria_btn = QPushButton("💸 Sangria")
        self.sangria_btn.setMinimumHeight(40)
        self.sangria_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.sangria_btn.setStyleSheet(
            "QPushButton { background-color: #ef476f; color: #fff; border-radius: 6px; padding: 8px; }"
            "QPushButton:hover { background-color: #d63d5e; }"
            "QPushButton:pressed { background-color: #b5324f; }"
            "QPushButton:disabled { background-color: #2a2a4a; color: #555; }"
        )
        self.sangria_btn.clicked.connect(self._on_sangria_clicked)
        btn_layout.addWidget(self.sangria_btn)

        # Botão Suprimento
        self.suprimento_btn = QPushButton("💰 Suprimento")
        self.suprimento_btn.setMinimumHeight(40)
        self.suprimento_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.suprimento_btn.setStyleSheet(
            "QPushButton { background-color: #4361ee; color: #fff; border-radius: 6px; padding: 8px; }"
            "QPushButton:hover { background-color: #3a54cc; }"
            "QPushButton:pressed { background-color: #2f47a8; }"
            "QPushButton:disabled { background-color: #2a2a4a; color: #555; }"
        )
        self.suprimento_btn.clicked.connect(self._on_suprimento_clicked)
        btn_layout.addWidget(self.suprimento_btn)

        frame_layout.addLayout(btn_layout)

        # Botão Fechar Turno (F10)
        self.fechar_btn = QPushButton("🔒 Fechar Turno (F10)")
        self.fechar_btn.setMinimumHeight(48)
        self.fechar_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.fechar_btn.setStyleSheet(
            "QPushButton { background-color: #2a2a4a; color: #ef476f; border: 2px solid #ef476f; border-radius: 8px; }"
            "QPushButton:hover { background-color: #ef476f; color: #fff; }"
            "QPushButton:pressed { background-color: #b5324f; }"
            "QPushButton:disabled { background-color: #1a1a2e; color: #555; border-color: #2a2a4a; }"
        )
        self.fechar_btn.clicked.connect(self._on_fechar_clicked)
        frame_layout.addWidget(self.fechar_btn)

        main_layout.addWidget(self.frame)

        # Desabilita botões quando não há turno
        self._update_buttons_state()

    def set_turno(self, turno_id: int, user_id: int):
        """
        Define o turno atual pelo ID e user_id.
        Cria um turno_data mínimo para exibição; dados completos
        podem ser atualizados via update_turno().
        """
        turno_data = {
            "id": turno_id,
            "usuario_id": user_id,
            "status": "aberto",
            "abertura": None,
            "total_vendas": 0,
            "qtd_vendas": 0,
            "valor_abertura": 0,
            "total_sangrias": 0,
            "total_suprimentos": 0,
        }
        self.update_turno(turno_data)

    def update_turno(self, turno_data: dict, operador_nome: str = ""):
        """
        Atualiza os dados exibidos do turno.

        Args:
            turno_data: Dicionário com dados do turno (id, abertura, total_vendas, etc.)
            operador_nome: Nome do operador para exibição
        """
        self.turno_data = turno_data

        if not turno_data:
            self._clear_display()
            return

        # Número do turno
        turno_id = turno_data.get("id", "---")
        self.turno_num_lbl.setText(f"Turno #{turno_id}")

        # Operador
        if operador_nome:
            self.operador_val.setText(operador_nome)
        else:
            self.operador_val.setText(turno_data.get("operador", "---"))

        # Hora de abertura
        abertura = turno_data.get("abertura")
        if abertura:
            self.abertura_val.setText(format_datetime(abertura))
        else:
            self.abertura_val.setText("---")

        # Status
        status = turno_data.get("status", "fechado")
        if status == "aberto":
            self.status_lbl.setText("● ABERTO")
            self.status_lbl.setStyleSheet("color: #06d6a0; font-size: 12px; font-weight: bold; background: transparent;")
        else:
            self.status_lbl.setText("● FECHADO")
            self.status_lbl.setStyleSheet("color: #ef476f; font-size: 12px; font-weight: bold; background: transparent;")

        # Resumo
        total_vendas = float(turno_data.get("total_vendas", 0) or 0)
        qtd_vendas = int(turno_data.get("qtd_vendas", 0) or 0)
        valor_abertura = float(turno_data.get("valor_abertura", 0) or 0)
        total_sangrias = float(turno_data.get("total_sangrias", 0) or 0)
        total_suprimentos = float(turno_data.get("total_suprimentos", 0) or 0)

        # Saldo = abertura + vendas - sangrias + suprimentos
        saldo = valor_abertura + total_vendas - total_sangrias + total_suprimentos

        self.total_vendas_val.setText(format_currency(total_vendas))
        self.qtd_vendas_val.setText(str(qtd_vendas))
        self.saldo_val.setText(format_currency(saldo))

        # Cor do saldo baseado no valor
        if saldo >= 0:
            self.saldo_val.setStyleSheet("color: #06d6a0; font-size: 22px; font-weight: bold; background: transparent;")
        else:
            self.saldo_val.setStyleSheet("color: #ef476f; font-size: 22px; font-weight: bold; background: transparent;")

        self._update_buttons_state()

    def _clear_display(self):
        """Limpa a exibição quando não há turno."""
        self.turno_num_lbl.setText("Turno: ---")
        self.operador_val.setText("---")
        self.abertura_val.setText("---")
        self.status_lbl.setText("● FECHADO")
        self.status_lbl.setStyleSheet("color: #ef476f; font-size: 12px; font-weight: bold; background: transparent;")
        self.total_vendas_val.setText("R$ 0,00")
        self.qtd_vendas_val.setText("0")
        self.saldo_val.setText("R$ 0,00")
        self.saldo_val.setStyleSheet("color: #06d6a0; font-size: 22px; font-weight: bold; background: transparent;")
        self._update_buttons_state()

    def _update_buttons_state(self):
        """Atualiza estado dos botões baseado no turno."""
        has_turno = self.turno_data is not None and self.turno_data.get("status") == "aberto"
        self.sangria_btn.setEnabled(has_turno)
        self.suprimento_btn.setEnabled(has_turno)
        self.fechar_btn.setEnabled(has_turno)

    def _on_sangria_clicked(self):
        """Abre diálogo para sangria de caixa."""
        dialog = ValorMovimentacaoDialog(
            self,
            "💸 Sangria de Caixa",
            "Valor a retirar:",
            "Motivo (ex: depósito, troco, etc.)"
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sangria_requested.emit(dialog.valor, dialog.motivo)

    def _on_suprimento_clicked(self):
        """Abre diálogo para suprimento de caixa."""
        dialog = ValorMovimentacaoDialog(
            self,
            "💰 Suprimento de Caixa",
            "Valor a adicionar:",
            "Motivo (ex: troco, reforço de caixa)"
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.suprimento_requested.emit(dialog.valor, dialog.motivo)

    def _on_fechar_clicked(self):
        """Emite sinal de solicitação de fechamento do turno."""
        reply = QMessageBox.question(
            self,
            "Fechar Turno",
            "Deseja realmente fechar o turno atual?\n\n"
            "Esta ação encerra as operações de caixa.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.fechar_turno_requested.emit()

    def keyPressEvent(self, event: QKeyEvent):
        """Atalho F10 para fechar turno."""
        if event.key() == Qt.Key.Key_F10:
            if self.fechar_btn.isEnabled():
                self._on_fechar_clicked()
        else:
            super().keyPressEvent(event)
