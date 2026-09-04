"""
BaseModel — Classe base para todos os DAOs.
Fornece operações CRUD genéricas com prepared statements.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from database.connection import (
    execute_query,
    execute_insert,
    execute_update,
    execute_many,
    db_transaction,
)

logger = logging.getLogger(__name__)


class BaseModel:
    """
    Classe base para Data Access Objects (DAO).
    Subclasses devem definir:
        - TABLE_NAME: nome da tabela
        - FIELDS: lista de campos da tabela
    """

    TABLE_NAME: str = ""
    FIELDS: List[str] = []
    PK: str = "id"

    # --- CRUD Genérico ---

    def get_by_id(self, record_id: int) -> Optional[Dict]:
        """Busca um registro pelo ID."""
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE {self.PK} = %s"
        return execute_query(query, (record_id,), fetch_one=True)

    def get_all(
        self,
        where: str = None,
        params: tuple = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
    ) -> List[Dict]:
        """
        Busca registros com filtros opcionais.

        Args:
            where: Cláusula WHERE (sem a keyword WHERE).
            params: Parâmetros para o WHERE.
            order_by: Cláusula ORDER BY (sem a keyword).
            limit: Limite de registros.
            offset: Offset para paginação.
        """
        query = f"SELECT * FROM {self.TABLE_NAME}"
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {int(limit)}"
            if offset:
                query += f" OFFSET {int(offset)}"

        return execute_query(query, params) or []

    def count(self, where: str = None, params: tuple = None) -> int:
        """Conta registros com filtro opcional."""
        query = f"SELECT COUNT(*) as total FROM {self.TABLE_NAME}"
        if where:
            query += f" WHERE {where}"
        result = execute_query(query, params, fetch_one=True)
        return result["total"] if result else 0

    def insert(self, data: Dict[str, Any]) -> int:
        """
        Insere um registro e retorna o ID gerado.

        Args:
            data: Dicionário {campo: valor}.

        Returns:
            ID do registro inserido.
        """
        fields = [k for k in data.keys() if k in self.FIELDS or k not in [self.PK]]
        values = [data[k] for k in fields]
        placeholders = ", ".join(["%s"] * len(fields))
        field_names = ", ".join(fields)

        query = f"INSERT INTO {self.TABLE_NAME} ({field_names}) VALUES ({placeholders})"
        return execute_insert(query, tuple(values))

    def update(self, record_id: int, data: Dict[str, Any]) -> int:
        """
        Atualiza um registro pelo ID.

        Args:
            record_id: ID do registro.
            data: Dicionário {campo: valor} com os campos a atualizar.

        Returns:
            Número de linhas afetadas.
        """
        fields = [k for k in data.keys() if k != self.PK]
        values = [data[k] for k in fields]
        set_clause = ", ".join([f"{f} = %s" for f in fields])

        query = f"UPDATE {self.TABLE_NAME} SET {set_clause} WHERE {self.PK} = %s"
        values.append(record_id)
        return execute_update(query, tuple(values))

    def delete(self, record_id: int) -> int:
        """Deleta um registro pelo ID."""
        query = f"DELETE FROM {self.TABLE_NAME} WHERE {self.PK} = %s"
        return execute_update(query, (record_id,))

    def soft_delete(self, record_id: int) -> int:
        """Desativa um registro (soft delete) se tiver campo 'ativo'."""
        return self.update(record_id, {"ativo": False})

    def search(
        self,
        search_fields: List[str],
        term: str,
        active_only: bool = True,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Busca textual em múltiplos campos (LIKE %term%).

        Args:
            search_fields: Lista de campos para buscar.
            term: Termo de busca.
            active_only: Se True, filtra apenas registros ativos.
            limit: Limite de resultados.
        """
        conditions = " OR ".join([f"{f} LIKE %s" for f in search_fields])
        params = tuple([f"%{term}%"] * len(search_fields))

        where = f"({conditions})"
        if active_only and "ativo" in self.FIELDS:
            where += " AND ativo = TRUE"

        return self.get_all(where=where, params=params, limit=limit)

    def exists(self, where: str, params: tuple = None) -> bool:
        """Verifica se um registro existe."""
        return self.count(where=where, params=params) > 0

    def insert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Insere múltiplos registros em lote."""
        if not data_list:
            return 0

        fields = [k for k in data_list[0].keys() if k != self.PK]
        field_names = ", ".join(fields)
        placeholders = ", ".join(["%s"] * len(fields))
        query = f"INSERT INTO {self.TABLE_NAME} ({field_names}) VALUES ({placeholders})"

        params_list = [tuple(d[k] for k in fields) for d in data_list]
        return execute_many(query, params_list)
