"""
NumericKeypad — Teclado numérico virtual para o PDV.

Componente reutilizável para entrada de valores numéricos, usado para:
- Quantidade de itens
- Valor em dinheiro
- Percentual de desconto

Sinal `value_entered` é emitido ao pressionar Enter.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Paleta do tema escuro
_BG_DISPLAY = "#16213e"
_BORDER = "#2a2a4a"
_PRIMARY = "#4361ee"
_PRIMARY_HOVER = "#3a56d4"
_SUCCESS = "#06d6a0"
_SUCCESS_HOVER = "#05b384"
_DANGER = "#ef476f"
_DANGER_HOVER = "#d63d62"
_TEXT = "#e0e0e0"
_TEXT_MUTED = "#8888aa"
_BTN_BG = "#1a1a2e"
_BTN_HOVER = "#25254a"
_BTN_PRESSED = "#2a2a5a"


class NumericKeypad(QWidget):
    """
    Teclado numérico virtual com display e botões 0-9,
    backspace, clear, ponto decimal e enter.

    Signals:
        value_entered: emitido com float ao pressionar Enter.
        value_changed: emitido a cada alteração no display (str).
    """

    value_entered = pyqtSignal(float)
    value_changed = pyqtSignal(str)

    def __init__(
        self,
        title: str = "Valor",
        max_digits: int = 12,
        allow_decimal: bool = True,
        parent=None,
    ):
        """
        Args:
            title: Rótulo exibido acima do display.
            max_digits: Número máximo de caracteres no display.
            allow_decimal: Se True, mostra o botão de ponto decimal.
        """
        super().__init__(parent)
        self._title = title
        self._max_digits = max_digits
        self._allow_decimal = allow_decimal
        self._current_value = ""

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === Título (opcional) ===
        if self._title:
            self.title_label = QLabel(self._title)
            self.title_label.setStyleSheet(
                f"color: {_TEXT_MUTED}; font-size: 12px; "
                f"font-weight: bold; background: transparent;"
            )
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.title_label)

        # === Display ===
        self.display = QLineEdit("0")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setMaxLength(self._max_digits + 2)  # +2 para "0." e sinal
        self.display.setMinimumHeight(56)
        self.display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.display.setFont(QFont("SF Mono", 28, QFont.Weight.Bold))
        self.display.setCursor(Qt.CursorShape.ArrowCursor)
        layout.addWidget(self.display)

        # === Grid de botões ===
        btn_layout = QGridLayout()
        btn_layout.setSpacing(6)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # Estilo padrão dos botões numéricos
        num_btn_size = 64
        num_font = QFont("Segoe UI", 22, QFont.Weight.Medium)

        # Fileira 1: 7, 8, 9
        for i, n in enumerate([7, 8, 9]):
            btn = self._create_button(str(n), num_font, num_btn_size)
            btn.clicked.connect(lambda checked, digit=n: self._on_digit(digit))
            btn_layout.addWidget(btn, 0, i)

        # Backspace (fileira 1, coluna 3)
        back_btn = self._create_function_button("⌫", "Apagar último dígito", 64)
        back_btn.clicked.connect(self._on_backspace)
        btn_layout.addWidget(back_btn, 0, 3)

        # Fileira 2: 4, 5, 6
        for i, n in enumerate([4, 5, 6]):
            btn = self._create_button(str(n), num_font, num_btn_size)
            btn.clicked.connect(lambda checked, digit=n: self._on_digit(digit))
            btn_layout.addWidget(btn, 1, i)

        # Clear (C)
        clear_btn = self._create_function_button("C", "Limpar tudo", 64)
        clear_btn.clicked.connect(self._on_clear)
        btn_layout.addWidget(clear_btn, 1, 3)

        # Fileira 3: 1, 2, 3
        for i, n in enumerate([1, 2, 3]):
            btn = self._create_button(str(n), num_font, num_btn_size)
            btn.clicked.connect(lambda checked, digit=n: self._on_digit(digit))
            btn_layout.addWidget(btn, 2, i)

        # Enter (ocupar 2 linhas)
        enter_btn = self._create_button("⏎", num_font, num_btn_size)
        enter_btn.setProperty("class", "enter")
        enter_btn.setMinimumHeight(num_btn_size * 2 + 6)
        enter_btn.clicked.connect(self._on_enter)
        btn_layout.addWidget(enter_btn, 2, 3, 2, 1)

        # Fileira 4: 0 (ocupa 2 colunas), ponto decimal
        zero_btn = self._create_button("0", num_font, num_btn_size)
        zero_btn.setMinimumWidth(num_btn_size * 2 + 6)
        zero_btn.clicked.connect(lambda checked: self._on_digit(0))
        btn_layout.addWidget(zero_btn, 3, 0, 1, 2)

        if self._allow_decimal:
            dot_btn = self._create_button(".", num_font, num_btn_size)
            dot_btn.clicked.connect(self._on_decimal_dot)
            btn_layout.addWidget(dot_btn, 3, 2)

        layout.addLayout(btn_layout)

    def _create_button(self, text: str, font: QFont, size: int) -> QPushButton:
        """Cria um botão numérico padrão."""
        btn = QPushButton(text)
        btn.setFont(font)
        btn.setMinimumSize(size, size)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("class", "numpad-btn")
        return btn

    def _create_function_button(self, text: str, tooltip: str, size: int) -> QPushButton:
        """Cria um botão de função (backspace, clear)."""
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 18, QFont.Weight.Medium))
        btn.setMinimumSize(size, size)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setProperty("class", "numpad-fn")
        return btn

    def _apply_styles(self):
        """Aplica o estilo escuro do tema do projeto."""
        self.setStyleSheet(f"""
            QPushButton[class="numpad-btn"] {{
                background-color: {_BTN_BG};
                color: {_TEXT};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton[class="numpad-btn"]:hover {{
                background-color: {_BTN_HOVER};
                border-color: {_PRIMARY};
            }}
            QPushButton[class="numpad-btn"]:pressed {{
                background-color: {_BTN_PRESSED};
            }}
            QPushButton[class="numpad-fn"] {{
                background-color: {_DANGER};
                color: #ffffff;
                border: 1px solid {_DANGER};
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton[class="numpad-fn"]:hover {{
                background-color: {_DANGER_HOVER};
                border-color: {_DANGER_HOVER};
            }}
            QPushButton[class="numpad-fn"]:pressed {{
                background-color: {_DANGER_HOVER};
            }}
            QPushButton[class="enter"] {{
                background-color: {_SUCCESS};
                color: #0f0f23;
                border: 1px solid {_SUCCESS};
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton[class="enter"]:hover {{
                background-color: {_SUCCESS_HOVER};
                border-color: {_SUCCESS_HOVER};
            }}
            QPushButton[class="enter"]:pressed {{
                background-color: {_SUCCESS_HOVER};
            }}
        """)

        # Estilo do display (separado pois é QLineEdit)
        self.display.setStyleSheet(f"""
            QLineEdit {{
                background-color: {_BG_DISPLAY};
                color: {_SUCCESS};
                border: 2px solid {_BORDER};
                border-radius: 8px;
                padding: 4px 16px;
                selection-background-color: {_PRIMARY};
            }}
        """)

    # === Slots ===

    def _on_digit(self, digit: int):
        """Processa digito numérico pressionado."""
        # Evita zeros à esquerda (ex: "07")
        if self._current_value == "0" and digit != 0:
            self._current_value = str(digit)
        elif self._current_value == "0":
            # Já está em 0, manter
            return
        else:
            # Verifica limite de dígitos
            if len(self._current_value.replace(".", "")) >= self._max_digits:
                return
            self._current_value += str(digit)

        self._update_display()

    def _on_decimal_dot(self):
        """Adiciona ponto decimal."""
        if "." not in self._current_value:
            if not self._current_value:
                self._current_value = "0."
            else:
                self._current_value += "."
            self._update_display()

    def _on_backspace(self):
        """Apaga o último caractere."""
        if self._current_value:
            self._current_value = self._current_value[:-1]
        if not self._current_value:
            self._current_value = "0"
        self._update_display()

    def _on_clear(self):
        """Limpa todo o valor."""
        self._current_value = "0"
        self._update_display()

    def _on_enter(self):
        """Emite o sinal com o valor final."""
        try:
            value = float(self._current_value)
        except ValueError:
            value = 0.0
        self.value_entered.emit(value)

    def _update_display(self):
        """Atualiza o display e emite value_changed."""
        self.display.setText(self._current_value)
        self.value_changed.emit(self._current_value)

    # === API Pública ===

    def get_value(self) -> float:
        """Retorna o valor atual como float."""
        try:
            return float(self._current_value)
        except ValueError:
            return 0.0

    def set_value(self, value: float):
        """Define o valor do display programaticamente."""
        self._current_value = str(value) if value != int(value) else str(int(value))
        self._update_display()

    def clear(self):
        """Limpa o display."""
        self._on_clear()

    def set_title(self, title: str):
        """Atualiza o título/rótulo do keypad."""
        self._title = title
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)
            self.title_label.setVisible(bool(title))
