"""
Serviço de Caixa - Lógica de negócio para operações de caixa.
Camada entre Models e UI, contendo validações e regras de negócio.
"""

import logging
from typing import Optional, Dict, List
from decimal import Decimal

from models.caixa import CaixaModel
from database.connection import execute_query

logger = logging.getLogger(__name__)


class CaixaService:
    """
    Serviço responsável pela lógica de operações de caixa:
    abertura, fechamento, sangrias, suprimentos e validações.
    """

    def __init__(self):
        self.model = CaixaModel()

    def abrir_caixa(self, usuario_id: int, valor_abertura: float) -> int:
        """
        Abre um novo turno de caixa.

        Args:
            usuario_id: ID do operador que está abrindo o caixa.
            valor_abertura: Valor inicial em dinheiro no caixa.

        Returns:
            ID do turno aberto.

        Raises:
            ValueError: Se valor_abertura < 0 ou se já houver turno aberto.
        """
        if valor_abertura < 0:
            raise ValueError("Valor de abertura não pode ser negativo.")

        turno_id = self.model.open_shift(usuario_id, valor_abertura)
        logger.info(
            f"Caixa aberto: turno #{turno_id}, operador #{usuario_id}, "
            f"valor R$ {valor_abertura:.2f}"
        )
        return turno_id

    def fechar_caixa(
        self, turno_id: int, valor_fechamento: float, observacao: str = None
    ) -> dict:
        """
        Fecha um turno de caixa e retorna resumo com diferença.

        Args:
            turno_id: ID do turno a ser fechado.
            valor_fechamento: Valor contado no fechamento.
            observacao: Observação opcional sobre o fechamento.

        Returns:
            Dicionário com resumo do turno e diferença calculada.

        Raises:
            ValueError: Se turno não encontrado ou já fechado.
        """
        resumo = self.model.close_shift(turno_id, valor_fechamento, observacao)
        logger.info(
            f"Caixa fechado: turno #{turno_id}, "
            f"valor informado R$ {valor_fechamento:.2f}, "
            f"diferença R$ {resumo['diferenca']:.2f}"
        )
        return resumo

    def sangria(
        self, turno_id: int, usuario_id: int, valor: float, motivo: str
    ) -> int:
        """
        Registra uma saída de dinheiro do caixa (sangria).

        Args:
            turno_id: ID do turno ativo.
            usuario_id: ID do operador realizando a sangria.
            valor: Valor a ser retirado (deve ser > 0).
            motivo: Motivo da sangria (não pode ser vazio).

        Returns:
            ID da movimentação registrada.

        Raises:
            ValueError: Se valor <= 0 ou motivo vazio.
        """
        if valor <= 0:
            raise ValueError("Valor da sangria deve ser maior que zero.")
        if not motivo or not motivo.strip():
            raise ValueError("Motivo da sangria é obrigatório.")

        mov_id = self.model.register_cash_movement(
            turno_id, usuario_id, "sangria", valor, motivo.strip()
        )
        logger.info(
            f"Sangria registrada: mov #{mov_id}, turno #{turno_id}, "
            f"valor R$ {valor:.2f}, motivo: {motivo}"
        )
        return mov_id

    def suprimento(
        self, turno_id: int, usuario_id: int, valor: float, motivo: str
    ) -> int:
        """
        Registra uma entrada de dinheiro no caixa (suprimento).

        Args:
            turno_id: ID do turno ativo.
            usuario_id: ID do operador realizando o suprimento.
            valor: Valor a ser adicionado (deve ser > 0).
            motivo: Motivo do suprimento (não pode ser vazio).

        Returns:
            ID da movimentação registrada.

        Raises:
            ValueError: Se valor <= 0 ou motivo vazio.
        """
        if valor <= 0:
            raise ValueError("Valor do suprimento deve ser maior que zero.")
        if not motivo or not motivo.strip():
            raise ValueError("Motivo do suprimento é obrigatório.")

        mov_id = self.model.register_cash_movement(
            turno_id, usuario_id, "suprimento", valor, motivo.strip()
        )
        logger.info(
            f"Suprimento registrado: mov #{mov_id}, turno #{turno_id}, "
            f"valor R$ {valor:.2f}, motivo: {motivo}"
        )
        return mov_id

    def get_saldo_turno(self, turno_id: int) -> Decimal:
        """
        Calcula o saldo atual do turno.

        Fórmula: abertura + vendas_dinheiro - sangrias + suprimentos

        Args:
            turno_id: ID do turno.

        Returns:
            Saldo calculado do turno.
        """
        turno = self.model.get_by_id(turno_id)
        if not turno:
            raise ValueError(f"Turno #{turno_id} não encontrado.")

        valor_abertura = Decimal(str(turno["valor_abertura"] or 0))
        total_sangrias = Decimal(str(turno["total_sangrias"] or 0))
        total_suprimentos = Decimal(str(turno["total_suprimentos"] or 0))

        # Obtém vendas em dinheiro diretamente do banco
        vendas_dinheiro = self.model.get_total_vendas_dinheiro(turno_id)

        saldo = valor_abertura + vendas_dinheiro - total_sangrias + total_suprimentos
        return saldo

    def get_movimentacoes(self, turno_id: int) -> list:
        """
        Retorna todas as movimentações de um turno.

        Args:
            turno_id: ID do turno.

        Returns:
            Lista de movimentações (sangrias e suprimentos).
        """
        return self.model.get_shift_movements(turno_id)

    def validar_fechamento(self, turno_id: int) -> dict:
        """
        Valida se o turno pode ser fechado.

        Verifica:
        - Turno existe e está aberto
        - Não há vendas em aberto (status diferente de 'finalizada' ou 'cancelada')

        Args:
            turno_id: ID do turno a validar.

        Returns:
            Dicionário com:
                - pode_fechar: bool indicando se pode fechar
                - alertas: lista de mensagens de alerta
        """
        alertas = []

        turno = self.model.get_by_id(turno_id)
        if not turno:
            return {
                "pode_fechar": False,
                "alertas": [f"Turno #{turno_id} não encontrado."],
            }

        if turno["status"] != "aberto":
            alertas.append(f"Turno já está com status '{turno['status']}'.")

        # Verifica vendas em aberto
        vendas_abertas = execute_query(
            """
            SELECT COUNT(*) as total FROM vendas
            WHERE turno_id = %s AND status NOT IN ('finalizada', 'cancelada')
            """,
            (turno_id,),
            fetch_one=True,
        )

        if vendas_abertas and vendas_abertas["total"] > 0:
            alertas.append(
                f"Existem {vendas_abertas['total']} venda(s) em aberto neste turno."
            )

        pode_fechar = len(alertas) == 0

        if pode_fechar:
            logger.info(f"Turno #{turno_id} validado: pode ser fechado.")
        else:
            logger.warning(
                f"Turno #{turno_id} com impedimentos para fechamento: {alertas}"
            )

        return {"pode_fechar": pode_fechar, "alertas": alertas}
