"""DAO de Movimentações de Estoque."""

from typing import List, Dict
from datetime import date

from models.base_model import BaseModel
from database.connection import execute_query, db_transaction


class EstoqueModel(BaseModel):
    TABLE_NAME = "movimentacoes_estoque"
    FIELDS = [
        "id", "produto_id", "usuario_id", "nota_entrada_id", "tipo",
        "quantidade", "estoque_anterior", "estoque_posterior",
        "observacao", "criado_em",
    ]

    def register_movement(
        self,
        produto_id: int,
        usuario_id: int,
        tipo: str,
        quantidade: float,
        observacao: str = None,
        nota_entrada_id: int = None,
    ) -> int:
        """
        Registra uma movimentação de estoque e atualiza o saldo do produto.

        Args:
            tipo: entrada | saida | ajuste | venda | devolucao | nfe_entrada
        """
        with db_transaction() as (conn, cursor):
            # Buscar estoque atual
            cursor.execute(
                "SELECT estoque_atual FROM produtos WHERE id = %s",
                (produto_id,),
            )
            produto = cursor.fetchone()
            if not produto:
                raise ValueError(f"Produto #{produto_id} não encontrado.")

            estoque_anterior = float(produto["estoque_atual"])

            # Calcular novo estoque
            if tipo in ("entrada", "devolucao", "nfe_entrada", "ajuste"):
                estoque_posterior = estoque_anterior + quantidade
            elif tipo in ("saida", "venda"):
                estoque_posterior = estoque_anterior - quantidade
            else:
                estoque_posterior = quantidade  # ajuste absoluto

            # Atualizar estoque do produto
            cursor.execute(
                "UPDATE produtos SET estoque_atual = %s WHERE id = %s",
                (estoque_posterior, produto_id),
            )

            # Registrar movimentação
            cursor.execute(
                """
                INSERT INTO movimentacoes_estoque
                (produto_id, usuario_id, nota_entrada_id, tipo, quantidade,
                 estoque_anterior, estoque_posterior, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (produto_id, usuario_id, nota_entrada_id, tipo,
                 quantidade, estoque_anterior, estoque_posterior, observacao),
            )
            return cursor.lastrowid

    def get_history(
        self,
        produto_id: int = None,
        start_date: date = None,
        end_date: date = None,
        tipo: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Consulta histórico de movimentações com filtros."""
        query = """
            SELECT me.*, p.nome as produto_nome, p.codigo_interno,
                   u.nome as usuario_nome
            FROM movimentacoes_estoque me
            JOIN produtos p ON me.produto_id = p.id
            JOIN usuarios u ON me.usuario_id = u.id
        """
        conditions = []
        params = []

        if produto_id:
            conditions.append("me.produto_id = %s")
            params.append(produto_id)
        if start_date:
            conditions.append("DATE(me.criado_em) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(me.criado_em) <= %s")
            params.append(end_date)
        if tipo:
            conditions.append("me.tipo = %s")
            params.append(tipo)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY me.criado_em DESC LIMIT {int(limit)}"

        return execute_query(query, tuple(params) if params else None) or []
