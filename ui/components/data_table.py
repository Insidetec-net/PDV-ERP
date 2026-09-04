"""
DataTable — Componente de tabela reutilizável com busca, paginação e ações.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QLabel, QHeaderView, QAbstractItemView,
    QComboBox, QSpacerItem, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List, Dict, Callable, Optional


class DataTable(QWidget):
    """
    Tabela genérica reutilizável com:
    - Busca por texto
    - Paginação
    - Botões de ação por linha
    - Formatação personalizada de colunas
    """

    row_selected = pyqtSignal(dict)  # Emitido ao clicar em uma linha
    row_double_clicked = pyqtSignal(dict)  # Emitido ao dar duplo clique

    def __init__(
        self,
        columns: List[Dict],
        page_size: int = 25,
        searchable: bool = True,
        show_actions: bool = True,
        parent=None,
    ):
        """
        Args:
            columns: Lista de dicts definindo as colunas.
                Cada dict tem: {key, label, width (opcional), formatter (opcional), align (opcional)}
            page_size: Itens por página.
            searchable: Mostrar campo de busca.
            show_actions: Mostrar coluna de ações.
        """
        super().__init__(parent)
        self.columns = columns
        self.page_size = page_size
        self.searchable = searchable
        self.show_actions = show_actions

        self._data: List[Dict] = []
        self._filtered_data: List[Dict] = []
        self._current_page = 0
        self._action_buttons: List[Dict] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # === Toolbar ===
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        if self.searchable:
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("🔍  Buscar...")
            self.search_input.setProperty("class", "search")
            self.search_input.setMinimumHeight(40)
            self.search_input.setMaximumWidth(350)
            self.search_input.textChanged.connect(self._on_search)
            toolbar.addWidget(self.search_input)

        toolbar.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self.count_label = QLabel("0 registros")
        self.count_label.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        toolbar.addWidget(self.count_label)

        layout.addLayout(toolbar)

        # === Tabela ===
        col_count = len(self.columns) + (1 if self.show_actions else 0)
        self.table = QTableWidget(0, col_count)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Headers
        headers = [col["label"] for col in self.columns]
        if self.show_actions:
            headers.append("Ações")
        self.table.setHorizontalHeaderLabels(headers)

        # Ajustar larguras
        header = self.table.horizontalHeader()
        for i, col in enumerate(self.columns):
            if "width" in col:
                self.table.setColumnWidth(i, col["width"])
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        if self.show_actions:
            self.table.setColumnWidth(col_count - 1, 150)

        self.table.cellClicked.connect(self._on_row_clicked)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)

        layout.addWidget(self.table)

        # === Paginação ===
        pagination = QHBoxLayout()
        pagination.setSpacing(8)

        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.setProperty("class", "secondary")
        self.prev_btn.setMaximumWidth(120)
        self.prev_btn.clicked.connect(self._prev_page)
        pagination.addWidget(self.prev_btn)

        self.page_label = QLabel("Página 1 de 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("color: #8888aa; background: transparent;")
        pagination.addWidget(self.page_label)

        self.next_btn = QPushButton("Próximo ▶")
        self.next_btn.setProperty("class", "secondary")
        self.next_btn.setMaximumWidth(120)
        self.next_btn.clicked.connect(self._next_page)
        pagination.addWidget(self.next_btn)

        layout.addLayout(pagination)

    def set_data(self, data: List[Dict]):
        """Define os dados da tabela."""
        self._data = data
        self._filtered_data = data.copy()
        self._current_page = 0
        self._refresh_table()

    def add_action_button(
        self,
        label: str,
        callback: Callable,
        btn_class: str = "secondary",
        tooltip: str = "",
    ):
        """Adiciona um botão de ação a cada linha."""
        self._action_buttons.append({
            "label": label,
            "callback": callback,
            "class": btn_class,
            "tooltip": tooltip,
        })

    def _on_search(self, text: str):
        """Filtra os dados pela busca."""
        if not text.strip():
            self._filtered_data = self._data.copy()
        else:
            term = text.lower()
            self._filtered_data = [
                row for row in self._data
                if any(
                    term in str(row.get(col["key"], "")).lower()
                    for col in self.columns
                )
            ]
        self._current_page = 0
        self._refresh_table()

    def _refresh_table(self):
        """Atualiza a tabela com os dados filtrados e paginados."""
        total = len(self._filtered_data)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        start = self._current_page * self.page_size
        end = min(start + self.page_size, total)
        page_data = self._filtered_data[start:end]

        self.table.setRowCount(len(page_data))

        for row_idx, row_data in enumerate(page_data):
            # Colunas de dados
            for col_idx, col in enumerate(self.columns):
                value = row_data.get(col["key"], "")

                # Aplicar formatter se existir
                if "formatter" in col and col["formatter"]:
                    display_value = col["formatter"](value)
                else:
                    display_value = str(value) if value is not None else ""

                item = QTableWidgetItem(display_value)

                # Alinhamento
                align = col.get("align", "left")
                if align == "center":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif align == "right":
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )

                self.table.setItem(row_idx, col_idx, item)

            # Coluna de ações
            if self.show_actions and self._action_buttons:
                actions_widget = QWidget()
                actions_widget.setStyleSheet("background: transparent;")
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)

                for action in self._action_buttons:
                    btn = QPushButton(action["label"])
                    btn.setProperty("class", action["class"])
                    btn.setMaximumHeight(28)
                    btn.setFont(QFont("Segoe UI", 12))
                    btn.setStyleSheet("padding: 2px; min-width: 28px; border-radius: 4px;")
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    if action["tooltip"]:
                        btn.setToolTip(action["tooltip"])
                    btn.clicked.connect(
                        lambda checked, data=row_data, cb=action["callback"]: cb(data)
                    )
                    actions_layout.addWidget(btn)

                self.table.setCellWidget(
                    row_idx, len(self.columns), actions_widget
                )

            self.table.setRowHeight(row_idx, 44)

        # Atualizar labels
        self.count_label.setText(f"{total} registro{'s' if total != 1 else ''}")
        self.page_label.setText(
            f"Página {self._current_page + 1} de {total_pages}"
        )
        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < total_pages - 1)

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._refresh_table()

    def _next_page(self):
        total = len(self._filtered_data)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._refresh_table()

    def _on_row_clicked(self, row: int, col: int):
        data = self._get_row_data(row)
        if data:
            self.row_selected.emit(data)

    def _on_row_double_clicked(self, row: int, col: int):
        data = self._get_row_data(row)
        if data:
            self.row_double_clicked.emit(data)

    def _get_row_data(self, row: int) -> Optional[Dict]:
        start = self._current_page * self.page_size
        idx = start + row
        if 0 <= idx < len(self._filtered_data):
            return self._filtered_data[idx]
        return None

    def get_selected_data(self) -> Optional[Dict]:
        """Retorna os dados da linha selecionada."""
        rows = self.table.selectionModel().selectedRows()
        if rows:
            return self._get_row_data(rows[0].row())
        return None

    def refresh(self):
        """Recarrega a tabela mantendo a página atual."""
        self._refresh_table()
