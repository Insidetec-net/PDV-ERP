"""Serviço de Estoque — lógica de negócio para movimentações de estoque."""

import logging
from typing import Dict, List, Optional
from datetime import date

from models.estoque import EstoqueModel
from models.produto import ProdutoModel

logger = logging.getLogger(__name__)


class EstoqueService:
    """Serviço de estoque: orquestra movimentações e consultas de saldo."""

    def __init__(
        self,
        estoque_model: EstoqueModel = None,
        produto_model: ProdutoModel = None,
    ):
        self.estoque_model = estoque_model or EstoqueModel()
        self.produto_model = produto_model or ProdutoModel()

    def ajustar_estoque(
        self,
        produto_id: int,
        usuario_id: int,
        novo_estoque: float,
        motivo: str,
    ) -> int:
        """
        Ajusta o estoque de um produto para um valor absoluto.

        Args:
            produto_id: ID do produto.
            usuario_id: ID do usuário que realizou o ajuste.
            novo_estoque: Valor absoluto alvo do estoque.
            motivo: Motivo do ajuste (registrado em observacao).

        Returns:
            ID da movimentação registrada.
        """
        produto = self.produto_model.get_by_id(produto_id)
        if not produto:
            raise ValueError(f"Produto #{produto_id} não encontrado.")

        estoque_atual = float(produto.get("estoque_atual", 0))
        delta = novo_estoque - estoque_atual

        if delta == 0:
            logger.info(
                "Ajuste ignorado: produto #%s já possui estoque = %s",
                produto_id,
                novo_estoque,
            )
            return 0

        return self.estoque_model.register_movement(
            produto_id=produto_id,
            usuario_id=usuario_id,
            tipo="ajuste",
            quantidade=delta,
            observacao=motivo or f"Ajuste para {novo_estoque}",
        )

    def registrar_entrada(
        self,
        produto_id: int,
        usuario_id: int,
        quantidade: float,
        motivo: Optional[str] = None,
        nota_entrada_id: Optional[int] = None,
    ) -> int:
        """
        Registra entrada de estoque (compra manual ou via NF-e).

        O tipo de movimentacao é 'nfe_entrada' quando nota_entrada_id é
        fornecido, caso contrario 'entrada'.

        Args:
            produto_id: ID do produto.
            usuario_id: ID do usuário que registrou a entrada.
            quantidade: Quantidade a adicionar ao estoque.
            motivo: Observacao/motivo opcional.
            nota_entrada_id: ID da nota de entrada (NF-e), se aplicável.

        Returns:
            ID da movimentação registrada.
        """
        if quantidade <= 0:
            raise ValueError("Quantidade de entrada deve ser maior que zero.")

        tipo = "nfe_entrada" if nota_entrada_id else "entrada"

        return self.estoque_model.register_movement(
            produto_id=produto_id,
            usuario_id=usuario_id,
            tipo=tipo,
            quantidade=quantidade,
            observacao=motivo,
            nota_entrada_id=nota_entrada_id,
        )

    def registrar_saida(
        self,
        produto_id: int,
        usuario_id: int,
        quantidade: float,
        motivo: Optional[str] = None,
    ) -> int:
        """
        Registra saída de estoque (perda, consumo interno, etc.).

        Args:
            produto_id: ID do produto.
            usuario_id: ID do usuário que registrou a saída.
            quantidade: Quantidade a remover do estoque.
            motivo: Observacao/motivo opcional.

        Returns:
            ID da movimentação registrada.
        """
        if quantidade <= 0:
            raise ValueError("Quantidade de saída deve ser maior que zero.")

        return self.estoque_model.register_movement(
            produto_id=produto_id,
            usuario_id=usuario_id,
            tipo="saida",
            quantidade=quantidade,
            observacao=motivo,
        )

    def get_posicao_estoque(self, produto_id: int) -> Dict:
        """
        Retorna a posição de estoque completa de um produto.

        O campo 'status' é calculado a partir de estoque_atual vs
        estoque_minimo:
            - 'zerado' quando estoque_atual <= 0
            - 'baixo'  quando estoque_atual <= estoque_minimo
            - 'ok'     caso contrário

        Args:
            produto_id: ID do produto.

        Returns:
            Dict com 'produto', 'estoque_atual', 'estoque_minimo' e 'status'.
        """
        produto = self.produto_model.get_by_id(produto_id)
        if not produto:
            raise ValueError(f"Produto #{produto_id} não encontrado.")

        estoque_atual = float(produto.get("estoque_atual", 0))
        estoque_minimo = float(produto.get("estoque_minimo", 0))

        if estoque_atual <= 0:
            status = "zerado"
        elif estoque_atual <= estoque_minimo:
            status = "baixo"
        else:
            status = "ok"

        return {
            "produto": produto,
            "estoque_atual": estoque_atual,
            "estoque_minimo": estoque_minimo,
            "status": status,
        }

    def listar_abaixo_minimo(self) -> List[Dict]:
        """Retorna produtos com estoque abaixo do mínimo configurado."""
        return self.produto_model.get_low_stock()

    def get_historico(
        self,
        produto_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tipo: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Consulta histórico de movimentações de um produto com filtros.

        Args:
            produto_id: ID do produto.
            start_date: Data inicial (inclusive) do filtro.
            end_date: Data final (inclusive) do filtro.
            tipo: Filtrar por tipo de movimentacao (ex: entrada, saida, ajuste).
            limit: Máximo de registros retornados (padrão 100).

        Returns:
            Lista de movimentações com dados do produto e usuário.
        """
        return self.estoque_model.get_history(
            produto_id=produto_id,
            start_date=start_date,
            end_date=end_date,
            tipo=tipo,
            limit=limit,
        )
