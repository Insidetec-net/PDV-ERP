"""
View de Relatórios — Vendas, Curva ABC, Estoque, Movimentações de Caixa.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QDateEdit, QMessageBox, QSpacerItem, QSizePolicy,
    QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ui.components.data_table import DataTable
from models.relatorio import RelatorioModel
from services.export_service import ExportService
from utils.formatters import format_currency, format_datetime

class RelatoriosView(QWidget):
    """View para geração de relatórios e exportação."""

    def __init__(self, user_data: dict):
        super().__init__()
        self.user = user_data
        self.relatorio_model = RelatorioModel()
        self._current_data = []
        self._current_columns = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("📊 Central de Relatórios")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(title)

        # ==========================================
        # CARTÃO DE FILTROS E AÇÕES
        # ==========================================
        self.filter_card = QFrame()
        self.filter_card.setStyleSheet(
            "QFrame { background-color: #16213e; border: 1px solid #2a2a4a; border-radius: 8px; }"
        )
        card_layout = QVBoxLayout(self.filter_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(16)

        # Linha 1: Controles de Filtro
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)
        
        # Tipo de Relatório
        tipo_layout = QVBoxLayout()
        tipo_layout.setSpacing(4)
        lbl_tipo = QLabel("Tipo de Relatório")
        lbl_tipo.setStyleSheet("color: #8888aa; font-weight: bold; border: none; background: transparent;")
        tipo_layout.addWidget(lbl_tipo)
        
        self.tipo_combo = QComboBox()
        self.tipo_combo.setMinimumHeight(38)
        self.tipo_combo.addItems([
            "Vendas por Período",
            "Curva ABC de Produtos (Mais Vendidos)",
            "Estoque Atual (Imobilizado)",
            "Movimentações de Caixa"
        ])
        tipo_layout.addWidget(self.tipo_combo)
        controls_layout.addLayout(tipo_layout, stretch=2)

        # Data Inicial
        start_layout = QVBoxLayout()
        start_layout.setSpacing(4)
        lbl_start = QLabel("Data Inicial")
        lbl_start.setStyleSheet("color: #8888aa; font-weight: bold; border: none; background: transparent;")
        start_layout.addWidget(lbl_start)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setMinimumHeight(38)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        start_layout.addWidget(self.start_date)
        controls_layout.addLayout(start_layout, stretch=1)

        # Data Final
        end_layout = QVBoxLayout()
        end_layout.setSpacing(4)
        lbl_end = QLabel("Data Final")
        lbl_end.setStyleSheet("color: #8888aa; font-weight: bold; border: none; background: transparent;")
        end_layout.addWidget(lbl_end)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setMinimumHeight(38)
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        end_layout.addWidget(self.end_date)
        controls_layout.addLayout(end_layout, stretch=1)

        controls_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        card_layout.addLayout(controls_layout)

        # Linha 2: Botões de Ação
        action_layout = QHBoxLayout()
        
        gen_btn = QPushButton("📄  Gerar Relatório na Tela")
        gen_btn.setProperty("class", "accent")
        gen_btn.setMinimumHeight(44)
        gen_btn.setMinimumWidth(220)
        gen_btn.clicked.connect(self._on_generate)
        action_layout.addWidget(gen_btn)

        self.export_btn = QPushButton("💾  Exportar para Excel")
        self.export_btn.setProperty("class", "success")
        self.export_btn.setMinimumHeight(44)
        self.export_btn.setMinimumWidth(220)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export)
        action_layout.addWidget(self.export_btn)
        
        action_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        card_layout.addLayout(action_layout)

        layout.addWidget(self.filter_card)

        # Container for DataTable
        self.table_container = QVBoxLayout()
        layout.addLayout(self.table_container)
        
        self.table = None # Será recriada dinamicamente

    def _create_table(self, columns):
        if self.table:
            self.table_container.removeWidget(self.table)
            self.table.deleteLater()
            
        self.table = DataTable(columns=columns, page_size=100, show_actions=False)
        self.table_container.addWidget(self.table)

    def _on_generate(self):
        tipo_idx = self.tipo_combo.currentIndex()
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        
        if tipo_idx == 0:
            # Vendas por Período
            cols = [
                {"key": "data", "label": "Data", "formatter": lambda x: x.strftime("%d/%m/%Y") if hasattr(x, 'strftime') else str(x)},
                {"key": "total_vendas", "label": "Qtd. Vendas", "align": "center"},
                {"key": "receita_total", "label": "Receita Total", "formatter": format_currency, "align": "right"}
            ]
            self._create_table(cols)
            data = self.relatorio_model.get_vendas_por_periodo(start, end)
            
        elif tipo_idx == 1:
            # Curva ABC
            cols = [
                {"key": "codigo_interno", "label": "Código"},
                {"key": "nome", "label": "Produto"},
                {"key": "qtd_vendida", "label": "Qtd Vendida", "align": "center"},
                {"key": "receita_gerada", "label": "Receita Gerada", "formatter": format_currency, "align": "right"}
            ]
            self._create_table(cols)
            data = self.relatorio_model.get_curva_abc(start, end)
            
        elif tipo_idx == 2:
            # Estoque Atual
            cols = [
                {"key": "codigo_interno", "label": "Código"},
                {"key": "nome", "label": "Produto"},
                {"key": "estoque_atual", "label": "Qtd Estoque", "align": "center"},
                {"key": "preco_custo", "label": "Custo Unit.", "formatter": format_currency, "align": "right"},
                {"key": "custo_imobilizado", "label": "Custo Imob. (R$)", "formatter": format_currency, "align": "right"}
            ]
            self._create_table(cols)
            data = self.relatorio_model.get_estoque_atual()
            
        elif tipo_idx == 3:
            # Movimentações de Caixa
            cols = [
                {"key": "data_hora", "label": "Data/Hora", "formatter": format_datetime},
                {"key": "tipo", "label": "Tipo", "align": "center"},
                {"key": "valor", "label": "Valor (R$)", "formatter": format_currency, "align": "right"},
                {"key": "operador", "label": "Operador"},
                {"key": "observacao", "label": "Observação"}
            ]
            self._create_table(cols)
            data = self.relatorio_model.get_movimentacoes_caixa(start, end)

        self._current_columns = cols
        self._current_data = data
        self.table.set_data(data)
        
        self.export_btn.setEnabled(len(data) > 0)
        
        if not data:
            QMessageBox.information(self, "Relatório", "Nenhum dado encontrado para o período/filtro selecionado.")

    def _on_export(self):
        if not self._current_data:
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Selecione a pasta para salvar o Excel")
        if not folder:
            return
            
        # Preparar dados formatados para a planilha
        headers = [col["label"] for col in self._current_columns]
        
        export_data = []
        for row in self._current_data:
            row_list = []
            for col in self._current_columns:
                val = row.get(col["key"], "")
                if "formatter" in col and col["formatter"] and val is not None:
                    try:
                        val = col["formatter"](val)
                    except:
                        pass
                row_list.append(val)
            export_data.append(row_list)
            
        try:
            title = self.tipo_combo.currentText()
            path = ExportService.export_to_excel(title, headers, export_data, folder)
            QMessageBox.information(self, "Sucesso", f"Relatório exportado com sucesso em:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar Excel:\n{e}")
