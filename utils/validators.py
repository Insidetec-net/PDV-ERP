"""
Validadores — CPF, CNPJ, EAN-13, Chave NF-e, Email.
"""

import re


def validate_cpf(cpf: str) -> bool:
    """
    Valida um CPF (com ou sem formatação).

    Args:
        cpf: CPF no formato XXX.XXX.XXX-XX ou XXXXXXXXXXX.

    Returns:
        True se o CPF é válido.
    """
    # Remover caracteres não numéricos
    cpf = re.sub(r"[^0-9]", "", cpf)

    if len(cpf) != 11:
        return False

    # Rejeitar CPFs com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False

    # Calcular primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        return False

    # Calcular segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    return int(cpf[10]) == digito2


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ (com ou sem formatação).

    Args:
        cnpj: CNPJ no formato XX.XXX.XXX/XXXX-XX ou XXXXXXXXXXXXXX.

    Returns:
        True se o CNPJ é válido.
    """
    cnpj = re.sub(r"[^0-9]", "", cnpj)

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    # Primeiro dígito
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cnpj[12]) != digito1:
        return False

    # Segundo dígito
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    return int(cnpj[13]) == digito2


def validate_cpf_cnpj(doc: str) -> bool:
    """Valida CPF ou CNPJ (detecta automaticamente pelo tamanho)."""
    doc_digits = re.sub(r"[^0-9]", "", doc)
    if len(doc_digits) == 11:
        return validate_cpf(doc)
    elif len(doc_digits) == 14:
        return validate_cnpj(doc)
    return False


def validate_ean13(code: str) -> bool:
    """
    Valida um código de barras EAN-13.

    Args:
        code: Código de 13 dígitos.

    Returns:
        True se o EAN-13 é válido.
    """
    code = re.sub(r"[^0-9]", "", code)

    if len(code) != 13:
        return False

    # Calcular dígito verificador
    soma = 0
    for i in range(12):
        peso = 1 if i % 2 == 0 else 3
        soma += int(code[i]) * peso

    check = (10 - (soma % 10)) % 10
    return int(code[12]) == check


def validate_barcode(code: str) -> bool:
    """
    Valida código de barras genérico.
    Aceita EAN-13, EAN-8, UPC-A (12 dígitos) ou código interno (MB-XXXXXX).
    """
    if not code:
        return False

    # Código interno do sistema
    if code.upper().startswith("MB-"):
        return len(code) >= 4

    digits = re.sub(r"[^0-9]", "", code)

    if len(digits) == 13:
        return validate_ean13(code)
    elif len(digits) in (8, 12):
        return True  # EAN-8 e UPC-A (validação simplificada)

    return len(digits) > 0


def validate_nfe_key(chave: str) -> bool:
    """
    Valida uma chave de acesso de NF-e (44 dígitos).

    A chave é composta por:
    - 2 dígitos: UF
    - 4 dígitos: AAMM (ano/mês)
    - 14 dígitos: CNPJ
    - 2 dígitos: modelo (55=NF-e, 65=NFC-e)
    - 3 dígitos: série
    - 9 dígitos: número da NF
    - 1 dígito: tipo emissão
    - 8 dígitos: código numérico
    - 1 dígito: dígito verificador
    """
    chave = re.sub(r"[^0-9]", "", chave)

    if len(chave) != 44:
        return False

    # Verificar se não é tudo zero
    if chave == "0" * 44:
        return False

    # Validar UF (código IBGE)
    uf = int(chave[:2])
    ufs_validas = {
        11, 12, 13, 14, 15, 16, 17,  # Norte
        21, 22, 23, 24, 25, 26, 27, 28, 29,  # Nordeste
        31, 32, 33, 35,  # Sudeste
        41, 42, 43,  # Sul
        50, 51, 52, 53,  # Centro-Oeste
    }
    if uf not in ufs_validas:
        return False

    # Validar modelo (55 = NF-e, 65 = NFC-e)
    modelo = chave[20:22]
    if modelo not in ("55", "65"):
        return False

    return True


def validate_email(email: str) -> bool:
    """Validação básica de e-mail."""
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Valida telefone brasileiro (com ou sem formatação)."""
    digits = re.sub(r"[^0-9]", "", phone)
    return len(digits) in (10, 11)  # fixo ou celular com DDD


def validate_cep(cep: str) -> bool:
    """Valida CEP brasileiro."""
    digits = re.sub(r"[^0-9]", "", cep)
    return len(digits) == 8
