"""DAO de Usuários."""

import bcrypt
from typing import Optional, Dict

from models.base_model import BaseModel
from database.connection import execute_query


class UsuarioModel(BaseModel):
    TABLE_NAME = "usuarios"
    FIELDS = [
        "id", "nome", "login", "senha_hash", "perfil",
        "ativo", "criado_em", "atualizado_em",
    ]

    def get_by_login(self, login: str) -> Optional[Dict]:
        """Busca usuário pelo login."""
        query = "SELECT * FROM usuarios WHERE login = %s AND ativo = TRUE"
        return execute_query(query, (login,), fetch_one=True)

    def authenticate(self, login: str, senha: str) -> Optional[Dict]:
        """
        Autentica um usuário (login + senha).

        Returns:
            Dados do usuário se autenticado, None caso contrário.
        """
        user = self.get_by_login(login)
        if not user:
            return None

        # Verificar senha com bcrypt
        if bcrypt.checkpw(
            senha.encode("utf-8"),
            user["senha_hash"].encode("utf-8"),
        ):
            # Remover hash da resposta por segurança
            user_safe = {k: v for k, v in user.items() if k != "senha_hash"}
            return user_safe

        return None

    def create_user(
        self,
        nome: str,
        login: str,
        senha: str,
        perfil: str = "operador",
    ) -> int:
        """
        Cria um novo usuário com senha hasheada.

        Returns:
            ID do usuário criado.
        """
        # Gerar hash bcrypt
        senha_hash = bcrypt.hashpw(
            senha.encode("utf-8"),
            bcrypt.gensalt(rounds=12),
        ).decode("utf-8")

        return self.insert({
            "nome": nome,
            "login": login,
            "senha_hash": senha_hash,
            "perfil": perfil,
            "ativo": True,
        })

    def change_password(self, user_id: int, nova_senha: str) -> int:
        """Altera a senha de um usuário."""
        senha_hash = bcrypt.hashpw(
            nova_senha.encode("utf-8"),
            bcrypt.gensalt(rounds=12),
        ).decode("utf-8")

        return self.update(user_id, {"senha_hash": senha_hash})

    def get_active_users(self, perfil: str = None):
        """Lista usuários ativos, opcionalmente filtrando por perfil."""
        where = "ativo = TRUE"
        params = ()
        if perfil:
            where += " AND perfil = %s"
            params = (perfil,)
        return self.get_all(where=where, params=params, order_by="nome")
