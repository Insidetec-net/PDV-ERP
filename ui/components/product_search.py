"""
Widget de busca de produtos para o PDV.
Permite buscar por nome, código de barras ou código interno,
filtrar por categoria e selecionar um produto via teclado.

Sinais:
    product_selected(dict) — emitido quando o usuário seleciona um produto.
    search_closed()         — emitido quando o diálogo é fechado (Esc).
    advanced_filter()       — emitido quando o usuário pressiona F2.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QComboBox, QLabel, QHeaderView, QAbstractItemView,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QKeySequence, QShortcut


# ── Paleta do tema escuro ──────────────────────────────────────────────
BG          = "#0f0f23"
BG_ALT      = "#1a1a2e"
BG_HOVER    = "#252540"
BORDER      = "#2a2a4a"
TEXT        = "#e0e0e0"
TEXT_DIM    = "#888899"
ACCENT      = "#06d6a0"   # verde
ACCENT_BLUE = "#4361ee"   # azul
DANGER      = "#ef476f"   # vermelho


class ProductSearchWidget(QWidget):
    """Diálogo embutido de busca rápida de produtos."""

    product_selected = pyqtSignal(dict)
    search_closed    = pyqtSignal()
    advanced_filter  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Produto")
        self.setMinimumSize(720, 480)
        self._products: list[dict] = []
        self._categories: list[str] = []
        self._selected_index = -1

        self._build_ui()
        self._apply_styles()
        self._setup_shortcuts()

    # ── Construção da UI ────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ── Linha de busca ──────────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Buscar por nome, código de barras ou código interno…"
        )
        self.search_input.setMinimumHeight(36)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_input, stretch=1)

        # ── ComboBox de categoria ───────────────────────────────────
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(36)
        self.category_combo.setMinimumWidth(160)
        self.category_combo.addItem("Todas as categorias")
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        search_row.addWidget(self.category_combo)

        root.addLayout(search_row)

        # ── Tabela de resultados ────────────────────────────────────
        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(
            ["Código", "Nome", "Preço", "Estoque"]
        )
        self.results_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.results_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setShowGrid(False)
        self.results_table.horizontalHeader().setStretchLastSection(False)
        self.results_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.results_table.doubleClicked.connect(self._on_double_click)
        root.addWidget(self.results_table, stretch=1)

        # ── Rodapé com dicas de teclado ─────────────────────────────
        hint = QLabel("Enter: selecionar  •  Esc: fechar  •  F2: filtro avançado")
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hint)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG};
                color: {TEXT};
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: {BG_ALT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {TEXT};
                selection-background-color: {ACCENT_BLUE};
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
            QComboBox {{
                background-color: {BG_ALT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {TEXT};
            }}
            QComboBox:focus {{
                border: 1px solid {ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_ALT};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {BG_HOVER};
            }}
            QTableWidget {{
                background-color: {BG_ALT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                gridline-color: transparent;
                selection-background-color: {BG_HOVER};
                selection-color: {TEXT};
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {BG_HOVER};
                color: {ACCENT};
            }}
            QHeaderView::section {{
                background-color: {BG};
                color: {TEXT_DIM};
                border: none;
                border-bottom: 2px solid {BORDER};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                background: {BG};
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {TEXT_DIM};
            }}
        """)

    def _setup_shortcuts(self):
        # Esc — fechar
        QShortcut(
            QKeySequence(Qt.Key.Key_Escape), self, self._on_escape
        )
        # F2 — filtro avançado
        QShortcut(
            QKeySequence(Qt.Key.Key_F2), self, self.advanced_filter.emit
        )

    # ── API pública ────────────────────────────────────────────────────

    def set_products(self, products: list[dict]):
        """
        Define a lista de produtos para busca.
        Cada dict deve ter as chaves:
            code (str), name (str), price (float), stock (int), category (str)
        """
        self._products = products
        self._update_categories()
        self._refresh_table()

    def focus_search(self):
        """Coloca o foco no campo de busca."""
        self.search_input.setFocus()
        self.search_input.selectAll()

    # ── Lógica de busca ────────────────────────────────────────────────

    def _on_search_changed(self, _text: str):
        # Debounce leve para não filtrar a cada tecla em listas grandes
        QTimer.singleShot(150, self._refresh_table)

    def _on_category_changed(self, _index: int):
        self._refresh_table()

    def _matches(self, product: dict) -> bool:
        query = self.search_input.text().strip().lower()
        if query:
            haystack = " ".join([
                str(product.get("code", "")),
                str(product.get("barcode", "")),
                str(product.get("name", "")),
            ]).lower()
            if query not in haystack:
                return False

        cat_idx = self.category_combo.currentIndex()
        if cat_idx > 0:
            selected_cat = self.category_combo.itemText(cat_idx)
            if product.get("category", "") != selected_cat:
                return False

        return True

    def _refresh_table(self):
        filtered = [p for p in self._products if self._matches(p)]

        self.results_table.setRowCount(len(filtered))
        for row, prod in enumerate(filtered):
            code_item   = QTableWidgetItem(str(prod.get("code", "")))
            name_item   = QTableWidgetItem(str(prod.get("name", "")))
            price_item  = QTableWidgetItem(
                f"R$ {prod.get('price', 0):.2f}"
            )
            stock_item  = QTableWidgetItem(str(prod.get("stock", 0)))

            # Alinhamento
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            price_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Cor do estoque baixo
            if prod.get("stock", 0) <= 5:
                stock_item.setForeground(QColor(DANGER))
                stock_item.setToolTip("Estoque baixo!")

            self.results_table.setItem(row, 0, code_item)
            self.results_table.setItem(row, 1, name_item)
            self.results_table.setItem(row, 2, price_item)
            self.results_table.setItem(row, 3, stock_item)

        self._selected_index = -1

    def _update_categories(self):
        cats = sorted({p.get("category", "") for p in self._products if p.get("category")})
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Todas as categorias")
        self.category_combo.addItems(cats)
        self.category_combo.blockSignals(False)

    # ── Ações de seleção ───────────────────────────────────────────────

    def _selected_product(self) -> dict | None:
        row = self.results_table.currentRow()
        if row < 0:
            return None
        filtered = [p for p in self._products if self._matches(p)]
        if row < len(filtered):
            return filtered[row]
        return None

    def _on_double_click(self):
        prod = self._selected_product()
        if prod:
            self.product_selected.emit(prod)
            self.search_closed.emit()

    def _on_escape(self):
        self.search_closed.emit()

    # ── Eventos de teclado ─────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            prod = self._selected_product()
            if prod:
                self.product_selected.emit(prod)
                self.search_closed.emit()
            elif self.results_table.rowCount() > 0:
                # Seleciona a primeira linha se nenhuma estiver selecionada
                self.results_table.selectRow(0)
        elif event.key() == Qt.Key.Key_Down:
            self._move_selection(1)
        elif event.key() == Qt.Key.Key_Up:
            self._move_selection(-1)
        else:
            super().keyPressEvent(event)

    def _move_selection(self, delta: int):
        row = self.results_table.currentRow()
        new_row = max(0, min(row + delta, self.results_table.rowCount() - 1))
        self.results_table.selectRow(new_row)


# ── Teste rápido ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    sample_products = [
        {"code": "P001", "name": "Camiseta Preta",   "price": 49.90, "stock": 25, "category": "Vestuário"},
        {"code": "P002", "name": "Calça Jeans",      "price": 129.00, "stock": 3,  "category": "Vestuário"},
        {"code": "P003", "name": "Tênis Esportivo",  "price": 299.90, "stock": 12, "category": "Calçados"},
        {"code": "P004", "name": "Meia Algodão",     "price": 14.90,  "stock": 80, "category": "Acessórios"},
        {"code": "P005", "name": "Boné Aba Reta",    "price": 39.90,  "stock": 2,  "category": "Acessórios"},
    ]

    w = ProductSearchWidget()
    w.set_products(sample_products)
    w.product_selected.connect(lambda p: print("Selecionado:", p))
    w.advanced_filter.connect(lambda: print("Filtro avançado"))
    w.search_closed.connect(lambda: print("Busca fechada"))
    w.show()
    w.focus_search()

    sys.exit(app.exec())
