"""
Setup do banco de dados — Primeiro uso.
Cria o banco, executa o schema e insere os dados iniciais.
"""

import sys
import os
import logging
from pathlib import Path
from getpass import getpass

import mysql.connector
from mysql.connector import Error as MySQLError

from config.settings import DB_CONFIG, save_local_config

logger = logging.getLogger(__name__)

# Diretório deste arquivo
_DIR = Path(__file__).resolve().parent


def _read_sql_file(filename: str) -> str:
    """Lê um arquivo SQL do diretório database/."""
    filepath = _DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def _connect_without_db(host: str, port: int, user: str, password: str):
    """Conecta ao MySQL sem selecionar banco de dados."""
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


def _execute_sql_script(conn, sql_script: str):
    """
    Executa um script SQL que pode conter múltiplas statements.
    """
    cursor = conn.cursor()
    try:
        # Dividir por ponto-e-vírgula respeitando statements completas
        statements = []
        current = []
        for line in sql_script.split("\n"):
            stripped = line.strip()
            # Ignorar comentários e linhas vazias
            if stripped.startswith("--") or stripped == "":
                continue
            current.append(line)
            if stripped.endswith(";"):
                stmt = "\n".join(current).strip()
                if stmt and stmt != ";":
                    statements.append(stmt)
                current = []

        for stmt in statements:
            try:
                cursor.execute(stmt)
                conn.commit()
            except MySQLError as e:
                # Ignorar erros de "já existe"
                if e.errno in (1007, 1050, 1061, 1062):
                    logger.debug(f"Ignorado (já existe): {e.msg}")
                else:
                    logger.warning(f"Erro ao executar SQL: {e.msg}")
                    logger.debug(f"Statement: {stmt[:200]}...")
    finally:
        cursor.close()


def check_mysql_available(host: str, port: int, user: str, password: str) -> bool:
    """Verifica se o MySQL está disponível e acessível."""
    try:
        conn = _connect_without_db(host, port, user, password)
        conn.close()
        return True
    except MySQLError:
        return False


def setup_database(
    host: str = None,
    port: int = None,
    user: str = None,
    password: str = None,
    interactive: bool = True,
):
    """
    Configura o banco de dados: cria schema e insere dados iniciais.

    Args:
        host: Host do MySQL (default: config).
        port: Porta do MySQL (default: config).
        user: Usuário do MySQL (default: config).
        password: Senha do MySQL (default: config).
        interactive: Se True, solicita dados via input().
    """
    # Usar valores padrão do config se não fornecidos
    host = host or DB_CONFIG["host"]
    port = port or DB_CONFIG["port"]
    user = user or DB_CONFIG["user"]
    password = password if password is not None else DB_CONFIG["password"]

    if interactive:
        print("\n" + "=" * 60)
        print("  🏪 Sistema Meu Bazar — Configuração Inicial")
        print("=" * 60)
        print()
        print("Este assistente irá configurar o banco de dados MySQL.")
        print("Certifique-se de que o MySQL está rodando.\n")

        host_input = input(f"  Host MySQL [{host}]: ").strip()
        if host_input:
            host = host_input

        port_input = input(f"  Porta MySQL [{port}]: ").strip()
        if port_input:
            port = int(port_input)

        user_input = input(f"  Usuário MySQL [{user}]: ").strip()
        if user_input:
            user = user_input

        password = getpass(f"  Senha MySQL (vazio = sem senha): ")

    # Testar conexão
    print(f"\n  Conectando a {host}:{port} como '{user}'...")

    if not check_mysql_available(host, port, user, password):
        msg = "❌ Não foi possível conectar ao MySQL! Verifique se o serviço (XAMPP) está rodando."
        print(msg)
        if not interactive:
            raise RuntimeError(msg)
        sys.exit(1)

    print("  ✅ MySQL conectado com sucesso!")

    # Executar schema
    print("\n  📦 Criando banco de dados e tabelas...")
    conn = _connect_without_db(host, port, user, password)
    try:
        schema_sql = _read_sql_file("schema.sql")
        _execute_sql_script(conn, schema_sql)
        print("  ✅ Schema criado com sucesso (13 tabelas)!")

        # Executar seeds
        print("  🌱 Inserindo dados iniciais...")
        seeds_sql = _read_sql_file("seeds.sql")
        _execute_sql_script(conn, seeds_sql)
        print("  ✅ Dados iniciais inseridos!")

    finally:
        conn.close()

    # Salvar configuração local
    db_local = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": DB_CONFIG["database"],
    }
    save_local_config(db_config=db_local)

    print("\n  💾 Configuração salva em config.json")
    print()
    print("=" * 60)
    print("  ✅ Setup concluído com sucesso!")
    print("  ")
    print("  Login padrão:")
    print("    Usuário: admin")
    print("    Senha:   admin123")
    print("  ")
    print("  ⚠️  Troque a senha no primeiro acesso!")
    print("=" * 60)
    print()


# Permitir execução direta: python -m database.setup
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_database(interactive=True)
