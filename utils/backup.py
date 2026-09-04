"""
Sistema de backup do banco de dados MySQL para o Sistema Meu Bazar.
"""

import os
import gzip
import logging
import subprocess
import threading
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

# Configurações padrão do banco (podem ser sobrescritas por variáveis de ambiente)
DB_HOST = os.environ.get('BAZAR_DB_HOST', 'localhost')
DB_PORT = os.environ.get('BAZAR_DB_PORT', '3306')
DB_USER = os.environ.get('BAZAR_DB_USER', 'root')
DB_PASSWORD = os.environ.get('BAZAR_DB_PASSWORD', '')
DB_NAME = os.environ.get('BAZAR_DB_NAME', 'meubazar')

# Diretório padrão de backups
BACKUP_DIR = os.path.join(os.path.expanduser('~'), 'meubazar_backups')


def _get_mysqldump_cmd() -> str:
    """Localiza o executável mysqldump."""
    # Caminhos comuns no macOS com XAMPP
    candidatos = [
        '/Applications/XAMPP/bin/mysqldump',
        '/Applications/XAMPP/xamppfiles/bin/mysqldump',
        '/usr/local/mysql/bin/mysqldump',
        '/usr/local/bin/mysqldump',
        'mysqldump',
    ]
    for cmd in candidatos:
        if os.path.isfile(cmd) or subprocess.run(
            ['which', cmd], capture_output=True
        ).returncode == 0:
            return cmd
    return 'mysqldump'


def _get_mysql_cmd() -> str:
    """Localiza o executável mysql."""
    candidatos = [
        '/Applications/XAMPP/bin/mysql',
        '/Applications/XAMPP/xamppfiles/bin/mysql',
        '/usr/local/mysql/bin/mysql',
        '/usr/local/bin/mysql',
        'mysql',
    ]
    for cmd in candidatos:
        if os.path.isfile(cmd) or subprocess.run(
            ['which', cmd], capture_output=True
        ).returncode == 0:
            return cmd
    return 'mysql'


def _build_dump_args(output_path: str) -> List[str]:
    """Monta os argumentos para o mysqldump."""
    mysqldump = _get_mysqldump_cmd()
    args = [
        mysqldump,
        f'--host={DB_HOST}',
        f'--port={DB_PORT}',
        f'--user={DB_USER}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--quick',
        '--lock-tables=false',
        DB_NAME,
    ]
    if DB_PASSWORD:
        args.insert(3, f'--password={DB_PASSWORD}')
    return args


def criar_backup(output_dir: str = BACKUP_DIR) -> str:
    """
    Cria um backup do banco de dados MySQL usando mysqldump.

    Args:
        output_dir: Diretório onde o backup será salvo.

    Returns:
        Caminho do arquivo de backup criado (.sql.gz).
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'meubazar_backup_{timestamp}.sql.gz'
    output_path = os.path.join(output_dir, filename)

    args = _build_dump_args(output_path)

    logger.info("Iniciando backup do banco '%s' para: %s", DB_NAME, output_path)

    try:
        with gzip.open(output_path, 'wb') as gz_file:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Escreve a saída comprimida diretamente
            while True:
                chunk = process.stdout.read(8192)
                if not chunk:
                    break
                gz_file.write(chunk)

            process.wait()
            stderr = process.stderr.read().decode('utf-8', errors='replace')

        if process.returncode != 0:
            logger.error("Erro no mysqldump (código %d): %s", process.returncode, stderr)
            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError(f"Falha no backup: {stderr}")

        tamanho = os.path.getsize(output_path)
        logger.info("Backup concluído: %s (%d bytes)", output_path, tamanho)
        return output_path

    except FileNotFoundError:
        logger.error("mysqldump não encontrado. Verifique se o MySQL está instalado.")
        raise
    except Exception as e:
        logger.error("Erro ao criar backup: %s", e)
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def restore_backup(backup_path: str) -> bool:
    """
    Restaura um backup do banco de dados MySQL.

    Args:
        backup_path: Caminho do arquivo .sql.gz de backup.

    Returns:
        True se a restauração foi bem-sucedida.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup não encontrado: {backup_path}")

    mysql_cmd = _get_mysql_cmd()
    args = [
        mysql_cmd,
        f'--host={DB_HOST}',
        f'--port={DB_PORT}',
        f'--user={DB_USER}',
        DB_NAME,
    ]
    if DB_PASSWORD:
        args.insert(3, f'--password={DB_PASSWORD}')

    logger.info("Iniciando restauração do backup: %s", backup_path)

    try:
        with gzip.open(backup_path, 'rb') as gz_file:
            process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            while True:
                chunk = gz_file.read(8192)
                if not chunk:
                    break
                process.stdin.write(chunk)
            process.stdin.close()
            process.wait()
            stderr = process.stderr.read().decode('utf-8', errors='replace')

        if process.returncode != 0:
            logger.error("Erro na restauração (código %d): %s", process.returncode, stderr)
            return False

        logger.info("Restauração concluída com sucesso: %s", backup_path)
        return True

    except Exception as e:
        logger.error("Erro ao restaurar backup: %s", e)
        return False


def listar_backups(output_dir: str = BACKUP_DIR) -> List[dict]:
    """
    Lista os backups disponíveis no diretório.

    Args:
        output_dir: Diretório onde procurar os backups.

    Returns:
        Lista de dicionários com informações dos backups:
        [{nome, caminho, tamanho, data_criacao}]
    """
    if not os.path.isdir(output_dir):
        return []

    backups = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.sql.gz'):
            filepath = os.path.join(output_dir, filename)
            stat = os.stat(filepath)
            backups.append({
                'nome': filename,
                'caminho': filepath,
                'tamanho': stat.st_size,
                'tamanho_formatado': _format_size(stat.st_size),
                'data_criacao': datetime.fromtimestamp(stat.st_mtime).strftime(
                    '%Y-%m-%d %H:%M:%S'
                ),
            })

    # Ordena do mais recente ao mais antigo
    backups.sort(key=lambda b: b['data_criacao'], reverse=True)
    return backups


def _format_size(size_bytes: int) -> str:
    """Formata tamanho em bytes para string legível."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.1f} TB'


def agendar_backup(output_dir: str = BACKUP_DIR, intervalo_horas: int = 24) -> threading.Timer:
    """
    Agenda backups automáticos periódicos.

    Args:
        output_dir: Diretório onde salvar os backups.
        intervalo_horas: Intervalo entre backups em horas.

    Returns:
        threading.Timer que pode ser cancelado com .cancel().
    """
    intervalo_segundos = intervalo_horas * 3600

    def _backup_periodico():
        try:
            criar_backup(output_dir)
        except Exception as e:
            logger.error("Erro no backup automático: %s", e)
        finally:
            # Reagenda
            agendar_backup(output_dir, intervalo_horas)

    timer = threading.Timer(intervalo_segundos, _backup_periodico)
    timer.daemon = True
    timer.name = 'BackupPeriodico'
    timer.start()

    logger.info(
        "Backup automático agendado a cada %d horas em: %s",
        intervalo_horas,
        output_dir,
    )
    return timer


def limpar_backups_antigos(
    output_dir: str = BACKUP_DIR,
    manter_ultimos: int = 7,
) -> int:
    """
    Remove backups antigos, mantendo apenas os N mais recentes.

    Args:
        output_dir: Diretório de backups.
        manter_ultinos: Quantidade de backups a manter.

    Returns:
        Número de backups removidos.
    """
    backups = listar_backups(output_dir)
    if len(backups) <= manter_ultimos:
        return 0

    removidos = 0
    for backup in backups[manter_ultimos:]:
        try:
            os.remove(backup['caminho'])
            removidos += 1
            logger.info("Backup antigo removido: %s", backup['nome'])
        except OSError as e:
            logger.warning("Erro ao remover %s: %s", backup['nome'], e)

    return removidos
