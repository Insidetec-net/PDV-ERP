"""DAO de Clientes."""

from models.base_model import BaseModel


class ClienteModel(BaseModel):
    TABLE_NAME = "clientes"
    FIELDS = [
        "id", "nome", "cpf_cnpj", "telefone", "email",
        "endereco", "cidade", "uf", "cep", "observacao",
        "ativo", "criado_em", "atualizado_em",
    ]

    def search_clients(self, term: str, limit: int = 50):
        """Busca clientes por nome, CPF/CNPJ, telefone ou email."""
        return self.search(
            search_fields=["nome", "cpf_cnpj", "telefone", "email"],
            term=term,
            limit=limit,
        )

    def get_by_cpf_cnpj(self, cpf_cnpj: str):
        """Busca cliente por CPF ou CNPJ."""
        from database.connection import execute_query
        return execute_query(
            "SELECT * FROM clientes WHERE cpf_cnpj = %s AND ativo = TRUE",
            (cpf_cnpj,), fetch_one=True,
        )
