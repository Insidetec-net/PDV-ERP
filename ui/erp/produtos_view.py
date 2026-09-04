"""
View de Produtos — CRUD completo com busca, filtros e cálculo de markup.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QDialog, QFormLayout, QDoubleSpinBox,
    QSpinBox, QTextEdit, QMessageBox, QFrame, QSpacerItem,
    QSizePolicy, QCheckBox, QFileDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTable
from models.produto import ProdutoModel
from models.configuracao import ConfiguracaoModel
from utils.formatters import format_currency
from config.constants import (
    CST_ICMS, CST_PIS, CST_COFINS, CFOP_VENDA, UNIDADES,
)


class ProdutosView(QWidget):
    """View de gerenciamento de produtos."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.produto_model = ProdutoModel()
        self.config_model = ConfiguracaoModel()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Toolbar ===
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕  Novo Produto")
        add_btn.setMinimumHeight(40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(add_btn)

        import_btn = QPushButton("📥  Importar CSV")
        import_btn.setProperty("class", "secondary")
        import_btn.setMinimumHeight(40)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self._on_import_csv)
        toolbar.addWidget(import_btn)

        toolbar.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # Filtro por categoria
        toolbar.addWidget(QLabel("Categoria:"))
        self.cat_filter = QComboBox()
        self.cat_filter.setMinimumWidth(180)
        self.cat_filter.addItem("Todas", None)
        self._load_categories()
        self.cat_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.cat_filter)

        layout.addLayout(toolbar)

        # === Tabela ===
        self.table = DataTable(
            columns=[
                {"key": "codigo_interno", "label": "Código", "width": 100},
                {"key": "nome", "label": "Produto"},
                {"key": "categoria_nome", "label": "Categoria", "width": 140},
                {"key": "preco_custo", "label": "Custo", "width": 100,
                 "formatter": format_currency, "align": "right"},
                {"key": "preco_venda", "label": "Venda", "width": 100,
                 "formatter": format_currency, "align": "right"},
                {"key": "margem_lucro", "label": "Margem", "width": 80,
                 "formatter": lambda v: f"{v:.1f}%" if v else "0%", "align": "center"},
                {"key": "estoque_atual", "label": "Estoque", "width": 80,
                 "align": "center"},
            ],
            page_size=25,
        )
        self.table.add_action_button("✏️", self._on_edit, "secondary", "Editar")
        self.table.add_action_button("🗑️", self._on_delete, "danger", "Excluir")
        self.table.row_double_clicked.connect(self._on_edit)

        layout.addWidget(self.table)

    def refresh(self):
        """Recarrega os dados da tabela."""
        try:
            cat_id = self.cat_filter.currentData()
            data = self.produto_model.get_products_with_category(
                active_only=True,
                category_id=cat_id,
            )
            self.table.set_data(data)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos:\n{e}")

    def _load_categories(self):
        """Carrega categorias no combobox de filtro."""
        try:
            from database.connection import execute_query
            cats = execute_query(
                "SELECT id, nome FROM categorias WHERE ativa = TRUE ORDER BY nome"
            ) or []
            for cat in cats:
                self.cat_filter.addItem(cat["nome"], cat["id"])
        except Exception:
            pass

    def _on_filter_changed(self):
        self.refresh()

    def _on_add(self):
        """Abre diálogo para cadastrar novo produto."""
        dialog = ProductDialog(self, user=self.user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_edit(self, data: dict = None):
        """Abre diálogo para editar produto."""
        if not data:
            data = self.table.get_selected_data()
        if not data:
            QMessageBox.information(self, "Aviso", "Selecione um produto para editar.")
            return
        dialog = ProductDialog(self, product_data=data, user=self.user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_delete(self, data: dict):
        """Desativa um produto (soft delete)."""
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja desativar o produto '{data['nome']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.produto_model.soft_delete(data["id"])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir:\n{e}")

    def _on_import_csv(self):
        """Importa produtos de um arquivo CSV."""
        QMessageBox.information(
            self, "Em Breve",
            "Importação por CSV será implementada em breve."
        )


class ProductDialog(QDialog):
    """Diálogo de cadastro/edição de produto."""

    def __init__(self, parent, product_data: dict = None, user: dict = None):
        super().__init__(parent)
        self.product_data = product_data
        self.user = user
        self.produto_model = ProdutoModel()
        self.config_model = ConfiguracaoModel()
        self.is_edit = product_data is not None
        self._setup_ui()
        if self.is_edit:
            self._load_data()

    def _setup_ui(self):
        title = "Editar Produto" if self.is_edit else "Novo Produto"
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QLabel(f"{'✏️' if self.is_edit else '➕'}  {title}")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(header)

        # === Formulário ===
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Código de barras
        self.codigo_barras_input = QLineEdit()
        self.codigo_barras_input.setPlaceholderText("EAN-13 (scanner ou manual)")
        self.codigo_barras_input.setMinimumHeight(38)
        form.addRow("Código de Barras:", self.codigo_barras_input)

        # Nome
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome do produto")
        self.nome_input.setMinimumHeight(38)
        form.addRow("Nome *:", self.nome_input)

        # Categoria
        self.categoria_combo = QComboBox()
        self.categoria_combo.addItem("Sem categoria", None)
        self._load_categories()
        form.addRow("Categoria:", self.categoria_combo)

        # Unidade
        self.unidade_combo = QComboBox()
        for code, name in UNIDADES.items():
            self.unidade_combo.addItem(f"{code} — {name}", code)
        form.addRow("Unidade:", self.unidade_combo)

        # Preços
        preco_layout = QHBoxLayout()

        self.custo_input = QDoubleSpinBox()
        self.custo_input.setPrefix("R$ ")
        self.custo_input.setDecimals(2)
        self.custo_input.setMaximum(999999.99)
        self.custo_input.setMinimumHeight(38)
        self.custo_input.valueChanged.connect(self._calculate_price)
        preco_layout.addWidget(QLabel("Custo:"))
        preco_layout.addWidget(self.custo_input)

        self.markup_input = QDoubleSpinBox()
        self.markup_input.setSuffix(" %")
        self.markup_input.setDecimals(1)
        self.markup_input.setMaximum(9999.9)
        self.markup_input.setValue(
            float(self.config_model.get_value("sistema_markup_padrao") or "100")
        )
        self.markup_input.setMinimumHeight(38)
        self.markup_input.valueChanged.connect(self._calculate_price)
        preco_layout.addWidget(QLabel("Markup:"))
        preco_layout.addWidget(self.markup_input)

        self.venda_input = QDoubleSpinBox()
        self.venda_input.setPrefix("R$ ")
        self.venda_input.setDecimals(2)
        self.venda_input.setMaximum(999999.99)
        self.venda_input.setMinimumHeight(38)
        self.venda_input.setStyleSheet("color: #06d6a0; font-weight: bold;")
        preco_layout.addWidget(QLabel("Venda:"))
        preco_layout.addWidget(self.venda_input)

        form.addRow("Preços:", preco_layout)

        # Margem calculada
        self.margem_label = QLabel("Margem: 0,00%  |  Lucro: R$ 0,00")
        self.margem_label.setStyleSheet("color: #ffd166; font-size: 12px; background: transparent;")
        form.addRow("", self.margem_label)

        # Estoque
        estoque_layout = QHBoxLayout()

        self.estoque_input = QDoubleSpinBox()
        self.estoque_input.setDecimals(3)
        self.estoque_input.setMaximum(999999.999)
        self.estoque_input.setMinimumHeight(38)
        estoque_layout.addWidget(QLabel("Atual:"))
        estoque_layout.addWidget(self.estoque_input)

        self.estoque_min_input = QDoubleSpinBox()
        self.estoque_min_input.setDecimals(3)
        self.estoque_min_input.setMaximum(999999.999)
        self.estoque_min_input.setValue(
            float(self.config_model.get_value("sistema_estoque_minimo") or "5")
        )
        self.estoque_min_input.setMinimumHeight(38)
        estoque_layout.addWidget(QLabel("Mínimo:"))
        estoque_layout.addWidget(self.estoque_min_input)

        form.addRow("Estoque:", estoque_layout)

        # === Dados Fiscais ===
        fiscal_label = QLabel("📋 Dados Fiscais (Lucro Presumido)")
        fiscal_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        fiscal_label.setStyleSheet("color: #4361ee; background: transparent; padding-top: 8px;")
        form.addRow(fiscal_label)

        # NCM
        self.ncm_input = QLineEdit()
        self.ncm_input.setPlaceholderText("Ex: 62019900")
        self.ncm_input.setMinimumHeight(38)
        form.addRow("NCM:", self.ncm_input)

        # CFOP
        self.cfop_combo = QComboBox()
        for code, desc in CFOP_VENDA.items():
            self.cfop_combo.addItem(f"{code} — {desc}", code)
        form.addRow("CFOP:", self.cfop_combo)

        # CST ICMS
        self.cst_icms_combo = QComboBox()
        default_cst = self.config_model.get_value("fiscal_cst_icms_padrao") or "00"
        for code, desc in CST_ICMS.items():
            self.cst_icms_combo.addItem(f"{code} — {desc}", code)
        idx = self.cst_icms_combo.findData(default_cst)
        if idx >= 0:
            self.cst_icms_combo.setCurrentIndex(idx)
        form.addRow("CST ICMS:", self.cst_icms_combo)

        # Alíquota ICMS
        self.aliquota_icms_input = QDoubleSpinBox()
        self.aliquota_icms_input.setSuffix(" %")
        self.aliquota_icms_input.setDecimals(2)
        self.aliquota_icms_input.setMaximum(99.99)
        self.aliquota_icms_input.setValue(
            float(self.config_model.get_value("fiscal_aliquota_icms") or "18")
        )
        self.aliquota_icms_input.setMinimumHeight(38)
        form.addRow("Alíq. ICMS:", self.aliquota_icms_input)

        # Descrição
        self.descricao_input = QTextEdit()
        self.descricao_input.setPlaceholderText("Descrição (opcional)")
        self.descricao_input.setMaximumHeight(80)
        form.addRow("Descrição:", self.descricao_input)

        layout.addLayout(form)

        # === Botões ===
        buttons = QHBoxLayout()
        buttons.setSpacing(12)

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

    def _load_categories(self):
        try:
            from database.connection import execute_query
            cats = execute_query(
                "SELECT id, nome FROM categorias WHERE ativa = TRUE ORDER BY nome"
            ) or []
            for cat in cats:
                self.categoria_combo.addItem(cat["nome"], cat["id"])
        except Exception:
            pass

    def _load_data(self):
        """Preenche o formulário com dados do produto existente."""
        d = self.product_data
        self.codigo_barras_input.setText(d.get("codigo_barras") or "")
        self.nome_input.setText(d.get("nome", ""))
        self.custo_input.setValue(float(d.get("preco_custo", 0)))
        self.venda_input.setValue(float(d.get("preco_venda", 0)))
        self.estoque_input.setValue(float(d.get("estoque_atual", 0)))
        self.estoque_min_input.setValue(float(d.get("estoque_minimo", 0)))
        self.ncm_input.setText(d.get("ncm") or "")
        self.descricao_input.setPlainText(d.get("descricao") or "")
        self.aliquota_icms_input.setValue(float(d.get("aliquota_icms", 18)))

        # Selecionar categoria
        cat_id = d.get("categoria_id")
        if cat_id:
            idx = self.categoria_combo.findData(cat_id)
            if idx >= 0:
                self.categoria_combo.setCurrentIndex(idx)

        # Selecionar unidade
        unidade = d.get("unidade", "UN")
        idx = self.unidade_combo.findData(unidade)
        if idx >= 0:
            self.unidade_combo.setCurrentIndex(idx)

        # Selecionar CFOP
        cfop = d.get("cfop", "5102")
        idx = self.cfop_combo.findData(cfop)
        if idx >= 0:
            self.cfop_combo.setCurrentIndex(idx)

        # Selecionar CST ICMS
        cst = d.get("cst_icms", "00")
        idx = self.cst_icms_combo.findData(cst)
        if idx >= 0:
            self.cst_icms_combo.setCurrentIndex(idx)

        # Calcular margem
        custo = float(d.get("preco_custo", 0))
        venda = float(d.get("preco_venda", 0))
        if custo > 0 and venda > 0:
            markup = ((venda - custo) / custo) * 100
            self.markup_input.setValue(markup)
        self._calculate_price()

    def _calculate_price(self):
        """Calcula preço de venda e margem a partir do custo + markup."""
        custo = self.custo_input.value()
        markup = self.markup_input.value()

        if custo > 0:
            result = self.produto_model.calculate_sale_price(custo, markup)
            self.venda_input.setValue(result["preco_venda"])
            self.margem_label.setText(
                f"Margem: {result['margem_lucro']:.2f}%  |  "
                f"Lucro: {format_currency(result['lucro_bruto'])}"
            )

    def _on_save(self):
        """Salva o produto."""
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome do produto é obrigatório.")
            return

        data = {
            "codigo_barras": self.codigo_barras_input.text().strip() or None,
            "nome": nome,
            "descricao": self.descricao_input.toPlainText().strip() or None,
            "categoria_id": self.categoria_combo.currentData(),
            "preco_custo": self.custo_input.value(),
            "preco_venda": self.venda_input.value(),
            "margem_lucro": float(self.markup_input.value()),
            "ncm": self.ncm_input.text().strip() or None,
            "cst_icms": self.cst_icms_combo.currentData(),
            "cst_pis": self.config_model.get_value("fiscal_cst_pis_padrao") or "01",
            "cst_cofins": self.config_model.get_value("fiscal_cst_cofins_padrao") or "01",
            "aliquota_icms": self.aliquota_icms_input.value(),
            "cfop": self.cfop_combo.currentData(),
            "unidade": self.unidade_combo.currentData(),
            "estoque_atual": self.estoque_input.value(),
            "estoque_minimo": self.estoque_min_input.value(),
        }

        try:
            if self.is_edit:
                self.produto_model.update(self.product_data["id"], data)
            else:
                # Gerar código interno automático
                data["codigo_interno"] = self.produto_model.generate_next_internal_code()
                self.produto_model.insert(data)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar produto:\n{e}")
