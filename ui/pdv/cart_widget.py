"""
Widget lateral do carrinho (PDV).
Exibe a lista de itens, subtotal, desconto e total.
Integra-se com a lista `carrinho` do PDVWindow via signals.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QFrame, QSizePolicy, QSpacerItem,
    QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from utils.formatters import format_currency, format_quantity


class CartWidget(QWidget):
    """
    Widget lateral de carrinho do PDV.

    Signals:
        item_removed(int): Emitido quando um item é removido (row index).
        cart_cleared(): Emitido quando o carrinho é limpo.
        item_double_clicked(int, dict): Emitido ao dar duplo clique em um item
            (row index, item dict) — usado para editar quantidade.
    """

    item_removed = pyqtSignal(int)
    cart_cleared = pyqtSignal()
    item_double_clicked = pyqtSignal(int, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._carrinho = []
        self._desconto = 0.0
        self._setup_ui()

    # ------------------------------------------------------------------ #
    #  UI Setup
    # ------------------------------------------------------------------ #

    def _setup_ui(self):
        self.setMinimumWidth(340)
        self.setStyleSheet("background-color: #1a1a2e; border-radius: 10px;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ---- Título ----
        title = QLabel("🛒 Carrinho")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        main_layout.addWidget(title)

        # ---- Tabela de itens ----
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Produto", "Qtd", "Subtotal"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.table.doubleClicked.connect(self._on_double_click)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0f0f23;
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                gridline-color: #2a2a4a;
                selection-background-color: rgba(67, 97, 238, 0.3);
                selection-color: #ffffff;
                alternate-background-color: #16213e;
            }
            QTableWidget::item { padding: 6px 8px; }
            QHeaderView::section {
                background-color: #16213e;
                color: #8888aa;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #4361ee;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.table.setMinimumHeight(280)
        main_layout.addWidget(self.table, stretch=1)

        # ---- Botões de ação ----
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_remove = QPushButton("❌ Remover")
        self.btn_remove.setProperty("class", "danger")
        self.btn_remove.setMinimumHeight(38)
        self.btn_remove.setStyleSheet(
            "QPushButton { background-color: #ef476f; color: #ffffff; "
            "border: none; border-radius: 6px; padding: 8px 14px; font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background-color: #d63d60; }"
            "QPushButton:pressed { background-color: #b83350; }"
            "QPushButton:disabled { background-color: #2a2a4a; color: #555577; }"
        )
        self.btn_remove.clicked.connect(self._remove_selected_item)

        self.btn_clear = QPushButton("🗑 Limpar")
        self.btn_clear.setProperty("class", "warning")
        self.btn_clear.setMinimumHeight(38)
        self.btn_clear.setStyleSheet(
            "QPushButton { background-color: #7209b7; color: #ffffff; "
            "border: none; border-radius: 6px; padding: 8px 14px; font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background-color: #5f07a0; }"
            "QPushButton:pressed { background-color: #4c0585; }"
            "QPushButton:disabled { background-color: #2a2a4a; color: #555577; }"
        )
        self.btn_clear.clicked.connect(self._clear_cart)

        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        main_layout.addLayout(btn_layout)

        # ---- Painel de totais ----
        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "QFrame { background-color: #16213e; border: 1px solid #2a2a4a; "
            "border-radius: 8px; padding: 8px; }"
        )
        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(12, 12, 12, 12)
        totals_layout.setSpacing(6)

        # Subtotal
        sub_row = QHBoxLayout()
        sub_label = QLabel("Subtotal:")
        sub_label.setStyleSheet("color: #8888aa; background: transparent; font-size: 13px;")
        self.lbl_subtotal = QLabel("R$ 0,00")
        self.lbl_subtotal.setFont(QFont("Segoe UI", 13))
        self.lbl_subtotal.setStyleSheet("color: #e0e0e0; background: transparent;")
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        sub_row.addWidget(sub_label)
        sub_row.addWidget(self.lbl_subtotal)
        totals_layout.addLayout(sub_row)

        # Desconto
        disc_row = QHBoxLayout()
        disc_label = QLabel("Desconto:")
        disc_label.setStyleSheet("color: #8888aa; background: transparent; font-size: 13px;")
        self.lbl_desconto = QLabel("- R$ 0,00")
        self.lbl_desconto.setFont(QFont("Segoe UI", 13))
        self.lbl_desconto.setStyleSheet("color: #ef476f; background: transparent;")
        self.lbl_desconto.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        disc_row.addWidget(disc_label)
        disc_row.addWidget(self.lbl_desconto)
        totals_layout.addLayout(disc_row)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2a2a4a; max-height: 1px;")
        totals_layout.addWidget(sep)

        # Total
        total_row = QHBoxLayout()
        total_label = QLabel("TOTAL:")
        total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.lbl_total = QLabel("R$ 0,00")
        self.lbl_total.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.lbl_total.setStyleSheet("color: #06d6a0; background: transparent;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_row.addWidget(total_label)
        total_row.addWidget(self.lbl_total)
        totals_layout.addLayout(total_row)

        main_layout.addWidget(totals_frame)

        # ---- Contador de itens ----
        self.lbl_count = QLabel("0 itens")
        self.lbl_count.setStyleSheet("color: #555577; background: transparent; font-size: 11px;")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_count)

        self._update_buttons_state()

    # ------------------------------------------------------------------ #
    #  Public API — integração com PDVWindow
    # ------------------------------------------------------------------ #

    def set_carrinho(self, carrinho: list):
        """
        Vincula a lista `carrinho` do PDVWindow.
        A referência é compartilhada — modificações externas devem chamar
        `refresh()` para atualizar a view.
        """
        self._carrinho = carrinho
        self.refresh()

    def add_item(self, item: dict):
        """
        Adiciona um item ao carrinho e atualiza a view.
        """
        self._carrinho.append(item)
        self.refresh()

    def refresh(self):
        """Re-renderiza a tabela com base em `self._carrinho`."""
        self.table.setRowCount(0)
        for idx, item in enumerate(self._carrinho):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(idx + 1).zfill(3)))
            self.table.setItem(idx, 1, QTableWidgetItem(item.get("nome", "")))
            qtd_item = QTableWidgetItem(format_quantity(item.get("qtd", 0)))
            qtd_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(idx, 2, qtd_item)
            sub = QTableWidgetItem(format_currency(item.get("subtotal", 0)))
            sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(idx, 3, sub)
            self.table.setRowHeight(idx, 34)

        self._update_totals()
        self._update_buttons_state()

    def set_desconto(self, valor: float):
        """Define o valor de desconto aplicado ao carrinho."""
        self._desconto = max(0.0, float(valor))
        self._update_totals()

    def clear(self):
        """Limpa o carrinho (remove todos os itens da lista vinculada)."""
        self._carrinho.clear()
        self._desconto = 0.0
        self.refresh()
        self.cart_cleared.emit()

    def get_selected_row(self) -> int:
        """Retorna o índice da linha selecionada ou -1."""
        return self.table.currentRow()

    def get_total(self) -> float:
        """Calcula o total (subtotal - desconto)."""
        subtotal = sum(i.get("subtotal", 0) for i in self._carrinho)
        return max(0.0, subtotal - self._desconto)

    def get_subtotal(self) -> float:
        """Calcula o bruto dos itens."""
        return sum(i.get("subtotal", 0) for i in self._carrinho)

    # ------------------------------------------------------------------ #
    #  Slots internos
    # ------------------------------------------------------------------ #

    def _remove_selected_item(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._carrinho):
            return
        self._carrinho.pop(row)
        self.refresh()
        self.item_removed.emit(row)

    def _clear_cart(self):
        self.clear()

    def _on_double_click(self, index):
        row = index.row()
        if 0 <= row < len(self._carrinho):
            self.item_double_clicked.emit(row, self._carrinho[row])

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _update_totals(self):
        subtotal = sum(i.get("subtotal", 0) for i in self._carrinho)
        total = max(0.0, subtotal - self._desconto)

        self.lbl_subtotal.setText(format_currency(subtotal))
        self.lbl_desconto.setText(f"- {format_currency(self._desconto)}")
        self.lbl_total.setText(format_currency(total))

    def _update_buttons_state(self):
        has_items = len(self._carrinho) > 0
        self.btn_remove.setEnabled(has_items)
        self.btn_clear.setEnabled(has_items)
