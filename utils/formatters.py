"""
Formatadores — Moeda BRL, datas, CPF/CNPJ, telefone, etc.
"""

import re
from datetime import datetime, date
from decimal import Decimal
from typing import Union


def format_currency(value: Union[float, Decimal, int, str]) -> str:
    """
    Formata valor como moeda brasileira (R$).

    Exemplos:
        format_currency(1234.56)  -> "R$ 1.234,56"
        format_currency(0)        -> "R$ 0,00"
        format_currency(-50.5)    -> "-R$ 50,50"
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "R$ 0,00"

    negative = value < 0
    value = abs(value)

    # Separar inteiro e decimal
    integer_part = int(value)
    decimal_part = round((value - integer_part) * 100)

    # Formatar com pontos de milhar
    int_str = f"{integer_part:,}".replace(",", ".")
    result = f"R$ {int_str},{decimal_part:02d}"

    if negative:
        result = f"-{result}"

    return result


def format_currency_input(value: Union[float, Decimal]) -> str:
    """
    Formata valor para input (sem R$, com vírgula).

    Exemplo:
        format_currency_input(1234.56) -> "1.234,56"
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0,00"

    integer_part = int(abs(value))
    decimal_part = round((abs(value) - integer_part) * 100)
    int_str = f"{integer_part:,}".replace(",", ".")
    return f"{int_str},{decimal_part:02d}"


def parse_currency(text: str) -> float:
    """
    Converte texto de moeda brasileira para float.

    Exemplos:
        parse_currency("R$ 1.234,56") -> 1234.56
        parse_currency("1234,56")     -> 1234.56
        parse_currency("1234.56")     -> 1234.56
    """
    if not text:
        return 0.0

    # Remover R$, espaços
    text = text.replace("R$", "").replace(" ", "").strip()

    # Se tem vírgula e ponto, é formato BR (1.234,56)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    # Se só tem vírgula, trocar por ponto
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return 0.0


def format_cpf(cpf: str) -> str:
    """
    Formata CPF: XXX.XXX.XXX-XX

    Exemplo:
        format_cpf("12345678901") -> "123.456.789-01"
    """
    digits = re.sub(r"[^0-9]", "", cpf)
    if len(digits) != 11:
        return cpf
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def format_cnpj(cnpj: str) -> str:
    """
    Formata CNPJ: XX.XXX.XXX/XXXX-XX

    Exemplo:
        format_cnpj("12345678000190") -> "12.345.678/0001-90"
    """
    digits = re.sub(r"[^0-9]", "", cnpj)
    if len(digits) != 14:
        return cnpj
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def format_cpf_cnpj(doc: str) -> str:
    """Formata CPF ou CNPJ automaticamente pelo tamanho."""
    digits = re.sub(r"[^0-9]", "", doc)
    if len(digits) == 11:
        return format_cpf(doc)
    elif len(digits) == 14:
        return format_cnpj(doc)
    return doc


def format_phone(phone: str) -> str:
    """
    Formata telefone brasileiro.

    Exemplos:
        format_phone("11999998888")  -> "(11) 99999-8888"
        format_phone("1133334444")   -> "(11) 3333-4444"
    """
    digits = re.sub(r"[^0-9]", "", phone)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return phone


def format_cep(cep: str) -> str:
    """
    Formata CEP: XXXXX-XXX

    Exemplo:
        format_cep("01234567") -> "01234-567"
    """
    digits = re.sub(r"[^0-9]", "", cep)
    if len(digits) != 8:
        return cep
    return f"{digits[:5]}-{digits[5:]}"


def format_date(dt: Union[datetime, date, str], fmt: str = "%d/%m/%Y") -> str:
    """
    Formata data no padrão brasileiro.

    Exemplo:
        format_date(datetime.now()) -> "26/08/2026"
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt

    if isinstance(dt, (datetime, date)):
        return dt.strftime(fmt)
    return str(dt)


def format_datetime(
    dt: Union[datetime, str],
    fmt: str = "%d/%m/%Y %H:%M",
) -> str:
    """
    Formata data e hora.

    Exemplo:
        format_datetime(datetime.now()) -> "26/08/2026 16:30"
    """
    return format_date(dt, fmt)


def format_quantity(qty: Union[float, Decimal], decimals: int = 3) -> str:
    """
    Formata quantidade com casas decimais variáveis.
    Remove zeros à direita desnecessários.

    Exemplos:
        format_quantity(1.0)     -> "1"
        format_quantity(2.500)   -> "2,5"
        format_quantity(3.145)   -> "3,145"
    """
    try:
        value = float(qty)
    except (TypeError, ValueError):
        return "0"

    formatted = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return formatted.replace(".", ",")


def format_percentage(value: Union[float, Decimal]) -> str:
    """
    Formata percentual.

    Exemplo:
        format_percentage(18.5) -> "18,50%"
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0,00%"
    return f"{value:.2f}%".replace(".", ",")


def format_nfe_key(chave: str) -> str:
    """
    Formata chave de NF-e em grupos de 4 dígitos.

    Exemplo:
        "12345678901234567890123456789012345678901234"
        -> "1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234"
    """
    digits = re.sub(r"[^0-9]", "", chave)
    if len(digits) != 44:
        return chave
    return " ".join(digits[i:i+4] for i in range(0, 44, 4))
