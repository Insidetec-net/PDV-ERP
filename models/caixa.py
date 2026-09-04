"""DAO de Turnos (Caixa) e Movimentações de Caixa."""

from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal

from models.base_model import BaseModel
from database.connection import execute_query, db_transaction


class CaixaModel(BaseModel):
    TABLE_NAME = "turnos"
    FIELDS = [
        "id", "usuario_id", "valor_abertura", "valor_fechamento",
        "total_vendas", "total_cancelamentos", "total_sangrias",
        "total_suprimentos", "diferenca", "qtd_vendas",
        "abertura", "fechamento", "status", "observacao",
    ]

    def open_shift(self, usuario_id: int, valor_abertura: float) -> int:
        """
        Abre um novo turno de caixa.

        Raises:
            ValueError se o operador já tiver um turno aberto.
        """
        # Verificar turno aberto
        existing = execute_query(
            "SELECT id FROM turnos WHERE usuario_id = %s AND status = 'aberto'",
            (usuario_id,), fetch_one=True,
        )
        if existing:
            raise ValueError(
                f"Operador já possui turno aberto (#{existing['id']})."
            )

        return self.insert({
            "usuario_id": usuario_id,
            "valor_abertura": valor_abertura,
            "status": "aberto",
        })

    def close_shift(
        self,
        turno_id: int,
        valor_fechamento: float,
        observacao: str = None,
    ) -> Dict:
        """
        Fecha um turno e calcula a diferença.

        Returns:
            Resumo do turno fechado.
        """
        turno = self.get_by_id(turno_id)
        if not turno or turno["status"] != "aberto":
            raise ValueError("Turno não encontrado ou já fechado.")

        # Calcular diferença - converter tudo para Decimal
        valor_abertura = Decimal(str(turno["valor_abertura"] or 0))
        total_vendas = Decimal(str(turno["total_vendas"] or 0))
        total_cancelamentos = Decimal(str(turno["total_cancelamentos"] or 0))
        total_sangrias = Decimal(str(turno["total_sangrias"] or 0))
        total_suprimentos = Decimal(str(turno["total_suprimentos"] or 0))
        
        valor_esperado = (
            valor_abertura
            + total_vendas
            - total_cancelamentos
            - total_sangrias
            + total_suprimentos
        )
        diferenca = Decimal(str(valor_fechamento)) - valor_esperado

        self.update(turno_id, {
            "valor_fechamento": float(valor_fechamento),
            "diferenca": float(diferenca),
            "fechamento": datetime.now(),
            "status": "fechado",
            "observacao": observacao,
        })

        return {
            "turno_id": turno_id,
            "valor_abertura": float(valor_abertura),
            "total_vendas": float(total_vendas),
            "total_cancelamentos": float(total_cancelamentos),
            "total_sangrias": float(total_sangrias),
            "total_suprimentos": float(total_suprimentos),
            "qtd_vendas": turno["qtd_vendas"],
            "valor_esperado": float(valor_esperado),
            "valor_fechamento": float(valor_fechamento),
            "diferenca": float(diferenca),
        }

    def get_open_shift(self, usuario_id: int) -> Optional[Dict]:
        """Retorna o turno aberto do operador (se houver)."""
        return execute_query(
            "SELECT * FROM turnos WHERE usuario_id = %s AND status = 'aberto'",
            (usuario_id,), fetch_one=True,
        )

    def register_cash_movement(
        self,
        turno_id: int,
        usuario_id: int,
        tipo: str,
        valor: float,
        motivo: str = None,
    ) -> int:
        """
        Registra uma sangria ou suprimento.

        Args:
            tipo: 'sangria' ou 'suprimento'
        """
        with db_transaction() as (conn, cursor):
            # Inserir movimentação
            cursor.execute(
                """
                INSERT INTO movimentacoes_caixa
                (turno_id, usuario_id, tipo, valor, motivo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (turno_id, usuario_id, tipo, valor, motivo),
            )
            mov_id = cursor.lastrowid

            # Atualizar total do turno
            campo = "total_sangrias" if tipo == "sangria" else "total_suprimentos"
            cursor.execute(
                f"UPDATE turnos SET {campo} = {campo} + %s WHERE id = %s",
                (valor, turno_id),
            )

            return mov_id

    def get_shift_movements(self, turno_id: int) -> List[Dict]:
        """Lista movimentações de caixa de um turno."""
        return execute_query(
            """
            SELECT mc.*, u.nome as usuario_nome
            FROM movimentacoes_caixa mc
            JOIN usuarios u ON mc.usuario_id = u.id
            WHERE mc.turno_id = %s
            ORDER BY mc.criado_em
            """,
            (turno_id,),
        )

    def get_total_vendas_dinheiro(self, turno_id: int) -> Decimal:
        """Calcula a soma real das vendas em dinheiro no turno atual."""
        result = execute_query(
            """
            SELECT SUM(pv.valor) as total
            FROM pagamentos_venda pv
            JOIN vendas v ON pv.venda_id = v.id
            WHERE v.turno_id = %s AND pv.forma = 'dinheiro' AND v.status = 'finalizada'
            """,
            (turno_id,)
        )
        if result and result[0]['total'] is not None:
            return Decimal(str(result[0]['total']))
        return Decimal('0')

    def get_total_vendas_outros(self, turno_id: int) -> Decimal:
        """Calcula a soma das vendas em cartão, pix e outros meios."""
        result = execute_query(
            """
            SELECT SUM(pv.valor) as total
            FROM pagamentos_venda pv
            JOIN vendas v ON pv.venda_id = v.id
            WHERE v.turno_id = %s AND pv.forma != 'dinheiro' AND v.status = 'finalizada'
            """,
            (turno_id,)
        )
        if result and result[0]['total'] is not None:
            return Decimal(str(result[0]['total']))
        return Decimal('0')
