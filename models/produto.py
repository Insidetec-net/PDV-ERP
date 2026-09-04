"""DAO de Produtos."""

from typing import Optional, Dict, List
from decimal import Decimal

from models.base_model import BaseModel
from database.connection import execute_query, execute_update


class ProdutoModel(BaseModel):
    TABLE_NAME = "produtos"
    FIELDS = [
        "id", "codigo_barras", "codigo_interno", "nome", "descricao",
        "categoria_id", "preco_custo", "preco_venda", "margem_lucro",
        "ncm", "cst_icms", "cst_pis", "cst_cofins", "aliquota_icms",
        "cfop", "unidade", "estoque_atual", "estoque_minimo",
        "ativo", "criado_em", "atualizado_em",
    ]

    def get_by_codigo_barras(self, codigo: str) -> Optional[Dict]:
        """Busca produto pelo código de barras (EAN)."""
        query = "SELECT * FROM produtos WHERE codigo_barras = %s AND ativo = TRUE"
        return execute_query(query, (codigo,), fetch_one=True)

    def get_by_codigo_interno(self, codigo: str) -> Optional[Dict]:
        """Busca produto pelo código interno (MB-XXXXXX)."""
        query = "SELECT * FROM produtos WHERE codigo_interno = %s AND ativo = TRUE"
        return execute_query(query, (codigo,), fetch_one=True)

    def get_by_any_code(self, codigo: str) -> Optional[Dict]:
        """
        Busca produto por qualquer código (barras ou interno).
        Usado no PDV para leitura rápida pelo scanner.
        """
        query = """
            SELECT * FROM produtos
            WHERE (codigo_barras = %s OR codigo_interno = %s)
            AND ativo = TRUE
        """
        return execute_query(query, (codigo, codigo), fetch_one=True)

    def search_products(self, term: str, limit: int = 50) -> List[Dict]:
        """
        Busca produtos por nome, código de barras ou código interno.
        """
        query = f"""
            SELECT p.*, c.nome as categoria_nome
            FROM produtos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE (
                p.nome LIKE %s
                OR p.codigo_barras LIKE %s
                OR p.codigo_interno LIKE %s
            )
            AND p.ativo = 1
            ORDER BY p.nome
            LIMIT {int(limit)}
        """
        like_term = f"%{term}%"
        return execute_query(query, (like_term, like_term, like_term)) or []

    def get_products_with_category(
        self,
        active_only: bool = True,
        category_id: int = None,
        order_by: str = "p.nome",
        limit: int = None,
        offset: int = None,
    ) -> List[Dict]:
        """Lista produtos com nome da categoria (JOIN)."""
        query = """
            SELECT p.*, c.nome as categoria_nome
            FROM produtos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
        """
        conditions = []
        params = []

        if active_only:
            conditions.append("p.ativo = TRUE")
        if category_id:
            conditions.append("p.categoria_id = %s")
            params.append(category_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {int(limit)}"
            if offset:
                query += f" OFFSET {int(offset)}"

        return execute_query(query, tuple(params) if params else None) or []

    def get_low_stock(self) -> List[Dict]:
        """Retorna produtos com estoque abaixo do mínimo."""
        query = """
            SELECT p.*, c.nome as categoria_nome
            FROM produtos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.estoque_atual <= p.estoque_minimo
            AND p.ativo = TRUE
            ORDER BY (p.estoque_atual - p.estoque_minimo) ASC
        """
        return execute_query(query) or []

    def update_stock(self, product_id: int, new_stock: Decimal) -> int:
        """Atualiza o estoque de um produto."""
        return self.update(product_id, {"estoque_atual": float(new_stock)})

    def calculate_sale_price(
        self, cost: float, markup_percent: float
    ) -> Dict[str, float]:
        """
        Calcula preço de venda e margem a partir do custo e markup.

        Args:
            cost: Preço de custo.
            markup_percent: Percentual de markup (ex: 100 = dobrar o preço).

        Returns:
            Dict com preco_venda, margem_lucro, lucro_bruto.
        """
        sale_price = cost * (1 + markup_percent / 100)
        gross_profit = sale_price - cost
        margin = (gross_profit / sale_price * 100) if sale_price > 0 else 0

        return {
            "preco_venda": round(sale_price, 2),
            "margem_lucro": round(margin, 2),
            "lucro_bruto": round(gross_profit, 2),
        }

    def generate_next_internal_code(self) -> str:
        """
        Gera o próximo código interno (MB-XXXXXX).
        Lê e incrementa o contador na tabela configuracoes.
        """
        from models.configuracao import ConfiguracaoModel
        config = ConfiguracaoModel()

        counter = int(config.get_value("sistema_codigo_interno_contador") or "0")
        counter += 1
        config.set_value("sistema_codigo_interno_contador", str(counter))

        return f"MB-{counter:06d}"
