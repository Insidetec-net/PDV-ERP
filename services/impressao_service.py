"""
Serviço de Impressão — Centraliza a geração de PDFs do sistema.
Cupom de venda, etiquetas térmicas, relatório de fechamento de turno,
e listagem de produtos.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict

from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument

from database.connection import execute_query
from services.fiscal_service import FiscalService
from services.barcode_service import BarcodeService
from models.venda import VendaModel
from models.produto import ProdutoModel
from models.caixa import CaixaModel

logger = logging.getLogger(__name__)


class ImpressaoService:
    """
    Serviço centralizado de geração de documentos PDF.
    Usa QPrinter/QTextDocument para renderizar HTML como PDF.
    """

    def __init__(self):
        self.fiscal_service = FiscalService()
        self.barcode_service = BarcodeService()
        self.venda_model = VendaModel()
        self.produto_model = ProdutoModel()
        self.caixa_model = CaixaModel()

    @staticmethod
    def _ensure_output_dir(output_dir: str) -> str:
        """Garante que o diretório de saída existe."""
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    @staticmethod
    def _html_to_pdf(html: str, output_path: str, page_mm: tuple = (210, 297)) -> str:
        """
        Renderiza HTML para PDF usando QTextDocument + QPrinter.

        Args:
            html: Conteúdo HTML a renderizar.
            output_path: Caminho completo do arquivo PDF de saída.
            page_mm: Tamanho da página em milímetros (largura, altura). Padrão A4.

        Returns:
            Caminho do PDF gerado.
        """
        from PyQt6.QtCore import QSizeF, QMarginsF

        doc = QTextDocument()
        doc.setHtml(html)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageSize(QPrinter.PageSize(
            QSizeF(page_mm[0], page_mm[1]),
            QPrinter.Unit.Millimeter
        ))
        printer.setPageMargins(
            QMarginsF(10, 10, 10, 10),
            QPrinter.PageLayout.Unit.Millimeter
        )

        doc.print(printer)
        return output_path

    def imprimir_cupom_venda(self, venda_id: int, output_dir: str) -> str:
        """
        Gera o cupom (DANFE Fake NFC-e) de uma venda.

        Args:
            venda_id: ID da venda.
            output_dir: Diretório onde salvar o PDF.

        Returns:
            Caminho completo do PDF gerado.

        Raises:
            ValueError se a venda não for encontrada.
        """
        self._ensure_output_dir(output_dir)

        venda = self.venda_model.get_sale_details(venda_id)
        if not venda:
            raise ValueError(f"Venda #{venda_id} não encontrada.")

        itens = []
        for item in venda.get("itens", []):
            itens.append({
                "nome": item.get("produto_nome", "PRODUTO"),
                "quantidade": float(item.get("quantidade", 1)),
                "preco_unitario": float(item.get("preco_unitario", 0)),
            })

        pagamentos = []
        for pag in venda.get("pagamentos", []):
            pagamentos.append({
                "forma": pag.get("forma", "dinheiro"),
                "valor": float(pag.get("valor", 0)),
            })

        total = float(venda.get("total", 0))

        filename = f"Cupom_Venda_{venda_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_dir, filename)

        self.fiscal_service.gerar_danfe_fake_pdf(
            venda_id=venda_id,
            itens=itens,
            pagamentos=pagamentos,
            total=total,
            output_path=output_path,
        )

        logger.info(f"Cupom venda #{venda_id} gerado: {output_path}")
        return output_path

    def imprimir_etiqueta_produto(self, produto_id: int, quantidade: int = 1, output_dir: str = None) -> str:
        """
        Gera etiquetas térmicas (PDF) para um produto.

        Args:
            produto_id: ID do produto.
            quantidade: Número de etiquetas a gerar.
            output_dir: Diretório onde salvar o PDF.

        Returns:
            Caminho completo do PDF gerado.

        Raises:
            ValueError se o produto não for encontrado.
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Etiquetas")
        self._ensure_output_dir(output_dir)

        produto = self.produto_model.get_by_id(produto_id)
        if not produto:
            raise ValueError(f"Produto #{produto_id} não encontrado.")

        codigo = produto.get("codigo_interno") or produto.get("codigo_barras", "")
        if not codigo:
            codigo = f"MB-{produto_id:06d}"

        produtos_list = [{
            "nome": produto.get("nome", "PRODUTO"),
            "preco": float(produto.get("preco_venda", 0)),
            "codigo": codigo,
            "quantidade": quantidade,
        }]

        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in produto.get("nome", "produto")[:30])
        filename = f"Etiqueta_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_dir, filename)

        self.barcode_service.gerar_pdf_etiquetas_termicas(produtos_list, output_path)

        logger.info(f"Etiqueta produto #{produto_id} gerada: {output_path}")
        return output_path

    def imprimir_relatorio_turno(self, turno_id: int, output_dir: str) -> str:
        """
        Gera relatório de fechamento de caixa (turno) em PDF.

        Inclui: dados de abertura, vendas realizadas, sangrias, suprimentos,
        totais e diferença.

        Args:
            turno_id: ID do turno.
            output_dir: Diretório onde salvar o PDF.

        Returns:
            Caminho completo do PDF gerado.

        Raises:
            ValueError se o turno não for encontrado.
        """
        self._ensure_output_dir(output_dir)

        turno = self.caixa_model.get_by_id(turno_id)
        if not turno:
            raise ValueError(f"Turno #{turno_id} não encontrado.")

        # Buscar movimentações detalhadas
        movimentacoes = self.caixa_model.get_shift_movements(turno_id) or []

        sangrias = [m for m in movimentacoes if m.get("tipo") == "sangria"]
        suprimentos = [m for m in movimentacoes if m.get("tipo") == "suprimento"]

        # Buscar vendas do turno
        vendas = execute_query(
            """
            SELECT v.id, v.total, v.status, v.criado_em, u.nome as operador
            FROM vendas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.turno_id = %s
            ORDER BY v.criado_em
            """,
            (turno_id,),
        ) or []

        # Montar HTML
        html = self._build_relatorio_turno_html(turno, vendas, sangrias, suprimentos)

        filename = f"Relatorio_Turno_{turno_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_dir, filename)

        self._html_to_pdf(html, output_path)

        logger.info(f"Relatório turno #{turno_id} gerado: {output_path}")
        return output_path

    def imprimir_lista_produtos(self, produtos: List[Dict], output_dir: str) -> str:
        """
        Gera uma listagem simples de produtos em PDF (consulta).
        Colunas: Nome, Código, Preço.

        Args:
            produtos: Lista de dicts com chaves 'nome', 'codigo', 'preco'.
            output_dir: Diretório onde salvar o PDF.

        Returns:
            Caminho completo do PDF gerado.

        Raises:
            ValueError se a lista de produtos estiver vazia.
        """
        self._ensure_output_dir(output_dir)

        if not produtos:
            raise ValueError("A lista de produtos está vazia.")

        html = self._build_lista_produtos_html(produtos)

        filename = f"Lista_Produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_dir, filename)

        self._html_to_pdf(html, output_path)

        logger.info(f"Lista de produtos gerada ({len(produtos)} itens): {output_path}")
        return output_path

    @staticmethod
    def _build_relatorio_turno_html(turno: dict, vendas: list, sangrias: list, suprimentos: list) -> str:
        """Monta o HTML do relatório de fechamento de turno."""

        def fmt(valor) -> str:
            try:
                return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except (ValueError, TypeError):
                return "R$ 0,00"

        def fmt_data(valor) -> str:
            if not valor:
                return "-"
            if isinstance(valor, str):
                try:
                    from datetime import datetime as dt
                    valor = dt.fromisoformat(valor)
                except (ValueError, TypeError):
                    return str(valor)
            try:
                return valor.strftime("%d/%m/%Y %H:%M")
            except AttributeError:
                return str(valor)

        valor_abertura = float(turno.get("valor_abertura", 0))
        total_vendas = float(turno.get("total_vendas", 0))
        total_cancelamentos = float(turno.get("total_cancelamentos", 0))
        total_sangrias = float(turno.get("total_sangrias", 0))
        total_suprimentos = float(turno.get("total_suprimentos", 0))
        valor_fechamento = turno.get("valor_fechamento")
        diferenca = turno.get("diferenca")

        valor_esperado = valor_abertura + total_vendas - total_cancelamentos - total_sangrias + total_suprimentos

        status_turno = turno.get("status", "aberto").upper()
        operador = turno.get("operador_nome", "-")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #333; margin: 0; padding: 20px; }}
                h1 {{ text-align: center; font-size: 18px; margin-bottom: 5px; }}
                h2 {{ text-align: center; font-size: 14px; color: #555; margin-top: 0; }}
                .header-info {{ text-align: center; color: #666; margin-bottom: 20px; font-size: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th {{ background-color: #2c3e50; color: white; padding: 8px 5px; text-align: left; font-size: 11px; }}
                td {{ padding: 6px 5px; border-bottom: 1px solid #ddd; font-size: 11px; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .total-row {{ font-weight: bold; background-color: #ecf0f1 !important; }}
                .positive {{ color: #27ae60; }}
                .negative {{ color: #e74c3c; }}
                .resumo-box {{ border: 2px solid #2c3e50; padding: 15px; margin: 15px 0; background: #fafafa; }}
                .resumo-box h3 {{ margin-top: 0; font-size: 13px; }}
                .grid {{ display: flex; justify-content: space-between; flex-wrap: wrap; }}
                .grid-item {{ width: 48%; }}
                .section-title {{ font-size: 13px; font-weight: bold; margin-top: 20px; margin-bottom: 5px; border-bottom: 2px solid #2c3e50; padding-bottom: 3px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 9px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; }}
                .destaque {{ font-size: 14px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>RELATÓRIO DE FECHAMENTO DE CAIXA</h1>
            <h2>Turno #{turno.get("id")} — Status: {status_turno}</h2>
            <div class="header-info">
                Operador: <b>{operador}</b> |
                Abertura: <b>{fmt_data(turno.get("abertura"))}</b>
                {f"| Fechamento: <b>{fmt_data(turno.get('fechamento'))}</b>" if turno.get("fechamento") else ""}
            </div>

            <div class="resumo-box">
                <h3>RESUMO FINANCEIRO</h3>
                <table>
                    <tr><td>Valor de Abertura</td><td align="right" class="destaque">{fmt(valor_abertura)}</td></tr>
                    <tr><td>(+) Total Vendas</td><td align="right" class="positive">+{fmt(total_vendas)}</td></tr>
                    <tr><td>(-) Cancelamentos</td><td align="right" class="negative">-{fmt(total_cancelamentos)}</td></tr>
                    <tr><td>(-) Sangrias</td><td align="right" class="negative">-{fmt(total_sangrias)}</td></tr>
                    <tr><td>(+) Suprimentos</td><td align="right" class="positive">+{fmt(total_suprimentos)}</td></tr>
                    <tr class="total-row"><td>VALOR ESPERADO</td><td align="right" class="destaque">{fmt(valor_esperado)}</td></tr>
                </table>
            </div>
        """

        if valor_fechamento is not None:
            dif_class = "positive" if (diferenca or 0) >= 0 else "negative"
            html += f"""
            <div class="resumo-box">
                <h3>CONFERÊNCIA</h3>
                <table>
                    <tr><td>Valor Informado (Fechamento)</td><td align="right" class="destaque">{fmt(valor_fechamento)}</td></tr>
                    <tr class="total-row"><td>Diferença</td><td align="right class="{dif_class}">{fmt(diferenca)}</td></tr>
                </table>
            </div>
            """

        # Seção Vendas
        html += '<div class="section-title">VENDAS DO TURNO</div>'
        if vendas:
            html += '<table><tr><th>#</th><th>Valor</th><th>Status</th><th>Data/Hora</th><th>Operador</th></tr>'
            for v in vendas:
                status_color = "#27ae60" if v.get("status") == "finalizada" else "#e74c3c"
                html += (
                    f'<tr><td>{v.get("id")}</td>'
                    f'<td align="right">{fmt(v.get("total", 0))}</td>'
                    f'<td style="color:{status_color}">{v.get("status", "").upper()}</td>'
                    f'<td>{fmt_data(v.get("criado_em"))}</td>'
                    f'<td>{v.get("operador", "-")}</td></tr>'
                )
            html += '</table>'
        else:
            html += '<p style="color:#999; font-style:italic;">Nenhuma venda registrada neste turno.</p>'

        # Seção Sangrias
        html += '<div class="section-title">SANGRIAS</div>'
        if sangrias:
            html += '<table><tr><th>#</th><th>Valor</th><th>Motivo</th><th>Data/Hora</th><th>Operador</th></tr>'
            for s in sangrias:
                html += (
                    f'<tr><td>{s.get("id")}</td>'
                    f'<td align="right" class="negative">-{fmt(s.get("valor", 0))}</td>'
                    f'<td>{s.get("motivo", "-")}</td>'
                    f'<td>{fmt_data(s.get("criado_em"))}</td>'
                    f'<td>{s.get("usuario_nome", "-")}</td></tr>'
                )
            html += f'<tr class="total-row"><td colspan="4">Total Sangrias</td><td align="right" class="negative">-{fmt(total_sangrias)}</td></tr></table>'
        else:
            html += '<p style="color:#999; font-style:italic;">Nenhuma sangria registrada.</p>'

        # Seção Suprimentos
        html += '<div class="section-title">SUPRIMENTOS</div>'
        if suprimentos:
            html += '<table><tr><th>#</th><th>Valor</th><th>Motivo</th><th>Data/Hora</th><th>Operador</th></tr>'
            for s in suprimentos:
                html += (
                    f'<tr><td>{s.get("id")}</td>'
                    f'<td align="right" class="positive">+{fmt(s.get("valor", 0))}</td>'
                    f'<td>{s.get("motivo", "-")}</td>'
                    f'<td>{fmt_data(s.get("criado_em"))}</td>'
                    f'<td>{s.get("usuario_nome", "-")}</td></tr>'
                )
            html += f'<tr class="total-row"><td colspan="4">Total Suprimentos</td><td align="right" class="positive">+{fmt(total_suprimentos)}</td></tr></table>'
        else:
            html += '<p style="color:#999; font-style:italic;">Nenhum suprimento registrado.</p>'

        html += f"""
            <div class="footer">
                Sistema Meu Bazar — Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def _build_lista_produtos_html(produtos: List[Dict]) -> str:
        """Monta o HTML da listagem simples de produtos."""

        def fmt(valor) -> str:
            try:
                return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except (ValueError, TypeError):
                return "R$ 0,00"

        total_itens = len(produtos)
        valor_total = sum(float(p.get("preco", 0)) for p in produtos)

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #333; margin: 0; padding: 20px; }}
                h1 {{ text-align: center; font-size: 18px; margin-bottom: 5px; }}
                .header-info {{ text-align: center; color: #666; margin-bottom: 20px; font-size: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th {{ background-color: #2c3e50; color: white; padding: 8px 5px; text-align: left; font-size: 11px; }}
                td {{ padding: 6px 5px; border-bottom: 1px solid #ddd; font-size: 11px; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .total-row {{ font-weight: bold; background-color: #ecf0f1 !important; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 9px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>LISTAGEM DE PRODUTOS</h1>
            <div class="header-info">
                Consulta gerada em <b>{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</b> |
                <b>{total_itens}</b> produto(s)
            </div>

            <table>
                <tr><th width="5%">#</th><th width="50%">Produto</th><th width="20%">Código</th><th width="25%" align="right">Preço</th></tr>
        """

        for idx, p in enumerate(produtos, 1):
            nome = p.get("nome", "PRODUTO")
            codigo = p.get("codigo", p.get("codigo_interno", p.get("codigo_barras", "-")))
            preco = p.get("preco", p.get("preco_venda", 0))
            html += f'<tr><td>{idx}</td><td>{nome}</td><td>{codigo}</td><td align="right">{fmt(preco)}</td></tr>'

        html += f"""
                <tr class="total-row">
                    <td colspan="3">Total Geral</td>
                    <td align="right">{fmt(valor_total)}</td>
                </tr>
            </table>

            <div class="footer">
                Sistema Meu Bazar — Documento para consulta
            </div>
        </body>
        </html>
        """
        return html
