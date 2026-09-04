"""DAO para operações fiscais (NFC-e)."""

from typing import Optional, Dict, List

from models.base_model import BaseModel
from database.connection import execute_query


class FiscalModel(BaseModel):
    """
    Operações no banco relacionadas a notas fiscais emitidas (NFC-e).
    A comunicação com a API Focus NFe fica no fiscal_service.py.
    """
    TABLE_NAME = "vendas"
    FIELDS = []  # Não tem tabela própria, opera sobre vendas

    def get_pending_nfce(self) -> List[Dict]:
        """Retorna vendas finalizadas sem NFC-e emitida (contingência)."""
        return execute_query(
            """
            SELECT v.*, u.nome as operador_nome
            FROM vendas v
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.status = 'contingencia'
            OR (v.status = 'finalizada' AND v.nfce_chave IS NULL)
            ORDER BY v.criado_em
            """,
        ) or []

    def update_nfce_data(
        self,
        venda_id: int,
        nfce_numero: str,
        nfce_chave: str,
        nfce_protocolo: str,
        nfce_pdf_url: str,
        nfce_status: str = "autorizada",
    ) -> int:
        """Atualiza dados da NFC-e após resposta da API fiscal."""
        from database.connection import execute_update
        return execute_update(
            """
            UPDATE vendas
            SET nfce_numero = %s, nfce_chave = %s, nfce_protocolo = %s,
                nfce_pdf_url = %s, nfce_status = %s,
                status = 'finalizada'
            WHERE id = %s
            """,
            (nfce_numero, nfce_chave, nfce_protocolo,
             nfce_pdf_url, nfce_status, venda_id),
        )

    def get_nfce_by_period(self, start_date, end_date) -> List[Dict]:
        """Lista NFC-e emitidas por período."""
        return execute_query(
            """
            SELECT v.id, v.nfce_numero, v.nfce_chave, v.nfce_status,
                   v.total, v.criado_em, u.nome as operador_nome
            FROM vendas v
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.nfce_chave IS NOT NULL
            AND DATE(v.criado_em) BETWEEN %s AND %s
            ORDER BY v.criado_em DESC
            """,
            (start_date, end_date),
        ) or []
