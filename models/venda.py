"""DAO de Vendas."""

from typing import Optional, Dict, List
from datetime import datetime, date

from models.base_model import BaseModel
from database.connection import execute_query, db_transaction


class VendaModel(BaseModel):
    TABLE_NAME = "vendas"
    FIELDS = [
        "id", "turno_id", "cliente_id", "usuario_id",
        "subtotal", "desconto", "total", "valor_recebido", "troco",
        "status", "nfce_numero", "nfce_chave", "nfce_protocolo",
        "nfce_pdf_url", "nfce_status", "criado_em",
    ]

    def create_sale(
        self,
        turno_id: int,
        usuario_id: int,
        items: List[Dict],
        payments: List[Dict],
        cliente_id: int = None,
        desconto: float = 0.0,
    ) -> int:
        """
        Cria uma venda completa (venda + itens + pagamentos) em transação.

        Args:
            turno_id: ID do turno aberto.
            usuario_id: ID do operador.
            items: Lista de dicts {produto_id, quantidade, preco_unitario, desconto_item}.
            payments: Lista de dicts {forma, valor, bandeira, nsu, parcelas}.
            cliente_id: ID do cliente (opcional).
            desconto: Desconto total da venda.

        Returns:
            ID da venda criada.
        """
        # Calcular totais - converter para Decimal para evitar erros
        subtotal = sum(
            Decimal(str(item["quantidade"])) * Decimal(str(item["preco_unitario"])) - Decimal(str(item.get("desconto_item", 0)))
            for item in items
        )
        total = subtotal - Decimal(str(desconto))
        valor_recebido = sum(Decimal(str(p["valor"])) for p in payments)
        troco = max(Decimal('0'), valor_recebido - total)

        with db_transaction() as (conn, cursor):
            # 1. Inserir venda
            cursor.execute(
                """
                INSERT INTO vendas
                (turno_id, cliente_id, usuario_id, subtotal, desconto, total,
                 valor_recebido, troco, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'finalizada')
                """,
                (turno_id, cliente_id, usuario_id, float(subtotal), float(desconto),
                 float(total), float(valor_recebido), float(troco)),
            )
            venda_id = cursor.lastrowid

            # 2. Inserir itens
            for item in items:
                item_subtotal = (
                    Decimal(str(item["quantidade"])) * Decimal(str(item["preco_unitario"]))
                    - Decimal(str(item.get("desconto_item", 0)))
                )
                cursor.execute(
                    """
                    INSERT INTO venda_itens
                    (venda_id, produto_id, quantidade, preco_unitario,
                     desconto_item, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (venda_id, item["produto_id"], item["quantidade"],
                     item["preco_unitario"], item.get("desconto_item", 0),
                     float(item_subtotal)),
                )

                # 3. Baixar estoque
                cursor.execute(
                    """
                    UPDATE produtos
                    SET estoque_atual = estoque_atual - %s
                    WHERE id = %s
                    """,
                    (item["quantidade"], item["produto_id"]),
                )

                # 4. Registrar movimentação de estoque
                cursor.execute(
                    "SELECT estoque_atual FROM produtos WHERE id = %s",
                    (item["produto_id"],),
                )
                produto = cursor.fetchone()
                estoque_posterior = produto["estoque_atual"] if produto else 0

                cursor.execute(
                    """
                    INSERT INTO movimentacoes_estoque
                    (produto_id, usuario_id, tipo, quantidade,
                     estoque_anterior, estoque_posterior, observacao)
                    VALUES (%s, %s, 'venda', %s, %s, %s, %s)
                    """,
                    (item["produto_id"], usuario_id, item["quantidade"],
                     estoque_posterior + item["quantidade"],
                     estoque_posterior, f"Venda #{venda_id}"),
                )

            # 5. Inserir pagamentos
            for payment in payments:
                cursor.execute(
                    """
                    INSERT INTO pagamentos_venda
                    (venda_id, forma, valor, bandeira, nsu, parcelas)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (venda_id, payment["forma"], payment["valor"],
                     payment.get("bandeira"), payment.get("nsu"),
                     payment.get("parcelas", 1)),
                )

            # 6. Atualizar totais do turno
            cursor.execute(
                """
                UPDATE turnos
                SET total_vendas = total_vendas + %s,
                    qtd_vendas = qtd_vendas + 1
                WHERE id = %s
                """,
                (total, turno_id),
            )

        return venda_id

    def get_sale_details(self, venda_id: int) -> Optional[Dict]:
        """Retorna venda completa com itens e pagamentos."""
        # Venda
        venda = execute_query(
            """
            SELECT v.*, u.nome as operador_nome, c.nome as cliente_nome
            FROM vendas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = %s
            """,
            (venda_id,), fetch_one=True,
        )
        if not venda:
            return None

        # Itens
        venda["itens"] = execute_query(
            """
            SELECT vi.*, p.nome as produto_nome, p.codigo_barras,
                   p.codigo_interno
            FROM venda_itens vi
            JOIN produtos p ON vi.produto_id = p.id
            WHERE vi.venda_id = %s
            """,
            (venda_id,),
        ) or []

        # Pagamentos
        venda["pagamentos"] = execute_query(
            "SELECT * FROM pagamentos_venda WHERE venda_id = %s",
            (venda_id,),
        ) or []

        return venda

    def get_sales_by_period(
        self,
        start_date: date,
        end_date: date,
        status: str = None,
    ) -> List[Dict]:
        """Lista vendas por período."""
        query = """
            SELECT v.*, u.nome as operador_nome
            FROM vendas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE DATE(v.criado_em) BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if status:
            query += " AND v.status = %s"
            params.append(status)

        query += " ORDER BY v.criado_em DESC"

        return execute_query(query, tuple(params)) or []

    def cancel_sale(self, venda_id: int, usuario_id: int) -> bool:
        """
        Cancela uma venda e reverte o estoque.
        """
        with db_transaction() as (conn, cursor):
            # Verificar se a venda existe e está finalizada
            cursor.execute(
                "SELECT * FROM vendas WHERE id = %s AND status = 'finalizada'",
                (venda_id,),
            )
            venda = cursor.fetchone()
            if not venda:
                return False

            # Buscar itens para reverter estoque
            cursor.execute(
                "SELECT * FROM venda_itens WHERE venda_id = %s",
                (venda_id,),
            )
            itens = cursor.fetchall()

            for item in itens:
                # Devolver estoque
                cursor.execute(
                    """
                    UPDATE produtos
                    SET estoque_atual = estoque_atual + %s
                    WHERE id = %s
                    """,
                    (item["quantidade"], item["produto_id"]),
                )

                # Registrar movimentação de devolução
                cursor.execute(
                    "SELECT estoque_atual FROM produtos WHERE id = %s",
                    (item["produto_id"],),
                )
                produto = cursor.fetchone()
                estoque_posterior = produto["estoque_atual"] if produto else 0

                cursor.execute(
                    """
                    INSERT INTO movimentacoes_estoque
                    (produto_id, usuario_id, tipo, quantidade,
                     estoque_anterior, estoque_posterior, observacao)
                    VALUES (%s, %s, 'devolucao', %s, %s, %s, %s)
                    """,
                    (item["produto_id"], usuario_id, item["quantidade"],
                     estoque_posterior - item["quantidade"],
                     estoque_posterior, f"Cancelamento venda #{venda_id}"),
                )

            # Atualizar status da venda
            cursor.execute(
                "UPDATE vendas SET status = 'cancelada' WHERE id = %s",
                (venda_id,),
            )

            # Reverter total do turno
            cursor.execute(
                """
                UPDATE turnos
                SET total_vendas = total_vendas - %s,
                    total_cancelamentos = total_cancelamentos + %s,
                    qtd_vendas = qtd_vendas - 1
                WHERE id = %s
                """,
                (venda["total"], venda["total"], venda["turno_id"]),
            )

        return True
