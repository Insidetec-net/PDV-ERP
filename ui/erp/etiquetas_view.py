"""
View de Etiquetas — Impressão de etiquetas de gôndola/produto.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit, QSpinBox,
    QHeaderView, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from models.produto import ProdutoModel
from services.barcode_service import BarcodeService
import os

class EtiquetasView(QWidget):
    """View para selecionar produtos e imprimir etiquetas térmicas."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.produto_model = ProdutoModel()
        self.fila_produtos = {} # codigo -> dict(produto) + qtd
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("🏷️ Impressão de Etiquetas (40x30mm Térmica)")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(title)

        # Busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto por nome ou código (Aperte Enter)...")
        self.search_input.setMinimumHeight(40)
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        add_btn = QPushButton("Buscar")
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self._on_search)
        search_layout.addWidget(add_btn)
        layout.addLayout(search_layout)

        # Tabela Resultados
        layout.addWidget(QLabel("Resultados da Busca:"))
        self.table_res = QTableWidget()
        self.table_res.setColumnCount(4)
        self.table_res.setHorizontalHeaderLabels(["Código", "Nome", "Preço", "Ação"])
        self.table_res.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_res.verticalHeader().setDefaultSectionSize(44)
        from PyQt6.QtWidgets import QAbstractItemView
        self.table_res.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_res.setMinimumHeight(150)
        self.table_res.setMaximumHeight(200)
        layout.addWidget(self.table_res)

        # Fila de impressão
        layout.addWidget(QLabel("Fila de Impressão:"))
        self.table_fila = QTableWidget()
        self.table_fila.setColumnCount(5)
        self.table_fila.setHorizontalHeaderLabels(["Código", "Nome", "Preço", "Qtd Etiquetas", "Remover"])
        self.table_fila.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_fila.verticalHeader().setDefaultSectionSize(44)
        self.table_fila.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_fila)

        # Ações
        action_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Limpar Fila")
        clear_btn.setMinimumHeight(44)
        clear_btn.clicked.connect(self._limpar_fila)
        action_layout.addWidget(clear_btn)
        
        print_btn = QPushButton("🖨️  Gerar PDF para Impressão")
        print_btn.setProperty("class", "success")
        print_btn.setMinimumHeight(44)
        print_btn.clicked.connect(self._on_print)
        action_layout.addWidget(print_btn)
        
        layout.addLayout(action_layout)
        self._search("")

    def _on_search(self):
        term = self.search_input.text().strip()
        self._search(term)

    def _search(self, query: str):
        produtos = self.produto_model.search_products(query, limit=10)
        self.table_res.setRowCount(len(produtos))
        for i, prod in enumerate(produtos):
            self.table_res.setItem(i, 0, QTableWidgetItem(str(prod.get("codigo_barras", ""))))
            self.table_res.setItem(i, 1, QTableWidgetItem(str(prod.get("nome", ""))))
            self.table_res.setItem(i, 2, QTableWidgetItem(f"R$ {prod.get('preco_venda', 0.0):.2f}"))
            
            btn_add = QPushButton("Adicionar")
            btn_add.clicked.connect(lambda _, p=prod: self._add_to_queue(p))
            self.table_res.setCellWidget(i, 3, btn_add)

    def _add_to_queue(self, prod: dict):
        codigo = prod.get("codigo_barras")
        if not codigo:
            QMessageBox.warning(self, "Aviso", "Produto sem código de barras não pode ser etiquetado.")
            return

        if codigo in self.fila_produtos:
            self.fila_produtos[codigo]["quantidade"] += 1
        else:
            self.fila_produtos[codigo] = {
                "codigo": codigo,
                "nome": prod.get("nome"),
                "preco": prod.get("preco_venda", 0.0),
                "quantidade": 1
            }
        self._update_fila_ui()

    def _update_fila_ui(self):
        self.table_fila.setRowCount(len(self.fila_produtos))
        for i, (cod, dados) in enumerate(self.fila_produtos.items()):
            self.table_fila.setItem(i, 0, QTableWidgetItem(cod))
            self.table_fila.setItem(i, 1, QTableWidgetItem(dados["nome"]))
            self.table_fila.setItem(i, 2, QTableWidgetItem(f"R$ {dados['preco']:.2f}"))
            
            spin = QSpinBox()
            spin.setMinimum(1)
            spin.setMaximum(1000)
            spin.setValue(dados["quantidade"])
            spin.valueChanged.connect(lambda val, c=cod: self._update_qtd(c, val))
            self.table_fila.setCellWidget(i, 3, spin)
            
            btn_rem = QPushButton("❌")
            btn_rem.clicked.connect(lambda _, c=cod: self._remove_from_queue(c))
            self.table_fila.setCellWidget(i, 4, btn_rem)

    def _update_qtd(self, codigo, val):
        if codigo in self.fila_produtos:
            self.fila_produtos[codigo]["quantidade"] = val

    def _remove_from_queue(self, codigo):
        if codigo in self.fila_produtos:
            del self.fila_produtos[codigo]
            self._update_fila_ui()

    def _limpar_fila(self):
        self.fila_produtos.clear()
        self._update_fila_ui()

    def _on_print(self):
        if not self.fila_produtos:
            QMessageBox.warning(self, "Fila Vazia", "Adicione produtos na fila antes de gerar o PDF.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF de Etiquetas",
            os.path.join(os.path.expanduser("~"), "Desktop", "etiquetas_bazar.pdf"),
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return

        try:
            lista = list(self.fila_produtos.values())
            BarcodeService.gerar_pdf_etiquetas_termicas(lista, file_path)
            QMessageBox.information(self, "Sucesso", f"PDF gerado com sucesso em:\n{file_path}\n\nAbra o PDF e mande para a impressora térmica selecionando tamanho de papel 40x30mm.")
            
            # Limpa fila apos imprimir
            self._limpar_fila()
            
            # Abre o PDF para o usuario ver (opcional macOS)
            os.system(f'open "{file_path}"')
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao gerar as etiquetas:\n{e}")

