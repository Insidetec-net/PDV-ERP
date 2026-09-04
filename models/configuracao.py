"""DAO de Configurações (white-label)."""

from typing import Optional, Dict, List

from models.base_model import BaseModel
from database.connection import execute_query, execute_update


class ConfiguracaoModel(BaseModel):
    TABLE_NAME = "configuracoes"
    FIELDS = ["id", "chave", "valor", "grupo", "descricao", "atualizado_em"]

    def get_value(self, chave: str) -> Optional[str]:
        """Retorna o valor de uma configuração pela chave."""
        result = execute_query(
            "SELECT valor FROM configuracoes WHERE chave = %s",
            (chave,), fetch_one=True,
        )
        return result["valor"] if result else None

    def set_value(self, chave: str, valor: str) -> int:
        """Define o valor de uma configuração existente."""
        return execute_update(
            "UPDATE configuracoes SET valor = %s WHERE chave = %s",
            (valor, chave),
        )

    def get_by_group(self, grupo: str) -> List[Dict]:
        """Retorna todas as configurações de um grupo."""
        return execute_query(
            "SELECT * FROM configuracoes WHERE grupo = %s ORDER BY chave",
            (grupo,),
        ) or []

    def get_all_as_dict(self) -> Dict[str, str]:
        """Retorna todas as configurações como dicionário {chave: valor}."""
        rows = execute_query("SELECT chave, valor FROM configuracoes")
        return {row["chave"]: row["valor"] for row in rows} if rows else {}

    def get_empresa_data(self) -> Dict[str, str]:
        """Retorna dados da empresa como dicionário."""
        rows = self.get_by_group("empresa")
        return {row["chave"]: row["valor"] for row in rows} if rows else {}

    def get_fiscal_data(self) -> Dict[str, str]:
        """Retorna configurações fiscais como dicionário."""
        rows = self.get_by_group("fiscal")
        return {row["chave"]: row["valor"] for row in rows} if rows else {}

    def update_batch(self, configs: Dict[str, str]):
        """Atualiza múltiplas configurações de uma vez."""
        for chave, valor in configs.items():
            self.set_value(chave, valor)
