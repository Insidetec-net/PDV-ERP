"""
Constantes fiscais e de negócio do Sistema Meu Bazar.
Regime: ME — Lucro Presumido.
"""

# =============================================================================
# REGIME TRIBUTÁRIO
# =============================================================================

REGIME_TRIBUTARIO = 3  # 1=Simples, 2=Simples Excesso, 3=Lucro Presumido

# =============================================================================
# PIS / COFINS — Regime Cumulativo (Lucro Presumido)
# =============================================================================

ALIQUOTA_PIS = 0.65       # 0,65%
ALIQUOTA_COFINS = 3.00    # 3,00%

# =============================================================================
# CST — Código de Situação Tributária (Lucro Presumido)
# =============================================================================

# CST ICMS (mais comuns para varejo)
CST_ICMS = {
    "00": "Tributada integralmente",
    "10": "Tributada com cobrança por substituição tributária",
    "20": "Com redução de base de cálculo",
    "30": "Isenta/não tributada com cobrança por ST",
    "40": "Isenta",
    "41": "Não tributada",
    "50": "Suspensão",
    "51": "Diferimento",
    "60": "ICMS cobrado anteriormente por ST",
    "70": "Com redução de base de cálculo e cobrança por ST",
    "90": "Outras",
}

# CST PIS (mais comuns)
CST_PIS = {
    "01": "Operação tributável — base de cálculo = receita bruta",
    "02": "Operação tributável — base de cálculo = receita bruta (alíq. diferenciada)",
    "04": "Operação tributável — tributação monofásica (alíq. zero)",
    "05": "Operação tributável — substituição tributária",
    "06": "Operação tributável — alíquota zero",
    "07": "Operação isenta da contribuição",
    "08": "Operação sem incidência da contribuição",
    "09": "Operação com suspensão da contribuição",
    "49": "Outras operações de saída",
    "99": "Outras operações",
}

# CST COFINS (espelha PIS na maioria dos casos)
CST_COFINS = CST_PIS.copy()

# =============================================================================
# CFOP — Código Fiscal de Operações e Prestações (mais comuns para varejo)
# =============================================================================

CFOP_VENDA = {
    "5102": "Venda de mercadoria adquirida de terceiros",
    "5405": "Venda de mercadoria adquirida com ST (interno)",
    "5403": "Venda de mercadoria com ST ao destinatário",
    "5101": "Venda de produção do estabelecimento",
    "5949": "Outra saída de mercadoria não especificada",
}

CFOP_ENTRADA = {
    "1102": "Compra para comercialização",
    "1403": "Compra para comercialização com ST",
    "1556": "Compra de material de uso e consumo",
    "1101": "Compra para industrialização",
    "2102": "Compra para comercialização (interestadual)",
}

# CFOP padrão para vendas no PDV
CFOP_PADRAO_VENDA = "5102"
CFOP_PADRAO_ENTRADA = "1102"

# =============================================================================
# NCM — Exemplos comuns de bazar
# =============================================================================

NCM_EXEMPLOS = {
    "62": "Vestuário e seus acessórios, exceto de malha",
    "61": "Vestuário e seus acessórios, de malha",
    "64": "Calçados, polainas e artefatos semelhantes",
    "42": "Obras de couro; artigos de viagem, bolsas",
    "71": "Pérolas, pedras preciosas, bijuterias",
    "95": "Brinquedos, jogos, artigos de divertimento",
    "96": "Obras diversas (canetas, escovas, etc.)",
}

# =============================================================================
# FORMAS DE PAGAMENTO
# =============================================================================

FORMAS_PAGAMENTO = {
    "01": "Dinheiro",
    "02": "Cheque",
    "03": "Cartão de Crédito",
    "04": "Cartão de Débito",
    "05": "Crédito Loja",
    "10": "Vale Alimentação",
    "11": "Vale Refeição",
    "12": "Vale Presente",
    "13": "Vale Combustível",
    "15": "Boleto Bancário",
    "16": "Depósito Bancário",
    "17": "PIX",
    "18": "Transferência bancária",
    "99": "Outros",
}

# Mapeamento interno → código fiscal
PAGAMENTO_MAP = {
    "dinheiro": "01",
    "cartao_credito": "03",
    "cartao_debito": "04",
    "pix": "17",
    "cheque": "02",
}

# =============================================================================
# UNIDADES DE MEDIDA
# =============================================================================

UNIDADES = {
    "UN": "Unidade",
    "KG": "Quilograma",
    "MT": "Metro",
    "M2": "Metro Quadrado",
    "CX": "Caixa",
    "PC": "Peça",
    "PR": "Par",
    "DZ": "Dúzia",
    "LT": "Litro",
    "JG": "Jogo",
}

# =============================================================================
# PERFIS DE USUÁRIO
# =============================================================================

PERFIL_OPERADOR = "operador"
PERFIL_GERENTE = "gerente"
PERFIL_ADMIN = "admin"

PERFIS = {
    PERFIL_OPERADOR: "Operador de Caixa",
    PERFIL_GERENTE: "Gerente",
    PERFIL_ADMIN: "Administrador",
}

# =============================================================================
# STATUS
# =============================================================================

STATUS_VENDA = {
    "finalizada": "Finalizada",
    "cancelada": "Cancelada",
    "contingencia": "Contingência (pendente NFC-e)",
}

STATUS_TURNO = {
    "aberto": "Aberto",
    "fechado": "Fechado",
}

TIPO_MOVIMENTACAO_ESTOQUE = {
    "entrada": "Entrada Manual",
    "saida": "Saída Manual",
    "ajuste": "Ajuste de Inventário",
    "venda": "Baixa por Venda",
    "devolucao": "Devolução",
    "nfe_entrada": "Entrada via NF-e",
}

TIPO_MOVIMENTACAO_CAIXA = {
    "sangria": "Sangria (retirada)",
    "suprimento": "Suprimento (entrada)",
}

# =============================================================================
# CÓDIGO DE BARRAS INTERNO
# =============================================================================

CODIGO_INTERNO_PREFIXO = "MB"
CODIGO_INTERNO_DIGITOS = 6  # MB-000001 a MB-999999

# =============================================================================
# ATALHOS DE TECLADO DO PDV
# =============================================================================

ATALHOS_PDV = {
    "F1": "Buscar produto",
    "F2": "Aplicar desconto",
    "F5": "Finalizar venda",
    "F8": "Cancelar item",
    "F10": "Cancelar venda",
    "F12": "Fechar turno",
}

# =============================================================================
# FOCUS NFE — Endpoints
# =============================================================================

FOCUSNFE_BASE_URL_PRODUCAO = "https://api.focusnfe.com.br"
FOCUSNFE_BASE_URL_HOMOLOGACAO = "https://homologacao.focusnfe.com.br"
FOCUSNFE_ENDPOINT_NFCE = "/v2/nfce"
FOCUSNFE_ENDPOINT_NFE_CONSULTA = "/v2/nfe"
