"""
Gerador de código de barras EAN-13 e Code128 para o Sistema Meu Bazar.
"""

import os
import logging
from io import BytesIO
from typing import List, Optional

from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def gerar_ean13(codigo: str) -> bytes:
    """
    Gera uma imagem PNG do código de barras EAN-13.

    Args:
        codigo: Código numérico de 12 ou 13 dígitos (checksum calculado automaticamente se 12).

    Returns:
        Bytes da imagem PNG gerada.
    """
    codigo = codigo.strip().zfill(12)[:12]
    ean = EAN13(codigo, writer=ImageWriter())
    buffer = BytesIO()
    ean.write(buffer, options={
        'module_width': 0.3,
        'module_height': 15.0,
        'font_size': 10,
        'text_distance': 5.0,
    })
    buffer.seek(0)
    return buffer.read()


def gerar_code128(codigo: str) -> bytes:
    """
    Gera uma imagem PNG do código de barras Code128.

    Args:
        codigo: String alfanumérica a ser codificada.

    Returns:
        Bytes da imagem PNG gerada.
    """
    codigo = codigo.strip()
    code128 = Code128(codigo, writer=ImageWriter())
    buffer = BytesIO()
    code128.write(buffer, options={
        'module_width': 0.25,
        'module_height': 15.0,
        'font_size': 10,
        'text_distance': 5.0,
    })
    buffer.seek(0)
    return buffer.read()


def salvar_barcode(codigo: str, path: str) -> str:
    """
    Salva a imagem do código de barras em disco.

    Detecta automaticamente EAN-13 (se numérico) ou Code128.

    Args:
        codigo: Código a ser gerado.
        path: Caminho completo do arquivo de saída (ex: '/tmp/barcode.png').

    Returns:
        Caminho do arquivo salvo.
    """
    codigo = codigo.strip()
    if codigo.isdigit() and len(codigo) <= 13:
        png_bytes = gerar_ean13(codigo)
    else:
        png_bytes = gerar_code128(codigo)

    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png_bytes)

    logger.info("Barcode salvo em: %s", path)
    return path


def gerar_codigo_barras_pdf(codigos: List[str], output_path: str) -> str:
    """
    Gera um PDF contendo múltiplos códigos de barras.

    Args:
        codigos: Lista de códigos a serem gerados.
        output_path: Caminho do arquivo PDF de saída.

    Returns:
        Caminho do arquivo PDF gerado.
    """
    imagens = []
    for codigo in codigos:
        codigo = codigo.strip()
        if codigo.isdigit() and len(codigo) <= 13:
            png_bytes = gerar_ean13(codigo)
        else:
            png_bytes = gerar_code128(codigo)

        img = Image.open(BytesIO(png_bytes)).convert('RGB')
        imagens.append(img)

    if not imagens:
        raise ValueError("Nenhum código de barras fornecido.")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    primeira = imagens[0]
    restantes = imagens[1:] if len(imagens) > 1 else []
    primeira.save(
        output_path,
        'PDF',
        save_all=True,
        append_images=restantes,
        resolution=150.0,
    )

    logger.info("PDF com %d códigos de barras salvo em: %s", len(codigos), output_path)
    return output_path
