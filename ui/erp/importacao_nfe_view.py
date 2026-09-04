"""
View de Importação de NF-e (XML).
Lê arquivos XML da Secretaria da Fazenda e cadastra notas de entrada + produtos.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpacerItem, QSizePolicy, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import xml.etree.ElementTree as ET
from pathlib import Path

from models.nota_entrada import NotaEntradaModel
from models.produto import ProdutoModel
from utils.formatters import format_currency


class NFeImportWorker(QThread):
    """Worker em background para processar XMLs sem travar a interface."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list, list) # success_list, error_list

    def __init__(self, file_paths: list, user_id: int):
        super().__init__()
        self.file_paths = file_paths
        self.user_id = user_id
        self.nota_model = NotaEntradaModel()
        self.produto_model = ProdutoModel()

    def run(self):
        success = []
        errors = []
        total = len(self.file_paths)

        for i, path_str in enumerate(self.file_paths):
            path = Path(path_str)
            self.progress.emit(int((i / total) * 100), f"Processando: {path.name}...")
            try:
                # Simples parser de XML da NF-e
                tree = ET.parse(path)
                root = tree.getroot()
                
                # Namespace da SEFAZ
                ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
                
                infNFe = root.find('.//nfe:infNFe', ns)
                if infNFe is None:
                    raise ValueError("Arquivo não é uma NF-e válida.")
                
                chave = infNFe.get('Id', '').replace('NFe', '')
                
                # Emitente
                emit = infNFe.find('nfe:emit', ns)
                cnpj_emitente = emit.find('nfe:CNPJ', ns).text
                nome_emitente = emit.find('nfe:xNome', ns).text
                
                # Ide
                ide = infNFe.find('nfe:ide', ns)
                numero = ide.find('nfe:nNF', ns).text
                serie = ide.find('nfe:serie', ns).text
                data_emissao = ide.find('nfe:dhEmi', ns).text[:10] # YYYY-MM-DD
                
                # Total
                total_nfe = infNFe.find('.//nfe:vNF', ns).text
                
                # Itens
                itens_nodes = infNFe.findall('.//nfe:det', ns)
                itens = []
                for det in itens_nodes:
                    prod = det.find('nfe:prod', ns)
                    cProd = prod.find('nfe:cProd', ns).text
                    xProd = prod.find('nfe:xProd', ns).text
                    qCom = float(prod.find('nfe:qCom', ns).text)
                    vUnCom = float(prod.find('nfe:vUnCom', ns).text)
                    vProd = float(prod.find('nfe:vProd', ns).text)
                    cEAN = prod.find('nfe:cEAN', ns)
                    cEAN = cEAN.text if cEAN is not None and cEAN.text != 'SEM GTIN' else None
                    
                    itens.append({
                        "codigo_fornecedor": cProd,
                        "nome": xProd,
                        "codigo_barras": cEAN,
                        "quantidade": qCom,
                        "custo_unitario": vUnCom,
                        "subtotal": vProd
                    })
                
                # Dados para salvar
                nota_data = {
                    "chave_acesso": chave,
                    "numero": numero,
                    "serie": serie,
                    "cnpj_fornecedor": cnpj_emitente,
                    "nome_fornecedor": nome_emitente,
                    "data_emissao": data_emissao,
                    "valor_total": float(total_nfe)
                }
                
                self.nota_model.import_nfe(nota_data, itens, self.user_id)
                success.append(path.name)
                
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")

        self.progress.emit(100, "Concluído")
        self.finished.emit(success, errors)


class ImportacaoNFeView(QWidget):
    """View para importar arquivos XML da NF-e."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.nota_model = NotaEntradaModel()
        self.worker = None
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Toolbar ===
        toolbar = QHBoxLayout()

        import_btn = QPushButton("📄  Importar XML(s)")
        import_btn.setMinimumHeight(44)
        import_btn.setProperty("class", "success")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self._on_import)
        toolbar.addWidget(import_btn)

        toolbar.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        layout.addLayout(toolbar)
        
        # === Progress Bar ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #8888aa;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # === Tabela de Notas de Entrada ===
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Data Recebimento", "Nº NF-e", "Fornecedor", "Chave", "Total", "Status"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

    def refresh(self):
        try:
            notas = self.nota_model.get_all(order_by="importado_em DESC")
            self.table.setRowCount(len(notas))
            for i, nota in enumerate(notas):
                self.table.setItem(i, 0, QTableWidgetItem(str(nota.get("importado_em", ""))[:16]))
                self.table.setItem(i, 1, QTableWidgetItem(str(nota.get("numero", ""))))
                self.table.setItem(i, 2, QTableWidgetItem(str(nota.get("nome_fornecedor", ""))))
                self.table.setItem(i, 3, QTableWidgetItem(str(nota.get("chave_acesso", ""))))
                
                item_total = QTableWidgetItem(format_currency(nota.get("valor_total", 0)))
                item_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, 4, item_total)
                
                status = nota.get("status", "")
                item_status = QTableWidgetItem("✅ Processada" if status == "processada" else "⏳ Pendente")
                self.table.setItem(i, 5, item_status)
                
                self.table.setRowHeight(i, 40)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar notas:\n{e}")

    def _on_import(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Selecione os arquivos XML", "", "XML Files (*.xml)"
        )
        if not files:
            return

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Iniciando importação...")
        self.status_label.setVisible(True)

        self.worker = NFeImportWorker(files, self.user["id"])
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def _on_finished(self, success, errors):
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        
        msg = f"Importação concluída.\nSucesso: {len(success)}\nFalhas: {len(errors)}"
        if errors:
            msg += "\n\nErros:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
                
        QMessageBox.information(self, "Resultado da Importação", msg)
        self.refresh()
