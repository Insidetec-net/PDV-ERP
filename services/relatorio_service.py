"""Serviço de Relatórios do Sistema Meu Bazar.

Camada de lógica entre Models e UI para geração de relatórios gerenciais.
Utiliza SQL agregado (SUM, COUNT, GROUP BY) para extrair dados consolidados
do banco MySQL.
"""

import logging
from datetime import date, datetime
from typing import Optional, Dict, List

from models.venda import VendaModel
from models.produto import ProdutoModel
from models.caixa import CaixaModel
from services.export_service import ExportService
from database.connection import execute_query

logger = logging.getLogger(__name__)


class RelatorioService:
    """Serviço responsável por gerar relatórios analíticos e operacionais."""

    def __init__(self):
        self.venda_model = VendaModel()
        self.produto_model = ProdutoModel()
        self.caixa_model = CaixaModel()
        self.export_service = ExportService()

    # -------------------------------------------------------------------------
    # 1. Relatório de Vendas no Período
    # -------------------------------------------------------------------------
    def relatorio_vendas_periodo(
        self, start_date: date, end_date: date
    ) -> Dict:
        """Retorna resumo de vendas num período.

        Inclui: total vendido (R$), ticket médio, quantidade de vendas
        finalizadas e total/count de cancelamentos.
        """
        logger.info(f"Gerando relatório de vendas: {start_date} a {end_date}")

        # Vendas finalizadas (receita e ticket médio)
        query_vendas = """
            SELECT
                COUNT(*)            AS qtd_vendas,
                COALESCE(SUM(total), 0) AS total_vendido,
                COALESCE(AVG(total), 0) AS ticket_medio
            FROM vendas
            WHERE status = 'finalizada'
              AND DATE(criado_em) BETWEEN %s AND %s
        """
        result_vendas = execute_query(query_vendas, (start_date, end_date), fetch_one=True)

        # Cancelamentos
        query_cancel = """
            SELECT
                COUNT(*)                AS qtd_cancelamentos,
                COALESCE(SUM(total), 0) AS total_cancelado
            FROM vendas
            WHERE status = 'cancelada'
              AND DATE(criado_em) BETWEEN %s AND %s
        """
        result_cancel = execute_query(query_cancel, (start_date, end_date), fetch_one=True)

        return {
            "periodo": {
                "inicio": str(start_date),
                "fim": str(end_date),
            },
            "vendas": {
                "quantidade": result_vendas["qtd_vendas"] if result_vendas else 0,
                "total": float(result_vendas["total_vendido"] or 0),
                "ticket_medio": float(result_vendas["ticket_medio"] or 0),
            },
            "cancelamentos": {
                "quantidade": result_cancel["qtd_cancelamentos"] if result_cancel else 0,
                "total": float(result_cancel["total_cancelado"] or 0),
            },
        }

    # -------------------------------------------------------------------------
    # 2. Vendas por Forma de Pagamento
    # -------------------------------------------------------------------------
    def relatorio_vendas_por_forma_pagamento(
        self, start_date: date, end_date: date
    ) -> List[Dict]:
        """Agrega vendas finalizadas por forma de pagamento.

        Retorna lista com forma_pagamento, quantidade, valor total e
        percentual do total.
        """
        logger.info(
            f"Gerando relatório por forma de pagamento: {start_date} a {end_date}"
        )

        query = """
            SELECT
                pv.forma                           AS forma_pagamento,
                COUNT(DISTINCT pv.venda_id)        AS qtd_vendas,
                COALESCE(SUM(pv.valor), 0)        AS total_forma
            FROM pagamentos_venda pv
            JOIN vendas v ON pv.venda_id = v.id
            WHERE v.status = 'finalizada'
              AND DATE(v.criado_em) BETWEEN %s AND %s
            GROUP BY pv.forma
            ORDER BY total_forma DESC
        """
        rows = execute_query(query, (start_date, end_date)) or []

        # Calcular percentual
        total_geral = sum(float(r["total_forma"]) for r in rows) or 1.0
        for r in rows:
            r["total_forma"] = float(r["total_forma"])
            r["percentual"] = round(float(r["total_forma"]) / total_geral * 100, 2)

        return rows

    # -------------------------------------------------------------------------
    # 3. Produtos Mais Vendidos
    # -------------------------------------------------------------------------
    def relatorio_produtos_mais_vendidos(
        self, start_date: date, end_date: date, limit: int = 20
    ) -> List[Dict]:
        """Retorna os top N produtos mais vendidos por quantidade.

        Args:
            start_date: Data inicial.
            end_date: Data final.
            limit: Número máximo de produtos (padrão 20).
        """
        logger.info(
            f"Gerando relatório top {limit} produtos: {start_date} a {end_date}"
        )

        query = """
            SELECT
                p.id                               AS produto_id,
                p.nome                             AS produto_nome,
                p.codigo_interno,
                COALESCE(SUM(vi.quantidade), 0)   AS qtd_vendida,
                COALESCE(SUM(vi.subtotal), 0)     AS total_vendido
            FROM venda_itens vi
            JOIN vendas v     ON vi.venda_id = v.id
            JOIN produtos p   ON vi.produto_id = p.id
            WHERE v.status = 'finalizada'
              AND DATE(v.criado_em) BETWEEN %s AND %s
            GROUP BY p.id, p.nome, p.codigo_interno
            ORDER BY qtd_vendida DESC
            LIMIT %s
        """
        rows = execute_query(query, (start_date, end_date, int(limit))) or []

        for r in rows:
            r["total_vendido"] = float(r["total_vendido"])
            r["qtd_vendida"] = int(r["qtd_vendida"])

        return rows

    # -------------------------------------------------------------------------
    # 4. Estoque Baixo (delega ao ProdutoModel)
    # -------------------------------------------------------------------------
    def relatorio_estoque_baixo(self) -> List[Dict]:
        """Retorna produtos com estoque atual abaixo do mínimo.

        Delega a lógica de query ao ProdutoModel.get_low_stock().
        """
        logger.info("Gerando relatório de estoque baixo")
        return self.produto_model.get_low_stock()

    # -------------------------------------------------------------------------
    # 5. Faturamento Diário
    # -------------------------------------------------------------------------
    def relatorio_faturamento_diario(
        self, start_date: date, end_date: date
    ) -> List[Dict]:
        """Retorna faturamento agrupado por dia.

        Inclui total vendido, quantidade de vendas e ticket médio diário.
        """
        logger.info(
            f"Gerando relatório faturamento diário: {start_date} a {end_date}"
        )

        query = """
            SELECT
                DATE(criado_em)                 AS dia,
                COUNT(*)                        AS qtd_vendas,
                COALESCE(SUM(total), 0)        AS faturamento,
                COALESCE(AVG(total), 0)        AS ticket_medio
            FROM vendas
            WHERE status = 'finalizada'
              AND DATE(criado_em) BETWEEN %s AND %s
            GROUP BY DATE(criado_em)
            ORDER BY dia ASC
        """
        rows = execute_query(query, (start_date, end_date)) or []

        for r in rows:
            r["faturamento"] = float(r["faturamento"])
            r["ticket_medio"] = float(r["ticket_medio"])
            r["qtd_vendas"] = int(r["qtd_vendas"])
            r["dia"] = str(r["dia"])

        return rows

    # -------------------------------------------------------------------------
    # 6. Relatório Completo de Turno (Caixa)
    # -------------------------------------------------------------------------
    def relatorio_caixa_turno(self, turno_id: int) -> Dict:
        """Retorna resumo completo de um turno de caixa.

        Inclui dados do turno, totais por forma de pagamento,
        movimentações (sangrias/suprimentos) e lista de vendas.
        """
        logger.info(f"Gerando relatório do turno #{turno_id}")

        # Dados do turno
        turno = execute_query(
            "SELECT * FROM turnos WHERE id = %s", (turno_id,), fetch_one=True
        )
        if not turno:
            raise ValueError(f"Turno #{turno_id} não encontrado.")

        # Resumo de pagamentos no turno
        query_pagamentos = """
            SELECT
                pv.forma                           AS forma_pagamento,
                COUNT(DISTINCT pv.venda_id)        AS qtd,
                COALESCE(SUM(pv.valor), 0)        AS total
            FROM pagamentos_venda pv
            JOIN vendas v ON pv.venda_id = v.id
            WHERE v.turno_id = %s AND v.status = 'finalizada'
            GROUP BY pv.forma
            ORDER BY total DESC
        """
        pagamentos = execute_query(query_pagamentos, (turno_id,)) or []
        for p in pagamentos:
            p["total"] = float(p["total"])

        # Movimentações de caixa
        movimentacoes = self.caixa_model.get_shift_movements(turno_id)

        # Vendas do turno
        vendas = self.venda_model.get_sales_by_period(
            start_date=turno["abertura"].date() if turno["abertura"] else date.today(),
            end_date=date.today(),
        )
        # Filtrar por turno_id
        vendas_turno = [v for v in (vendas or []) if v.get("turno_id") == turno_id]

        return {
            "turno": {
                "id": turno["id"],
                "status": turno["status"],
                "abertura": str(turno["abertura"]) if turno["abertura"] else None,
                "fechamento": str(turno["fechamento"]) if turno["fechamento"] else None,
                "valor_abertura": float(turno["valor_abertura"] or 0),
                "valor_fechamento": float(turno["valor_fechamento"] or 0),
                "total_vendas": float(turno["total_vendas"] or 0),
                "total_cancelamentos": float(turno["total_cancelamentos"] or 0),
                "total_sangrias": float(turno["total_sangrias"] or 0),
                "total_suprimentos": float(turno["total_suprimentos"] or 0),
                "qtd_vendas": int(turno["qtd_vendas"] or 0),
                "diferenca": float(turno["diferenca"] or 0),
            },
            "pagamentos_por_forma": pagamentos,
            "movimentacoes": movimentacoes,
            "vendas": vendas_turno,
        }

    # -------------------------------------------------------------------------
    # 7. Exportar Relatório para Excel
    # -------------------------------------------------------------------------
    def exportar_relatorio(
        self,
        tipo: str,
        start_date: date,
        end_date: date,
        output_dir: str,
    ) -> str:
        """Gera um relatório e exporta para Excel via ExportService.

        Args:
            tipo: Tipo do relatório ('vendas_periodo', 'forma_pagamento',
                  'produtos_vendidos', 'estoque_baixo', 'faturamento_diario').
            start_date: Data inicial (ignorada para estoque_baixo).
            end_date: Data final (ignorada para estoque_baixo).
            output_dir: Diretório onde o .xlsx será salvo.

        Returns:
            Caminho completo do arquivo gerado.
        """
        logger.info(f"Exportando relatório '{tipo}' para {output_dir}")

        tipo_relatorio = tipo.lower().strip()
        relatorio_gerado = None

        if tipo_relatorio == "vendas_periodo":
            dados = self.relatorio_vendas_periodo(start_date, end_date)
            columns = ["Métrica", "Valor"]
            data = [
                ["Total Vendado", f"R$ {dados['vendas']['total']:.2f}"],
                ["Ticket Médio", f"R$ {dados['vendas']['ticket_medio']:.2f}"],
                ["Quantidade Vendas", dados["vendas"]["quantidade"]],
                ["Total Cancelado", f"R$ {dados['cancelamentos']['total']:.2f}"],
                ["Qtd Cancelamentos", dados["cancelamentos"]["quantidade"]],
            ]
            title = f"Vendas no Período ({start_date} a {end_date})"

        elif tipo_relatorio == "forma_pagamento":
            dados = self.relatorio_vendas_por_forma_pagamento(start_date, end_date)
            columns = ["Forma de Pagamento", "Qtd Vendas", "Total (R$)", "%"]
            data = [
                [
                    d["forma_pagamento"],
                    d["qtd_vendas"],
                    f"R$ {d['total_forma']:.2f}",
                    f"{d['percentual']}%",
                ]
                for d in dados
            ]
            title = f"Vendas por Forma de Pagamento ({start_date} a {end_date})"

        elif tipo_relatorio == "produtos_vendidos":
            dados = self.relatorio_produtos_mais_vendidos(start_date, end_date)
            columns = ["Código Interno", "Produto", "Qtd Vendida", "Total (R$)"]
            data = [
                [
                    d.get("codigo_interno", "-"),
                    d["produto_nome"],
                    d["qtd_vendida"],
                    f"R$ {d['total_vendido']:.2f}",
                ]
                for d in dados
            ]
            title = f"Produtos Mais Vendidos ({start_date} a {end_date})"

        elif tipo_relatorio == "estoque_baixo":
            dados = self.relatorio_estoque_baixo()
            columns = ["Código", "Produto", "Estoque Atual", "Estoque Mínimo", "Falta"]
            data = [
                [
                    d.get("codigo_interno", "-"),
                    d["nome"],
                    d["estoque_atual"],
                    d["estoque_minimo"],
                    int(d["estoque_minimo"] - d["estoque_atual"]),
                ]
                for d in dados
            ]
            title = "Produtos com Estoque Baixo"

        elif tipo_relatorio == "faturamento_diario":
            dados = self.relatorio_faturamento_diario(start_date, end_date)
            columns = ["Dia", "Qtd Vendas", "Faturamento (R$)", "Ticket Médio (R$)"]
            data = [
                [
                    d["dia"],
                    d["qtd_vendas"],
                    f"R$ {d['faturamento']:.2f}",
                    f"R$ {d['ticket_medio']:.2f}",
                ]
                for d in dados
            ]
            title = f"Faturamento Diário ({start_date} a {end_date})"

        else:
            raise ValueError(
                f"Tipo de relatório não suportado: '{tipo}'. "
                f"Válidos: vendas_periodo, forma_pagamento, "
                f"produtos_vendidos, estoque_baixo, faturamento_diario"
            )

        filepath = self.export_service.export_to_excel(
            title=title,
            columns=columns,
            data=data,
            default_dir=output_dir,
        )

        logger.info(f"Relatório exportado com sucesso: {filepath}")
        return filepath
