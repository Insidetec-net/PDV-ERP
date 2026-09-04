"""
PDVWindow — Frente de Caixa Simples e Funcional
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSpacerItem, QSizePolicy, QMessageBox, QDialog, QDoubleSpinBox,
    QInputDialog, QFormLayout, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent

from services.caixa_service import CaixaService
from services.venda_service import VendaService
from models.produto import ProdutoModel
from models.caixa import CaixaModel
from decimal import Decimal


def dec(val):
    """Converte para Decimal."""
    if isinstance(val, Decimal):
        return val
    if val is None:
        return Decimal('0')
    return Decimal(str(val))


def money(val):
    """Formata como moeda."""
    return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class BuscaProdutoDialog(QDialog):
    def __init__(self, parent, produto_model):
        super().__init__(parent)
        self.produto_model = produto_model
        self.produto_selecionado = None
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle("🔍 Buscar Produto (F5)")
        self.setFixedSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome do produto...")
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Código", "Produto", "Preço"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self._on_select)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Selecionar")
        btn_ok.clicked.connect(self._on_select)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
        
    def _on_text_changed(self, text):
        if len(text) < 2:
            self.table.setRowCount(0)
            return
            
        produtos = self.produto_model.search_products(text, limit=20)
        self.table.setRowCount(len(produtos))
        for row, p in enumerate(produtos):
            self.table.setItem(row, 0, QTableWidgetItem(p.get("codigo_interno", "")))
            self.table.setItem(row, 1, QTableWidgetItem(p.get("nome", "")))
            self.table.setItem(row, 2, QTableWidgetItem(money(p.get("preco_venda", 0))))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, p)
            
    def _on_select(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                self.produto_selecionado = item.data(Qt.ItemDataRole.UserRole)
                self.accept()


class FechamentoCaixaDialog(QDialog):
    """Diálogo simples para fechamento de caixa."""

    def __init__(self, parent, caixa_service, turno_id):
        super().__init__(parent)
        self.caixa_service = caixa_service
        self.turno_id = turno_id
        self.resultado = None
        self._setup_ui()
        self._load_dados()

    def _setup_ui(self):
        self.setWindowTitle("Fechamento de Caixa")
        self.setFixedSize(450, 550)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Título
        titulo = QLabel("🔒 Fechamento de Caixa")
        titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Resumo
        resumo_frame = QFrame()
        resumo_layout = QFormLayout(resumo_frame)
        resumo_layout.setSpacing(10)

        self.lbl_abertura = QLabel("R$ 0,00")
        resumo_layout.addRow("💰 Abertura:", self.lbl_abertura)

        self.lbl_vendas_dinheiro = QLabel("R$ 0,00")
        resumo_layout.addRow("💵 Vendas (dinheiro):", self.lbl_vendas_dinheiro)

        self.lbl_suprimentos = QLabel("R$ 0,00")
        resumo_layout.addRow("📥 Suprimentos:", self.lbl_suprimentos)

        self.lbl_sangrias = QLabel("R$ 0,00")
        resumo_layout.addRow("📤 Sangrias:", self.lbl_sangrias)

        self.lbl_qtd_vendas = QLabel("0")
        resumo_layout.addRow("📊 Qtd Vendas:", self.lbl_qtd_vendas)

        # Linha separadora
        linha = QFrame()
        linha.setFrameShape(QFrame.Shape.HLine)
        resumo_layout.addRow(linha)

        self.lbl_sistema = QLabel("R$ 0,00")
        self.lbl_sistema.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        resumo_layout.addRow("💻 Total no Sistema:", self.lbl_sistema)

        layout.addWidget(resumo_frame)

        # Campo valor contado
        contar_label = QLabel("💵 Valor contado na gaveta:")
        contar_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(contar_label)

        self.valor_input = QDoubleSpinBox()
        self.valor_input.setPrefix("R$ ")
        self.valor_input.setDecimals(2)
        self.valor_input.setMaximum(999999.99)
        self.valor_input.setMinimumHeight(45)
        self.valor_input.valueChanged.connect(self._calcular_diferenca)
        layout.addWidget(self.valor_input)

        self.lbl_diferenca = QLabel("Diferença: R$ 0,00")
        self.lbl_diferenca.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_diferenca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_diferenca)

        # Observação
        obs_label = QLabel("📝 Observações:")
        layout.addWidget(obs_label)

        self.obs_input = QTextEdit()
        self.obs_input.setMaximumHeight(60)
        self.obs_input.setPlaceholderText("Anotações sobre o fechamento...")
        layout.addWidget(self.obs_input)

        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)

        btn_fechar = QPushButton("Confirmar Fechamento")
        btn_fechar.setMinimumHeight(40)
        btn_fechar.clicked.connect(self._confirmar)
        btn_layout.addWidget(btn_fechar)

        layout.addLayout(btn_layout)

    def _load_dados(self):
        """Carrega dados do turno."""
        turno = self.caixa_service.model.get_by_id(self.turno_id)
        if not turno:
            return

        abertura = dec(turno.get('valor_abertura'))
        vendas_dinheiro = dec(self.caixa_service.model.get_total_vendas_dinheiro(self.turno_id))
        suprimentos = dec(turno.get('total_suprimentos'))
        sangrias = dec(turno.get('total_sangrias'))
        qtd_vendas = turno.get('qtd_vendas', 0)

        # Saldo esperado no sistema (dinheiro)
        saldo_sistema = abertura + vendas_dinheiro + suprimentos - sangrias

        self.lbl_abertura.setText(money(abertura))
        self.lbl_vendas_dinheiro.setText(money(vendas_dinheiro))
        self.lbl_suprimentos.setText(money(suprimentos))
        self.lbl_sangrias.setText(money(sangrias))
        self.lbl_qtd_vendas.setText(str(qtd_vendas))
        self.lbl_sistema.setText(money(saldo_sistema))

        self.saldo_sistema = saldo_sistema
        self.valor_input.setValue(float(saldo_sistema))

    def _calcular_diferenca(self):
        """Calcula diferença."""
        contado = Decimal(str(self.valor_input.value()))
        diferenca = contado - self.saldo_sistema
        
        if diferenca > 0:
            self.lbl_diferenca.setText(f"SOBRA: +{money(diferenca)}")
        elif diferenca < 0:
            self.lbl_diferenca.setText(f"QUEBRA: {money(diferenca)}")
        else:
            self.lbl_diferenca.setText("Sem diferença ✅")

    def _confirmar(self):
        """Confirma fechamento."""
        contado = Decimal(str(self.valor_input.value()))
        diferenca = contado - self.saldo_sistema

        msg = f"Confirmar fechamento?\n\n"
        msg += f"Valor contado: {money(contado)}\n"
        msg += f"Valor sistema: {money(self.saldo_sistema)}\n"
        if diferenca != 0:
            msg += f"Diferença: {money(diferenca)}\n"

        reply = QMessageBox.question(self, "Confirmar", msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.resultado = {
                'valor_fechamento': contado,
                'diferenca': diferenca,
                'observacao': self.obs_input.toPlainText()
            }
            self.accept()


class PDVWindow(QMainWindow):
    """Janela do Ponto de Venda."""

    def __init__(self, user_data: dict, on_logout=None):
        super().__init__()
        self.user = user_data
        self.on_logout = on_logout
        self.caixa_service = CaixaService()
        self.venda_service = VendaService()
        self.produto_model = ProdutoModel()
        self.turno_id = None
        self.carrinho = []
        self.total = Decimal('0')
        
        self._setup_ui()
        self._check_caixa()

    def _setup_ui(self):
        from config.settings import APP_NAME
        self.setWindowTitle(f"{APP_NAME} — PDV")
        self.setMinimumSize(1024, 700)
        self.showMaximized()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === ESQUERDA ===
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)

        # Cabeçalho
        header = QFrame()
        header.setMinimumHeight(60)
        h_layout = QHBoxLayout(header)
        
        self.status_lbl = QLabel("🔴 CAIXA FECHADO")
        self.status_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        h_layout.addWidget(self.status_lbl)

        h_layout.addStretch()

        user_lbl = QLabel(f"👤 {self.user.get('nome', 'Operador')}")
        h_layout.addWidget(user_lbl)
        
        left_layout.addWidget(header)

        # Tabela do Carrinho
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["#", "Código", "Produto", "Qtd", "V.Unit", "Subtotal"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(300)
        
        header_table = self.table.horizontalHeader()
        header_table.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table)

        # Input
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        
        qty_lbl = QLabel("Qtd:")
        input_layout.addWidget(qty_lbl)

        self.qty_input = QLineEdit("1")
        self.qty_input.setFixedWidth(60)
        input_layout.addWidget(self.qty_input)

        code_lbl = QLabel("Código:")
        input_layout.addWidget(code_lbl)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Bipe ou digite o código (Enter)")
        self.code_input.returnPressed.connect(self._on_enter_code)
        input_layout.addWidget(self.code_input)

        left_layout.addWidget(input_frame)
        main_layout.addLayout(left_layout, stretch=7)

        # === DIREITA ===
        right_layout = QVBoxLayout()
        right_layout.setSpacing(16)

        # Info do Produto
        prod_frame = QFrame()
        prod_frame.setMinimumHeight(100)
        prod_layout = QVBoxLayout(prod_frame)
        
        self.prod_name_lbl = QLabel("CAIXA LIVRE")
        self.prod_name_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.prod_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prod_layout.addWidget(self.prod_name_lbl)
        
        self.prod_val_lbl = QLabel("")
        self.prod_val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prod_layout.addWidget(self.prod_val_lbl)
        
        right_layout.addWidget(prod_frame)

        # Total
        total_frame = QFrame()
        total_frame.setMinimumHeight(80)
        t_layout = QVBoxLayout(total_frame)
        
        t_lbl = QLabel("TOTAL:")
        t_layout.addWidget(t_lbl)
        
        self.total_lbl = QLabel("R$ 0,00")
        self.total_lbl.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        self.total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        t_layout.addWidget(self.total_lbl)
        
        right_layout.addWidget(total_frame)

        # Info do Caixa
        caixa_frame = QFrame()
        caixa_layout = QVBoxLayout(caixa_frame)
        caixa_layout.setSpacing(8)
        
        caixa_title = QLabel("💰 CAIXA")
        caixa_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        caixa_layout.addWidget(caixa_title)
        
        self.turno_lbl = QLabel("Turno: ---")
        caixa_layout.addWidget(self.turno_lbl)
        
        self.abertura_lbl = QLabel("Abertura: R$ 0,00")
        caixa_layout.addWidget(self.abertura_lbl)
        
        self.saldo_lbl = QLabel("Saldo: R$ 0,00")
        self.saldo_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        caixa_layout.addWidget(self.saldo_lbl)
        
        self.vendas_lbl = QLabel("Vendas: 0")
        caixa_layout.addWidget(self.vendas_lbl)
        
        self.sangrias_lbl = QLabel("Sangrias: R$ 0,00")
        caixa_layout.addWidget(self.sangrias_lbl)
        
        self.suprimentos_lbl = QLabel("Suprimentos: R$ 0,00")
        caixa_layout.addWidget(self.suprimentos_lbl)
        
        right_layout.addWidget(caixa_frame)

        # Botões de Ação
        btn_abrir = QPushButton("🔓 Abrir Caixa")
        btn_abrir.setMinimumHeight(45)
        btn_abrir.clicked.connect(self._open_caixa)
        right_layout.addWidget(btn_abrir)
        
        btn_sangria = QPushButton("📤 Sangria")
        btn_sangria.setMinimumHeight(45)
        btn_sangria.clicked.connect(self._on_sangria)
        right_layout.addWidget(btn_sangria)
        
        btn_suprimento = QPushButton("📥 Suprimento")
        btn_suprimento.setMinimumHeight(45)
        btn_suprimento.clicked.connect(self._on_suprimento)
        right_layout.addWidget(btn_suprimento)
        
        btn_fechar = QPushButton("🔒 Fechar Caixa")
        btn_fechar.setMinimumHeight(45)
        btn_fechar.clicked.connect(self._close_caixa)
        right_layout.addWidget(btn_fechar)

        right_layout.addStretch()

        # Atalhos
        shortcuts_lbl = QLabel("F4=Vender | F5=Buscar | F6=Cancel Item | F7=Cancel Venda | F10=Fechar")
        shortcuts_lbl.setStyleSheet("color: #8888aa; font-size: 11px;")
        right_layout.addWidget(shortcuts_lbl)

        # Voltar
        btn_voltar = QPushButton("⬅ Voltar")
        btn_voltar.setMinimumHeight(40)
        btn_voltar.clicked.connect(self._voltar)
        right_layout.addWidget(btn_voltar)

        main_layout.addLayout(right_layout, stretch=3)

    def _check_caixa(self):
        """Verifica se existe caixa aberto."""
        turno = self.caixa_service.model.get_open_shift(self.user["id"])
        if turno:
            self.turno_id = turno["id"]
            self._update_caixa_display(turno)
            self.status_lbl.setText("🟢 CAIXA ABERTO")
            self.code_input.setFocus()
        else:
            self.turno_id = None
            self._clear_caixa_display()
            self.status_lbl.setText("🔴 CAIXA FECHADO")

    def _update_caixa_display(self, turno):
        """Atualiza display do caixa."""
        self.turno_lbl.setText(f"Turno #{turno['id']}")
        self.abertura_lbl.setText(f"Abertura: {money(dec(turno.get('valor_abertura', 0)))}")
        
        saldo = dec(self.caixa_service.get_saldo_turno(self.turno_id))
        self.saldo_lbl.setText(f"Saldo: {money(saldo)}")
        
        self.vendas_lbl.setText(f"Vendas: {turno.get('qtd_vendas', 0)}")
        self.sangrias_lbl.setText(f"Sangrias: {money(dec(turno.get('total_sangrias', 0)))}")
        self.suprimentos_lbl.setText(f"Suprimentos: {money(dec(turno.get('total_suprimentos', 0)))}")

    def _clear_caixa_display(self):
        """Limpa display do caixa."""
        self.turno_lbl.setText("Turno: ---")
        self.abertura_lbl.setText("Abertura: R$ 0,00")
        self.saldo_lbl.setText("Saldo: R$ 0,00")
        self.vendas_lbl.setText("Vendas: 0")
        self.sangrias_lbl.setText("Sangrias: R$ 0,00")
        self.suprimentos_lbl.setText("Suprimentos: R$ 0,00")

    def _open_caixa(self):
        """Abre o caixa."""
        valor, ok = QInputDialog.getDouble(self, "Abertura de Caixa", 
                                           "Valor do fundo de troco:", 
                                           0.00, 0, 99999.99, 2)
        if ok:
            try:
                self.turno_id = self.caixa_service.abrir_caixa(self.user["id"], Decimal(str(valor)))
                turno = self.caixa_service.model.get_by_id(self.turno_id)
                self._update_caixa_display(turno)
                self.status_lbl.setText("🟢 CAIXA ABERTO")
                QMessageBox.information(self, "Sucesso", f"Caixa #{self.turno_id} aberto!")
                self.code_input.setFocus()
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def _close_caixa(self):
        """Fecha o caixa."""
        if not self.turno_id:
            QMessageBox.warning(self, "Atenção", "Não há caixa aberto.")
            return
            
        if self.carrinho:
            QMessageBox.warning(self, "Atenção", "Finalize ou cancele a venda atual.")
            return

        dialog = FechamentoCaixaDialog(self, self.caixa_service, self.turno_id)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.resultado:
            try:
                self.caixa_service.fechar_caixa(
                    self.turno_id,
                    dialog.resultado['valor_fechamento'],
                    dialog.resultado['observacao']
                )
                QMessageBox.information(self, "Sucesso", "Caixa fechado!")
                self.turno_id = None
                self._clear_caixa_display()
                self.status_lbl.setText("🔴 CAIXA FECHADO")
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def _on_sangria(self):
        """Registra sangria."""
        if not self.turno_id:
            QMessageBox.warning(self, "Atenção", "Abra o caixa primeiro.")
            return

        valor, ok = QInputDialog.getDouble(self, "Sangria", 
                                           "Valor da sangria:", 
                                           0.00, 0.01, 99999.99, 2)
        if ok and valor > 0:
            motivo, ok2 = QInputDialog.getText(self, "Sangria", "Motivo:")
            if ok2:
                try:
                    self.caixa_service.sangria(self.turno_id, self.user["id"], Decimal(str(valor)), motivo)
                    turno = self.caixa_service.model.get_by_id(self.turno_id)
                    self._update_caixa_display(turno)
                    QMessageBox.information(self, "Sucesso", "Sangria registrada!")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", str(e))
        self.code_input.setFocus()

    def _on_suprimento(self):
        """Registra suprimento."""
        if not self.turno_id:
            QMessageBox.warning(self, "Atenção", "Abra o caixa primeiro.")
            return

        valor, ok = QInputDialog.getDouble(self, "Suprimento", 
                                           "Valor do suprimento:", 
                                           0.00, 0.01, 99999.99, 2)
        if ok and valor > 0:
            motivo, ok2 = QInputDialog.getText(self, "Suprimento", "Motivo:")
            if ok2:
                try:
                    self.caixa_service.suprimento(self.turno_id, self.user["id"], Decimal(str(valor)), motivo)
                    turno = self.caixa_service.model.get_by_id(self.turno_id)
                    self._update_caixa_display(turno)
                    QMessageBox.information(self, "Sucesso", "Suprimento registrado!")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", str(e))
        self.code_input.setFocus()

    def _voltar(self):
        """Volta ao login."""
        if self.carrinho:
            reply = QMessageBox.question(self, "Atenção", 
                                         "Há itens no carrinho. Sair mesmo assim?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        
        if self.turno_id:
            reply = QMessageBox.question(self, "Atenção", 
                                         "Caixa aberto. Sair mesmo assim?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.close()
        if self.on_logout:
            self.on_logout()

    def keyPressEvent(self, event: QKeyEvent):
        """Atalhos de teclado."""
        if event.key() == Qt.Key.Key_F3:
            self.qty_input.setFocus()
            self.qty_input.selectAll()
        elif event.key() == Qt.Key.Key_F4:
            self._finalize_sale()
        elif event.key() == Qt.Key.Key_F5:
            dialog = BuscaProdutoDialog(self, self.produto_model)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.produto_selecionado:
                prod = dialog.produto_selecionado
                try:
                    qty = float(self.qty_input.text().replace(',', '.'))
                    if qty <= 0: raise ValueError
                except ValueError:
                    qty = 1.0
                
                v_unit = dec(prod["preco_venda"])
                qty_dec = Decimal(str(qty))
                subtotal = v_unit * qty_dec
                
                item = {
                    "id": prod["id"],
                    "nome": prod["nome"],
                    "codigo": prod["codigo_interno"],
                    "qtd": qty,
                    "v_unit": float(v_unit),
                    "subtotal": float(subtotal)
                }
                self.carrinho.append(item)
                self._update_ui_after_item(item)
                
        elif event.key() == Qt.Key.Key_F6:
            if not self.carrinho:
                return
            item_num, ok = QInputDialog.getInt(self, "Cancelar Item", 
                                               f"Item (1 a {len(self.carrinho)}):", 
                                               1, 1, len(self.carrinho))
            if ok:
                removido = self.carrinho.pop(item_num - 1)
                self.table.removeRow(item_num - 1)
                self.total = sum(dec(i["subtotal"]) for i in self.carrinho)
                self.total_lbl.setText(money(self.total))
                
                for row in range(self.table.rowCount()):
                    self.table.item(row, 0).setText(str(row + 1).zfill(3))
                    
        elif event.key() == Qt.Key.Key_F7:
            self._cancel_sale()
        elif event.key() == Qt.Key.Key_F10:
            self._close_caixa()
        else:
            if not self.qty_input.hasFocus():
                self.code_input.setFocus()
            super().keyPressEvent(event)

    def _on_enter_code(self):
        """Adiciona item ao carrinho."""
        code = self.code_input.text().strip()
        if not code:
            if self.carrinho:
                self._finalize_sale()
            return

        try:
            qty = float(self.qty_input.text().replace(',', '.'))
            if qty <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Erro", "Quantidade inválida.")
            self.qty_input.setText("1")
            self.code_input.selectAll()
            return

        product = self.produto_model.get_by_any_code(code)
        
        if not product:
            if not code.isdigit():
                products = self.produto_model.search_products(code, limit=1)
                if products:
                    product = products[0]
            
        if product:
            v_unit = dec(product["preco_venda"])
            qty_dec = Decimal(str(qty))
            subtotal = v_unit * qty_dec
            
            item = {
                "id": product["id"],
                "nome": product["nome"],
                "codigo": product["codigo_interno"],
                "qtd": qty,
                "v_unit": float(v_unit),
                "subtotal": float(subtotal)
            }
            self.carrinho.append(item)
            self._update_ui_after_item(item)
        else:
            QMessageBox.warning(self, "Não Encontrado", f"Produto '{code}' não encontrado.")
            self.code_input.selectAll()

    def _update_ui_after_item(self, item: dict):
        """Atualiza UI após adicionar item."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1).zfill(3)))
        self.table.setItem(row, 1, QTableWidgetItem(item["codigo"]))
        self.table.setItem(row, 2, QTableWidgetItem(item["nome"]))
        
        qtd_item = QTableWidgetItem(str(item["qtd"]))
        qtd_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, qtd_item)
        
        v_unit = QTableWidgetItem(money(item["v_unit"]))
        v_unit.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 4, v_unit)
        
        sub = QTableWidgetItem(money(item["subtotal"]))
        sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 5, sub)
        
        self.table.setRowHeight(row, 35)
        self.table.scrollToBottom()

        self.total = sum(dec(i["subtotal"]) for i in self.carrinho)
        self.total_lbl.setText(money(self.total))

        self.prod_name_lbl.setText(item["nome"])
        self.prod_val_lbl.setText(f"{item['qtd']}x {money(item['v_unit'])} = {money(item['subtotal'])}")

        self.qty_input.setText("1")
        self.code_input.clear()
        self.code_input.setFocus()

    def _cancel_sale(self):
        """Cancela venda."""
        if not self.carrinho:
            return
        reply = QMessageBox.question(self, "Cancelar", "Limpar carrinho?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._reset_sale()

    def _reset_sale(self):
        """Limpa carrinho."""
        self.carrinho.clear()
        self.table.setRowCount(0)
        self.total = Decimal('0')
        self.total_lbl.setText("R$ 0,00")
        self.prod_name_lbl.setText("CAIXA LIVRE")
        self.prod_val_lbl.setText("")
        self.qty_input.setText("1")
        self.code_input.clear()
        self.code_input.setFocus()

    def _finalize_sale(self):
        """Finaliza a venda."""
        if not self.carrinho:
            QMessageBox.warning(self, "Aviso", "Carrinho vazio.")
            return
        
        if not self.turno_id:
            QMessageBox.warning(self, "Atenção", "Abra o caixa primeiro.")
            return
        
        from ui.pdv.pagamento_dialog import PagamentoDialog
        
        total = sum(dec(i["subtotal"]) for i in self.carrinho)
        
        dialog = PagamentoDialog(self, self.user["id"], self.turno_id, self.carrinho, float(total))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", "Venda finalizada!")
            self._reset_sale()
            if self.turno_id:
                turno = self.caixa_service.model.get_by_id(self.turno_id)
                self._update_caixa_display(turno)
