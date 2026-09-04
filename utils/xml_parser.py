"""
Parser de XML NF-e (Nota Fiscal Eletrônica) para o Sistema Meu Bazar.
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

NAMESPACES = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
}


def _get_text(element: Optional[ET.Element], tag: str, ns: str = 'nfe') -> str:
    """Extrai texto de um elemento XML com namespace."""
    if element is None:
        return ''
    el = element.find(f'{ns}:{tag}', NAMESPACES)
    return el.text.strip() if el is not None and el.text else ''


def _get_float(element: Optional[ET.Element], tag: str, ns: str = 'nfe') -> float:
    """Extrai valor float de um elemento XML."""
    text = _get_text(element, tag, ns)
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def extrair_chave_acesso(xml_path: str) -> str:
    """
    Extrai a chave de acesso da NF-e.

    Args:
        xml_path: Caminho do arquivo XML da NF-e.

    Returns:
        Chave de acesso (44 dígitos).
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Tenta encontrar a chave em vários locais possíveis
    for tag in ['chNFe', 'chave', 'cNF']:
        el = root.find(f'.//nfe:{tag}', NAMESPACES)
        if el is not None and el.text:
            return el.text.strip()

    # Fallback: procura em qualquer lugar
    for el in root.iter():
        if el.tag.endswith('}chNFe') or el.tag == 'chNFe':
            if el.text:
                return el.text.strip()

    logger.warning("Chave de acesso não encontrada em: %s", xml_path)
    return ''


def parse_nfe(xml_path: str) -> Dict:
    """
    Lê o XML da NF-e e extrai informações principais.

    Args:
        xml_path: Caminho do arquivo XML da NF-e.

    Returns:
        Dicionário com dados da NF-e:
        - emitente: {cnpj, nome, ie, endereco, cidade, uf}
        - destinatario: {cnpj_cpf, nome, endereco, cidade, uf}
        - itens: [{codigo, descricao, ncm, cfop, unidade, quantidade, valor_unitario, valor_total}]
        - totais: {valor_total, valor_produtos, icms_base, icms_valor, ipi_valor}
        - nota: {numero, serie, data_emissao, natureza_operacao}
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"Arquivo XML não encontrado: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Identifica o elemento infNFe
    inf_nfe = root.find('.//nfe:infNFe', NAMESPACES)
    if inf_nfe is None:
        inf_nfe = root

    # Emitente
    emit = inf_nfe.find('nfe:emit', NAMESPACES)
    emitente = {
        'cnpj': _get_text(emit, 'CNPJ'),
        'cpf': _get_text(emit, 'CPF'),
        'nome': _get_text(emit, 'xNome'),
        'fantasia': _get_text(emit, 'xFant'),
        'ie': _get_text(emit, 'IE'),
        'endereco': _get_text(emit, 'xLgr'),
        'numero': _get_text(emit, 'nro'),
        'bairro': _get_text(emit, 'xBairro'),
        'cidade': _get_text(emit, 'xMun'),
        'uf': _get_text(emit, 'UF'),
        'cep': _get_text(emit, 'CEP'),
    }

    # Destinatário
    dest = inf_nfe.find('nfe:dest', NAMESPACES)
    destinatario = {
        'cnpj': _get_text(dest, 'CNPJ'),
        'cpf': _get_text(dest, 'CPF'),
        'nome': _get_text(dest, 'xNome'),
        'endereco': _get_text(dest, 'xLgr'),
        'numero': _get_text(dest, 'nro'),
        'bairro': _get_text(dest, 'xBairro'),
        'cidade': _get_text(dest, 'xMun'),
        'uf': _get_text(dest, 'UF'),
        'cep': _get_text(dest, 'CEP'),
    }

    # Itens
    itens = []
    for det in inf_nfe.findall('.//nfe:det', NAMESPACES):
        prod = det.find('nfe:prod', NAMESPACES)
        imposto = det.find('nfe:imposto', NAMESPACES)

        item = {
            'numero': det.get('nItem', ''),
            'codigo': _get_text(prod, 'cProd'),
            'ean': _get_text(prod, 'cEAN'),
            'descricao': _get_text(prod, 'xProd'),
            'ncm': _get_text(prod, 'NCM'),
            'cfop': _get_text(prod, 'CFOP'),
            'unidade': _get_text(prod, 'uCom'),
            'quantidade': _get_float(prod, 'qCom'),
            'valor_unitario': _get_float(prod, 'vUnCom'),
            'valor_total': _get_float(prod, 'vProd'),
            'desconto': _get_float(prod, 'vDesc'),
        }

        # Impostos
        icms = imposto.find('nfe:ICMS', NAMESPACES) if imposto is not None else None
        if icms is not None:
            for icms_tipo in icms:
                item['icms_origem'] = icms_tipo.get('orig', '')
                item['icms_cst'] = _get_text_from_parent(icms_tipo, 'CST')
                item['icms_base'] = _get_float_from_parent(icms_tipo, 'vBC')
                item['icms_aliquota'] = _get_float_from_parent(icms_tipo, 'pICMS')
                item['icms_valor'] = _get_float_from_parent(icms_tipo, 'vICMS')
                break

        ipi = imposto.find('nfe:IPI', NAMESPACES) if imposto is not None else None
        if ipi is not None:
            item['ipi_valor'] = _get_float_from_parent(ipi, 'vIPI')

        itens.append(item)

    # Totais
    total = inf_nfe.find('nfe:total', NAMESPACES)
    icms_total = total.find('nfe:ICMSTot', NAMESPACES) if total is not None else None
    totais = {
        'valor_total': _get_float(icms_total, 'vNF'),
        'valor_produtos': _get_float(icms_total, 'vProd'),
        'icms_base': _get_float(icms_total, 'vBC'),
        'icms_valor': _get_float(icms_total, 'vICMS'),
        'ipi_valor': _get_float(icms_total, 'vIPI'),
        'pis_valor': _get_float(icms_total, 'vPIS'),
        'cofins_valor': _get_float(icms_total, 'vCOFINS'),
        'desconto': _get_float(icms_total, 'vDesc'),
        'frete': _get_float(icms_total, 'vFrete'),
    }

    # Dados da nota
    ide = inf_nfe.find('nfe:ide', NAMESPACES)
    nota = {
        'numero': _get_text(ide, 'nNF'),
        'serie': _get_text(ide, 'serie'),
        'data_emissao': _get_text(ide, 'dhEmi') or _get_text(ide, 'dEmi'),
        'natureza_operacao': _get_text(ide, 'natOp'),
        'tipo': _get_text(ide, 'tpNF'),
        'chave_acesso': extrair_chave_acesso(xml_path),
    }

    return {
        'emitente': emitente,
        'destinatario': destinatario,
        'itens': itens,
        'totais': totais,
        'nota': nota,
    }


def _get_text_from_parent(parent: ET.Element, tag: str) -> str:
    """Busca tag direta (sem namespace) dentro de um elemento pai."""
    el = parent.find(tag)
    return el.text.strip() if el is not None and el.text else ''


def _get_float_from_parent(parent: ET.Element, tag: str) -> float:
    """Busca float direto (sem namespace) dentro de um elemento pai."""
    text = _get_text_from_parent(parent, tag)
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def nfe_para_nota_entrada(xml_path: str) -> Dict:
    """
    Converte uma NF-e para o formato de nota_entrada do sistema.

    Args:
        xml_path: Caminho do arquivo XML da NF-e.

    Returns:
        Dicionário formatado para nota_entrada:
        - fornecedor: dados do emitente
        - nota_fiscal: número, série, data, chave
        - produtos: lista de produtos da nota
        - totais: valores totais
    """
    nfe_data = parse_nfe(xml_path)

    nota_entrada = {
        'fornecedor': {
            'codigo': nfe_data['emitente']['cnpj'] or nfe_data['emitente']['cpf'],
            'razao_social': nfe_data['emitente']['nome'],
            'nome_fantasia': nfe_data['emitente']['fantasia'],
            'inscricao_estadual': nfe_data['emitente']['ie'],
            'endereco': nfe_data['emitente']['endereco'],
            'numero': nfe_data['emitente']['numero'],
            'bairro': nfe_data['emitente']['bairro'],
            'cidade': nfe_data['emitente']['cidade'],
            'uf': nfe_data['emitente']['uf'],
            'cep': nfe_data['emitente']['cep'],
        },
        'nota_fiscal': {
            'numero': nfe_data['nota']['numero'],
            'serie': nfe_data['nota']['serie'],
            'data_emissao': nfe_data['nota']['data_emissao'],
            'natureza_operacao': nfe_data['nota']['natureza_operacao'],
            'chave_acesso': nfe_data['nota']['chave_acesso'],
        },
        'produtos': [],
        'totais': {
            'valor_total': nfe_data['totais']['valor_total'],
            'valor_produtos': nfe_data['totais']['valor_produtos'],
            'desconto': nfe_data['totais']['desconto'],
            'frete': nfe_data['totais']['frete'],
            'icms_valor': nfe_data['totais']['icms_valor'],
            'ipi_valor': nfe_data['totais']['ipi_valor'],
        },
    }

    for item in nfe_data['itens']:
        produto = {
            'codigo': item['codigo'],
            'codigo_barras': item['ean'],
            'descricao': item['descricao'],
            'ncm': item['ncm'],
            'cfop': item['cfop'],
            'unidade': item['unidade'],
            'quantidade': item['quantidade'],
            'valor_unitario': item['valor_unitario'],
            'valor_total': item['valor_total'],
            'desconto': item.get('desconto', 0.0),
            'icms_cst': item.get('icms_cst', ''),
            'icms_aliquota': item.get('icms_aliquota', 0.0),
            'icms_valor': item.get('icms_valor', 0.0),
        }
        nota_entrada['produtos'].append(produto)

    logger.info(
        "NF-e convertida para nota_entrada: %s, %d itens",
        nota_entrada['nota_fiscal']['numero'],
        len(nota_entrada['produtos']),
    )

    return nota_entrada
