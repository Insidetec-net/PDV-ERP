"""
View de Clientes — CRUD com validação de CPF/CNPJ.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QSpacerItem, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTable
from models.cliente import ClienteModel
from utils.formatters import format_cpf_cnpj, format_phone, format_datetime
from utils.validators import validate_cpf_cnpj


class ClientesView(QWidget):
    """View de gerenciamento de clientes."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.cliente_model = ClienteModel()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕  Novo Cliente")
        add_btn.setMinimumHeight(40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(add_btn)

        toolbar.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        layout.addLayout(toolbar)

        # Tabela
        self.table = DataTable(
            columns=[
                {"key": "nome", "label": "Nome"},
                {"key": "cpf_cnpj", "label": "CPF/CNPJ", "width": 160,
                 "formatter": format_cpf_cnpj},
                {"key": "telefone", "label": "Telefone", "width": 140,
                 "formatter": format_phone},
                {"key": "email", "label": "E-mail", "width": 200},
                {"key": "cidade", "label": "Cidade", "width": 120},
                {"key": "uf", "label": "UF", "width": 50, "align": "center"},
            ],
        )
        self.table.add_action_button("✏️", self._on_edit, "secondary", "Editar")
        self.table.add_action_button("🗑️", self._on_delete, "danger", "Excluir")
        self.table.row_double_clicked.connect(self._on_edit)

        layout.addWidget(self.table)

    def refresh(self):
        try:
            data = self.cliente_model.get_all(
                where="ativo = TRUE", order_by="nome"
            )
            self.table.set_data(data)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar clientes:\n{e}")

    def _on_add(self):
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_edit(self, data: dict = None):
        if not data:
            data = self.table.get_selected_data()
        if not data:
            return
        dialog = ClientDialog(self, client_data=data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_delete(self, data: dict):
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja desativar o cliente '{data['nome']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cliente_model.soft_delete(data["id"])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))


class ClientDialog(QDialog):
    """Diálogo de cadastro/edição de cliente."""

    def __init__(self, parent, client_data: dict = None):
        super().__init__(parent)
        self.client_data = client_data
        self.cliente_model = ClienteModel()
        self.is_edit = client_data is not None
        self._setup_ui()
        if self.is_edit:
            self._load_data()

    def _setup_ui(self):
        title = "Editar Cliente" if self.is_edit else "Novo Cliente"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QLabel(f"{'✏️' if self.is_edit else '➕'}  {title}")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(12)

        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome completo")
        self.nome_input.setMinimumHeight(38)
        form.addRow("Nome *:", self.nome_input)

        self.doc_input = QLineEdit()
        self.doc_input.setPlaceholderText("CPF ou CNPJ")
        self.doc_input.setMinimumHeight(38)
        form.addRow("CPF/CNPJ:", self.doc_input)

        self.telefone_input = QLineEdit()
        self.telefone_input.setPlaceholderText("(XX) XXXXX-XXXX")
        self.telefone_input.setMinimumHeight(38)
        form.addRow("Telefone:", self.telefone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@exemplo.com")
        self.email_input.setMinimumHeight(38)
        form.addRow("E-mail:", self.email_input)

        self.endereco_input = QLineEdit()
        self.endereco_input.setMinimumHeight(38)
        form.addRow("Endereço:", self.endereco_input)

        addr_layout = QHBoxLayout()
        self.cidade_input = QLineEdit()
        self.cidade_input.setPlaceholderText("Cidade")
        self.cidade_input.setMinimumHeight(38)
        addr_layout.addWidget(self.cidade_input)

        self.uf_input = QLineEdit()
        self.uf_input.setPlaceholderText("UF")
        self.uf_input.setMaxLength(2)
        self.uf_input.setMaximumWidth(60)
        self.uf_input.setMinimumHeight(38)
        addr_layout.addWidget(self.uf_input)

        self.cep_input = QLineEdit()
        self.cep_input.setPlaceholderText("CEP")
        self.cep_input.setMaximumWidth(100)
        self.cep_input.setMinimumHeight(38)
        addr_layout.addWidget(self.cep_input)

        form.addRow("Cidade/UF/CEP:", addr_layout)

        self.obs_input = QTextEdit()
        self.obs_input.setPlaceholderText("Observações")
        self.obs_input.setMaximumHeight(60)
        form.addRow("Observação:", self.obs_input)

        layout.addLayout(form)

        # Botões
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("💾  Salvar")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(42)
        save_btn.clicked.connect(self._on_save)
        buttons.addWidget(save_btn)

        layout.addLayout(buttons)

    def _load_data(self):
        d = self.client_data
        self.nome_input.setText(d.get("nome", ""))
        self.doc_input.setText(d.get("cpf_cnpj") or "")
        self.telefone_input.setText(d.get("telefone") or "")
        self.email_input.setText(d.get("email") or "")
        self.endereco_input.setText(d.get("endereco") or "")
        self.cidade_input.setText(d.get("cidade") or "")
        self.uf_input.setText(d.get("uf") or "")
        self.cep_input.setText(d.get("cep") or "")
        self.obs_input.setPlainText(d.get("observacao") or "")

    def _on_save(self):
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome é obrigatório.")
            return

        doc = self.doc_input.text().strip()
        if doc and not validate_cpf_cnpj(doc):
            QMessageBox.warning(self, "Aviso", "CPF/CNPJ inválido.")
            return

        data = {
            "nome": nome,
            "cpf_cnpj": doc or None,
            "telefone": self.telefone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "endereco": self.endereco_input.text().strip() or None,
            "cidade": self.cidade_input.text().strip() or None,
            "uf": self.uf_input.text().strip().upper() or None,
            "cep": self.cep_input.text().strip() or None,
            "observacao": self.obs_input.toPlainText().strip() or None,
        }

        try:
            if self.is_edit:
                self.cliente_model.update(self.client_data["id"], data)
            else:
                self.cliente_model.insert(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{e}")
