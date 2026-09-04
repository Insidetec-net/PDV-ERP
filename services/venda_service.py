"""
VendaService — Lógica de negócio de Vendas.
Camada entre Models (DAOs) e UI, orquestrando operações de venda.
"""

import logging
from typing import Dict, List, Optional
from decimal import Decimal

from models.venda import VendaModel
from services.fiscal_service import FiscalService

logger = logging.getLogger(__name__)


def to_decimal(val):
    """Converte valor para Decimal com segurança."""
    if isinstance(val, Decimal):
        return val
    if val is None:
        return Decimal('0')
    return Decimal(str(val))


class VendaService:
    """Serviço de vendas: finalização, cancelamento, cálculos e resumos."""

    MAX_DESCONTO_PERCENT = 0.20  # 20% — regra do bazar

    def __init__(self):
        self.venda_model = VendaModel()
        self.fiscal_service: Optional[FiscalService] = None
        try:
            self.fiscal_service = FiscalService()
        except Exception as exc:
            logger.warning("FiscalService não inicializado: %s", exc)

    @staticmethod
    def _is_fiscal_configurado(fiscal: Optional[FiscalService]) -> bool:
        """Verifica se o serviço fiscal está configurado para emissão."""
        if fiscal is None:
            return False
        token = getattr(fiscal, "token", None)
        ambiente = getattr(fiscal, "ambiente", None)
        return bool(token) and bool(ambiente)

    def finalizar_venda(
        self,
        turno_id: int,
        usuario_id: int,
        items: List[Dict],
        pagamentos: List[Dict],
        cliente_id: int = None,
        desconto: float = 0.0,
    ) -> Dict:
        """
        Finaliza uma venda completa.

        Valida valor recebido >= total, calcula troco, aplica desconto validado,
        persiste via VendaModel e tenta emitir NFC-e se configurado.

        Args:
            turno_id: ID do turno aberto.
            usuario_id: ID do operador.
            items: Lista de {produto_id, quantidade, preco_unitario, desconto_item}.
            pagamentos: Lista de {forma, valor, bandeira?, nsu?, parcelas?}.
            cliente_id: ID do cliente (opcional).
            desconto: Desconto total da venda.

        Returns:
            {venda_id, status, nfce_dados}.

        Raises:
            ValueError: se valor recebido < total ou se dados obrigatórios faltarem.
        """
        if not items:
            raise ValueError("A venda deve ter pelo menos um item.")
        if not pagamentos:
            raise ValueError("A venda deve ter pelo menos um pagamento.")

        # 1. Calcular subtotal e validar desconto
        subtotal = sum(
            to_decimal(item["quantidade"]) * to_decimal(item["preco_unitario"]) - to_decimal(item.get("desconto_item", 0))
            for item in items
        )
        desconto_validado = self.validar_desconto(subtotal, desconto)
        total = subtotal - desconto_validado

        # 2. Validar valor recebido
        valor_recebido = sum(to_decimal(p["valor"]) for p in pagamentos)
        if valor_recebido < total - Decimal('0.005'):  # tolerância de meio centavo
            raise ValueError(
                f"Valor recebido (R$ {valor_recebido:.2f}) insuficiente. "
                f"Total: R$ {total:.2f}"
            )

        troco = self.calcular_troco(total, valor_recebido)
        logger.info(
            "Finalizando venda — turno=%s usuario=%s subtotal=%.2f desconto=%.2f "
            "total=%.2f recebido=%.2f troco=%.2f",
            turno_id, usuario_id, float(subtotal), float(desconto_validado),
            float(total), float(valor_recebido), float(troco),
        )

        # 3. Persistir venda via model (transação atômica)
        venda_id = self.venda_model.create_sale(
            turno_id=turno_id,
            usuario_id=usuario_id,
            items=items,
            payments=pagamentos,
            cliente_id=cliente_id,
            desconto=float(desconto_validado),
        )
        logger.info("Venda #%d persistida com sucesso.", venda_id)

        # 4. Tentar emitir NFC-e
        nfce_dados: Dict = {}
        if self._is_fiscal_configurado(self.fiscal_service):
            try:
                nfce_dados = self.fiscal_service.emitir_nfce(
                    venda_id=venda_id,
                    itens=items,
                    pagamentos=pagamentos,
                    total=float(total),
                )
                logger.info("NFC-e emitida para venda #%d: %s", venda_id, nfce_dados.get("status"))
            except Exception as exc:
                logger.error("Erro ao emitir NFC-e para venda #%d: %s", venda_id, exc)
                nfce_dados = {"status": "erro", "mensagem": str(exc)}
        else:
            logger.info("NFC-e não configurada — pulando emissão para venda #%d.", venda_id)
            nfce_dados = {"status": "nao_configurada"}

        return {
            "venda_id": venda_id,
            "status": "finalizada",
            "nfce_dados": nfce_dados,
        }

    def cancelar_venda(self, venda_id: int, usuario_id: int) -> bool:
        """
        Cancela uma venda e reverte estoque via VendaModel.

        Args:
            venda_id: ID da venda a cancelar.
            usuario_id: ID do operador que está cancelando.

        Returns:
            True se cancelada com sucesso.
        """
        logger.info("Cancelando venda #%d por usuario #%d.", venda_id, usuario_id)
        resultado = self.venda_model.cancel_sale(venda_id, usuario_id)
        if resultado:
            logger.info("Venda #%d cancelada com sucesso.", venda_id)
        else:
            logger.warning("Venda #%d não encontrada ou já cancelada.", venda_id)
        return resultado

    @staticmethod
    def calcular_troco(total: float, valor_recebido: float) -> float:
        """
        Calcula o troco.

        Args:
            total: Valor total da venda.
            valor_recebido: Valor pago pelo cliente.

        Returns:
            Valor do troco (>= 0).
        """
        total_dec = to_decimal(total)
        recebido_dec = to_decimal(valor_recebido)
        troco = max(Decimal('0'), recebido_dec - total_dec)
        return float(round(troco, 2))

    def validar_desconto(self, valor_atual: float, desconto: float) -> float:
        """
        Valida o desconto aplicado, garantindo que não ultrapasse 20% do valor
        da venda (regra do bazar).

        Args:
            valor_atual: Valor subtotal da venda (sem desconto).
            desconto: Desconto solicitado.

        Returns:
            Desconto validado (limitado a 20% se exceder).
        """
        if desconto <= 0:
            return 0.0
        
        valor_dec = to_decimal(valor_atual)
        desconto_dec = to_decimal(desconto)
        max_desconto = round(valor_dec * Decimal(str(self.MAX_DESCONTO_PERCENT)), 2)
        
        if desconto_dec > max_desconto:
            logger.warning(
                "Desconto R$ %.2f excede máximo permitido (20%% = R$ %.2f). "
                "Limitando.",
                desconto, float(max_desconto),
            )
            return float(max_desconto)
        return desconto

    def get_resumo_venda(self, venda_id: int) -> Dict:
        """
        Retorna resumo completo de uma venda.

        Args:
            venda_id: ID da venda.

        Returns:
            Dicionário com dados da venda, itens e pagamentos.
        """
        return self.venda_model.get_sale_details(venda_id)
