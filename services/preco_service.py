"""Serviço de cálculos de preço para o Sistema Meu Bazar.

Contém a lógica de cálculo de preço de venda, aplicação de descontos,
verificação de preços promocionais, cálculo de parcelas e formatação
de valores monetários em padrão brasileiro.
"""

import logging
from typing import Optional

from models.produto import ProdutoModel
from database.connection import execute_query

logger = logging.getLogger(__name__)


class PrecoService:
    """Serviço responsável por cálculos de preço de venda, descontos,
    promoções e parcelamentos."""

    @staticmethod
    def calcular_preco_venda(custo: float, markup_percent: float) -> dict:
        """
        Calcula preço de venda a partir do custo e markup percentual.

        Delega o cálculo ao ProdutoModel.calculate_sale_price().

        Args:
            custo: Preço de custo do produto.
            markup_percent: Percentual de markup (ex: 100 = dobrar o preço).

        Returns:
            Dict com preco_venda, margem_lucro e lucro_bruto.
        """
        produto_model = ProdutoModel()
        return produto_model.calculate_sale_price(custo, markup_percent)

    @staticmethod
    def aplicar_desconto(
        preco: float,
        desconto_percent: float,
        desconto_max_percent: float = 20.0,
    ) -> float:
        """
        Aplica desconto ao preço, respeitando teto máximo configurável.

        Args:
            preco: Preço original.
            desconto_percent: Percentual de desconto desejado.
            desconto_max_percent: Teto máximo de desconto (padrão 20%).

        Returns:
            Preço final após desconto, arredondado em 2 casas decimais.
        """
        desconto_efetivo = min(desconto_percent, desconto_max_percent)
        preco_final = preco * (1 - desconto_efetivo / 100)
        logger.debug(
            "Desconto aplicado: %.2f%% (solicitado: %.2f%%) -> R$ %.2f",
            desconto_efetivo, desconto_percent, preco_final,
        )
        return round(preco_final, 2)

    @staticmethod
    def verificar_preco_promocional(produto_id: int) -> Optional[dict]:
        """
        Busca preço promocional vigente para o produto.

        Consulta a tabela 'precos_promocionais' (id, produto_id,
        preco_promocional, data_inicio, data_fim) e retorna o menor
        preço promocional ativo dentro do período de vigência.

        Args:
            produto_id: ID do produto.

        Returns:
            Dict com os dados da promoção, ou None se não houver
            preço promocional vigente.
        """
        query = """
            SELECT *
            FROM precos_promocionais
            WHERE produto_id = %s
              AND data_inicio <= CURDATE()
              AND data_fim >= CURDATE()
            ORDER BY preco_promocional ASC
            LIMIT 1
        """
        result = execute_query(query, (produto_id,), fetch_one=True)
        if result is None:
            logger.debug(
                "Sem preço promocional para produto_id=%d", produto_id
            )
        return result

    @staticmethod
    def calcular_parcelas(
        valor: float, parcelas: int = 1, juros: float = 0.0
    ) -> dict:
        """
        Calcula parcelas com ou sem juros.

        Regra do varejo brasileiro: sem juros para até 3 parcelas.
        Para parcelas > 3, aplica o percentual de juros informado.

        Args:
            valor: Valor total da compra.
            parcelas: Número de parcelas (padrão 1).
            juros: Percentual de juros aplicado quando parcelas > 3.

        Returns:
            Dict com parcelas, valor_parcela, total e juros efetivamente
            aplicados.
        """
        juros_efetivo = 0.0 if parcelas <= 3 else juros
        total = valor * (1 + juros_efetivo / 100)
        valor_parcela = total / parcelas

        logger.debug(
            "Parcelamento: %d x de R$ %.2f (total: R$ %.2f, juros: %.2f%%)",
            parcelas, valor_parcela, total, juros_efetivo,
        )
        return {
            "parcelas": parcelas,
            "valor_parcela": round(valor_parcela, 2),
            "total": round(total, 2),
            "juros": juros_efetivo,
        }

    @staticmethod
    def formatar_preco(preco: float) -> str:
        """
        Formata valor numérico como preço brasileiro (R$ 1.234,56).

        Args:
            preco: Valor numérico.

        Returns:
            String formatada no padrão brasileiro.
        """
        preco_str = f"{preco:,.2f}"
        # Substitui separadores: "," -> "." e "." -> ","
        preco_str = preco_str.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {preco_str}"
