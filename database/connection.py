"""
Pool de conexões MySQL para o Sistema Meu Bazar.
Gerencia conexões com retry e tratamento de erros.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

import mysql.connector
from mysql.connector import pooling, Error as MySQLError

from config.settings import DB_CONFIG

logger = logging.getLogger(__name__)

# Pool global
_pool: Optional[pooling.MySQLConnectionPool] = None


def get_pool() -> pooling.MySQLConnectionPool:
    """
    Retorna o pool de conexões (singleton).
    Cria o pool na primeira chamada.
    """
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(**DB_CONFIG)
            logger.info("Pool de conexões MySQL criado com sucesso.")
        except MySQLError as e:
            logger.error(f"Erro ao criar pool de conexões: {e}")
            raise
    return _pool


def get_connection(retries: int = 3, delay: float = 1.0):
    """
    Obtém uma conexão do pool com retry.

    Args:
        retries: Número de tentativas em caso de falha.
        delay: Tempo de espera entre tentativas (segundos).

    Returns:
        MySQLConnection ativa.

    Raises:
        MySQLError se todas as tentativas falharem.
    """
    pool = get_pool()
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            conn = pool.get_connection()
            if conn.is_connected():
                return conn
        except MySQLError as e:
            last_error = e
            logger.warning(
                f"Tentativa {attempt}/{retries} de conexão falhou: {e}"
            )
            if attempt < retries:
                time.sleep(delay)

    logger.error(f"Falha ao obter conexão após {retries} tentativas.")
    raise last_error


@contextmanager
def db_connection():
    """
    Context manager para obter e devolver uma conexão do pool.

    Uso:
        with db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM produtos")
            rows = cursor.fetchall()
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
    except MySQLError as e:
        logger.error(f"Erro na conexão MySQL: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()


@contextmanager
def db_transaction():
    """
    Context manager para transações com commit/rollback automático.

    Uso:
        with db_transaction() as (conn, cursor):
            cursor.execute("INSERT INTO ...", (...))
            cursor.execute("UPDATE ...", (...))
            # commit automático ao sair do with
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)
        yield conn, cursor
        conn.commit()
    except Exception as e:
        if conn and conn.is_connected():
            conn.rollback()
            logger.error(f"Transação revertida: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def execute_query(
    query: str,
    params: tuple = None,
    fetch_one: bool = False,
    fetch_all: bool = True,
    dictionary: bool = True,
):
    """
    Executa uma query SELECT e retorna os resultados.

    Args:
        query: SQL query string.
        params: Parâmetros para prepared statement.
        fetch_one: Se True, retorna apenas o primeiro resultado.
        fetch_all: Se True, retorna todos os resultados.
        dictionary: Se True, retorna dicts ao invés de tuples.

    Returns:
        Lista de dicts, um dict, ou None.
    """
    with db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            cursor.execute(query, params)
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            return None
        finally:
            cursor.close()


def execute_insert(query: str, params: tuple = None) -> int:
    """
    Executa um INSERT e retorna o lastrowid.
    """
    with db_transaction() as (conn, cursor):
        cursor.execute(query, params)
        return cursor.lastrowid


def execute_update(query: str, params: tuple = None) -> int:
    """
    Executa um UPDATE/DELETE e retorna o número de linhas afetadas.
    """
    with db_transaction() as (conn, cursor):
        cursor.execute(query, params)
        return cursor.rowcount


def execute_many(query: str, params_list: list) -> int:
    """
    Executa um INSERT/UPDATE em lote (batch).
    """
    with db_transaction() as (conn, cursor):
        cursor.executemany(query, params_list)
        return cursor.rowcount


def test_connection() -> bool:
    """
    Testa se a conexão com o MySQL está funcionando.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            logger.info("Conexão com MySQL testada com sucesso.")
            return True
    except MySQLError as e:
        logger.error(f"Falha ao testar conexão: {e}")
        return False


def close_pool():
    """Fecha todas as conexões do pool."""
    global _pool
    if _pool:
        # MySQLConnectionPool não tem close(), mas podemos resetar
        _pool = None
        logger.info("Pool de conexões encerrado.")
