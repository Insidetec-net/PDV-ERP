"""DAO de Notas Fiscais de Entrada (NF-e de compra)."""

from typing import Optional, Dict, List

from models.base_model import BaseModel
from database.connection import execute_query


class NotaEntradaModel(BaseModel):
    TABLE_NAME = "notas_entrada"
    FIELDS = [
        "id", "chave_nfe", "numero_nfe", "serie",
        "fornecedor_cnpj", "fornecedor_nome", "data_emissao",
        "valor_total", "xml_path", "usuario_id",
        "importado_em", "observacao",
    ]

    def get_by_chave(self, chave_nfe: str) -> Optional[Dict]:
        """Busca nota de entrada pela chave de acesso."""
        return execute_query(
            "SELECT * FROM notas_entrada WHERE chave_nfe = %s",
            (chave_nfe,), fetch_one=True,
        )

    def get_with_items(self, nota_id: int) -> Optional[Dict]:
        """Retorna nota com seus itens."""
        nota = self.get_by_id(nota_id)
        if not nota:
            return None

        nota["itens"] = execute_query(
            """
            SELECT nei.*, p.nome as produto_nome_sistema,
                   p.codigo_interno
            FROM notas_entrada_itens nei
            LEFT JOIN produtos p ON nei.produto_id = p.id
            WHERE nei.nota_entrada_id = %s
            ORDER BY nei.numero_item
            """,
            (nota_id,),
        ) or []

        return nota

    def get_all_with_summary(self, limit: int = 100) -> List[Dict]:
        """Lista notas de entrada com resumo."""
        return execute_query(
            """
            SELECT ne.*, u.nome as usuario_nome,
                   COUNT(nei.id) as qtd_itens,
                   SUM(CASE WHEN nei.vinculado = TRUE THEN 1 ELSE 0 END) as itens_vinculados
            FROM notas_entrada ne
            JOIN usuarios u ON ne.usuario_id = u.id
            LEFT JOIN notas_entrada_itens nei ON ne.id = nei.nota_entrada_id
            GROUP BY ne.id
            ORDER BY ne.importado_em DESC
            LIMIT %s
            """,
            (limit,),
        ) or []


class NotaEntradaItemModel(BaseModel):
    TABLE_NAME = "notas_entrada_itens"
    FIELDS = [
        "id", "nota_entrada_id", "produto_id", "numero_item",
        "codigo_ean", "nome_produto_nfe", "ncm", "cfop",
        "unidade", "quantidade", "valor_unitario", "valor_total",
        "vinculado",
    ]

    def get_unlinked_items(self, nota_id: int) -> List[Dict]:
        """Retorna itens não vinculados a produtos do sistema."""
        return execute_query(
            """
            SELECT * FROM notas_entrada_itens
            WHERE nota_entrada_id = %s AND vinculado = FALSE
            ORDER BY numero_item
            """,
            (nota_id,),
        ) or []

    def link_to_product(self, item_id: int, produto_id: int) -> int:
        """Vincula um item da NF-e a um produto do sistema."""
        return self.update(item_id, {
            "produto_id": produto_id,
            "vinculado": True,
        })
