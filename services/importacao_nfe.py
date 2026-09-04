"""
Serviço de Importação de NF-e (Nota Fiscal Eletrônica)
Responsável por ler XML de NF-e de fornecedor, extrair dados,
salvar nota de entrada e atualizar estoque.
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

import xml.etree.ElementTree as ET

from models.nota_entrada import NotaEntradaModel, NotaEntradaItemModel
from models.estoque import EstoqueModel
from database.connection import db_transaction

logger = logging.getLogger(__name__)

# Namespaces padrão da NF-e
NFE_NAMESPACES = {
    "nfe": "http://www.portalfiscal.inf.br/nfe",
}


class ImportacaoNfeService:
    """Serviço para importar e processar NF-e de compra/entrada."""

    def __init__(self):
        self.nota_model = NotaEntradaModel()
        self.item_model = NotaEntradaItemModel()
        self.estoque_model = EstoqueModel()

    def parse_xml_nfe(self, xml_path: str) -> dict:
        """
        Lê XML da NF-e (padrão brasileiro) e extrai dados relevantes.

        Args:
            xml_path: Caminho completo para o arquivo XML.

        Returns:
            dict com: emitente (cnpj, nome), chave_nfe, numero_nfe, serie,
            data_emissao, valor_total, itens (lista com codigo, descricao,
            ncm, cfop, quantidade, valor_unitario, valor_total, ean).

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se o XML for inválido ou não for uma NF-e.
        """
        if not os.path.isfile(xml_path):
            raise FileNotFoundError(f"Arquivo XML não encontrado: {xml_path}")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Tenta com namespace padrão e sem namespace
        nfe_element = self._find_element(root, "NFe")
        if nfe_element is None:
            raise ValueError("Arquivo XML não parece ser uma NF-e válida (NFe não encontrada).")

        inf_nfe = self._find_element(nfe_element, "infNFe")
        if inf_nfe is None:
            raise ValueError("Arquivo XML não parece ser uma NF-e válida (infNFe não encontrado).")

        # Chave de acesso (Id no formato NFe + 44 dígitos)
        chave_nfe = inf_nfe.get("Id", "").replace("NFe", "")
        if not chave_nfe or len(chave_nfe) != 44:
            raise ValueError(f"Chave de acesso inválida: '{chave_nfe}'")

        # Dados de identificação
        ide = self._find_element(inf_nfe, "ide")
        if ide is None:
            raise ValueError("Bloco 'ide' não encontrado na NF-e.")

        numero_nfe = self._get_child_text(ide, "nNF", "")
        serie = self._get_child_text(ide, "serie", "0")
        data_emissao_str = self._get_child_text(ide, "dhEmi") or self._get_child_text(ide, "dEmi", "")

        # Emitente
        emit = self._find_element(inf_nfe, "emit")
        emitente_cnpj = ""
        emitente_nome = ""
        if emit is not None:
            emitente_cnpj = self._get_child_text(emit, "CNPJ", "")
            emitente_nome = self._get_child_text(emit, "xNome", "")

        # Totais
        total = self._find_element(inf_nfe, "total")
        valor_total = 0.0
        if total is not None:
            icms_tot = self._find_element(total, "ICMSTot")
            if icms_tot is not None:
                valor_total = float(self._get_child_text(icms_tot, "vNF", "0"))

        # Itens
        itens = []
        for det in inf_nfe.findall(".//det") if hasattr(inf_nfe, 'findall') else self._findall_recursive(inf_nfe, "det"):
            prod = self._find_element(det, "prod")
            if prod is None:
                continue

            item = {
                "numero_item": int(det.get("nItem", "0")),
                "codigo_ean": self._get_child_text(prod, "cEAN", "") or self._get_child_text(prod, "cProd", ""),
                "codigo_produto": self._get_child_text(prod, "cProd", ""),
                "descricao": self._get_child_text(prod, "xProd", ""),
                "ncm": self._get_child_text(prod, "NCM", ""),
                "cfop": self._get_child_text(prod, "CFOP", ""),
                "unidade": self._get_child_text(prod, "uCom", "UN"),
                "quantidade": float(self._get_child_text(prod, "qCom", "0")),
                "valor_unitario": float(self._get_child_text(prod, "vUnCom", "0")),
                "valor_total": float(self._get_child_text(prod, "vProd", "0")),
            }
            itens.append(item)

        dados = {
            "chave_nfe": chave_nfe,
            "numero_nfe": numero_nfe,
            "serie": serie,
            "data_emissao": data_emissao_str,
            "emitente_cnpj": emitente_cnpj,
            "emitente_nome": emitente_nome,
            "valor_total": valor_total,
            "xml_path": xml_path,
            "itens": itens,
        }

        logger.info(
            f"NF-e parseada: chave={chave_nfe}, emitente={emitente_nome}, "
            f"itens={len(itens)}, total={valor_total:.2f}"
        )
        return dados

    def salvar_nota_entrada(self, dados_nfe: dict, usuario_id: int) -> int:
        """
        Salva nota de entrada e seus itens em transação, e atualiza estoque
        dos itens vinculados.

        Args:
            dados_nfe: Dicionário retornado por parse_xml_nfe().
            usuario_id: ID do usuário que está importando.

        Returns:
            ID da nota de entrada criada.

        Raises:
            ValueError: Se já existe nota com a mesma chave.
        """
        chave = dados_nfe.get("chave_nfe", "")
        if not chave:
            raise ValueError("Chave da NF-e não informada.")

        if self.validar_nfe_importada(chave):
            raise ValueError(f"NF-e já importada anteriormente (chave: {chave}).")

        with db_transaction() as (conn, cursor):
            # Inserir nota_entrada
            cursor.execute(
                """
                INSERT INTO notas_entrada
                (chave_nfe, numero_nfe, serie, fornecedor_cnpj,
                 fornecedor_nome, data_emissao, valor_total, xml_path,
                 usuario_id, importado_em, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                """,
                (
                    chave,
                    dados_nfe.get("numero_nfe", ""),
                    dados_nfe.get("serie", ""),
                    dados_nfe.get("emitente_cnpj", ""),
                    dados_nfe.get("emitente_nome", ""),
                    dados_nfe.get("data_emissao"),
                    dados_nfe.get("valor_total", 0.0),
                    dados_nfe.get("xml_path", ""),
                    usuario_id,
                    dados_nfe.get("observacao", None),
                ),
            )
            nota_id = cursor.lastrowid
            logger.info(f"Nota de entrada criada: ID={nota_id}")

            # Inserir itens
            for item in dados_nfe.get("itens", []):
                cursor.execute(
                    """
                    INSERT INTO notas_entrada_itens
                    (nota_entrada_id, produto_id, numero_item, codigo_ean,
                     nome_produto_nfe, ncm, cfop, unidade, quantidade,
                     valor_unitario, valor_total, vinculado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        nota_id,
                        item.get("produto_id", None),
                        item.get("numero_item", 0),
                        item.get("codigo_ean", ""),
                        item.get("descricao", ""),
                        item.get("ncm", ""),
                        item.get("cfop", ""),
                        item.get("unidade", "UN"),
                        item.get("quantidade", 0.0),
                        item.get("valor_unitario", 0.0),
                        item.get("valor_total", 0.0),
                        item.get("vinculado", False),
                    ),
                )

            # Atualizar estoque dos itens vinculados (produto_id preenchido)
            for item in dados_nfe.get("itens", []):
                produto_id = item.get("produto_id")
                if produto_id:
                    try:
                        self.estoque_model.register_movement(
                            produto_id=int(produto_id),
                            usuario_id=usuario_id,
                            tipo="nfe_entrada",
                            quantidade=float(item.get("quantidade", 0)),
                            observacao=f"Entrada NF-e {nota_id}",
                            nota_entrada_id=nota_id,
                        )
                        logger.info(
                            f"Estoque atualizado: produto={produto_id}, "
                            f"qtd={item.get('quantidade', 0)}, nota={nota_id}"
                        )
                    except ValueError as ve:
                        logger.warning(
                            f"Não foi possível atualizar estoque do produto {produto_id}: {ve}"
                        )

        logger.info(f"NF-e {chave} importada com sucesso. Nota ID={nota_id}")
        return nota_id

    def listar_notas_entrada(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Lista notas de entrada importadas em um período.

        Args:
            start_date: Data inicial (YYYY-MM-DD).
            end_date: Data final (YYYY-MM-DD).
            limit: Máximo de registros retornados.

        Returns:
            Lista de dicionários com dados das notas.
        """
        from database.connection import execute_query

        query = """
            SELECT ne.*, u.nome as usuario_nome,
                   COUNT(nei.id) as qtd_itens,
                   SUM(CASE WHEN nei.vinculado = TRUE THEN 1 ELSE 0 END) as itens_vinculados
            FROM notas_entrada ne
            JOIN usuarios u ON ne.usuario_id = u.id
            LEFT JOIN notas_entrada_itens nei ON ne.id = nei.nota_entrada_id
        """
        conditions = []
        params = []

        if start_date:
            conditions.append("DATE(ne.importado_em) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(ne.importado_em) <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" GROUP BY ne.id ORDER BY ne.importado_em DESC LIMIT {int(limit)}"

        return execute_query(query, tuple(params) if params else None) or []

    def get_nota_entrada_detalhes(self, nota_id: int) -> Optional[Dict]:
        """
        Busca nota de entrada completa com seus itens.

        Args:
            nota_id: ID da nota de entrada.

        Returns:
            Dicionário com dados da nota e lista de itens, ou None se não existir.
        """
        return self.nota_model.get_with_items(nota_id)

    def validar_nfe_importada(self, chave: str) -> bool:
        """
        Verifica se já existe nota de entrada com a mesma chave de acesso.

        Args:
            chave: Chave de acesso da NF-e (44 dígitos).

        Returns:
            True se a NF-e já foi importada, False caso contrário.
        """
        if not chave or len(chave) != 44:
            return False

        resultado = self.nota_model.get_by_chave(chave)
        return resultado is not None

    # --- Métodos auxiliares para navegação no XML ---

    def _find_element(self, parent: ET.Element, tag: str) -> Optional[ET.Element]:
        """Busca elemento considerando namespaces."""
        # Tenta com namespace
        for ns_prefix, uri in NFE_NAMESPACES.items():
            element = parent.find(f"{{{uri}}}{tag}")
            if element is not None:
                return element
        # Tenta sem namespace (XMLs antigos)
        return parent.find(tag)

    def _findall_recursive(self, parent: ET.Element, tag: str) -> List[ET.Element]:
        """Busca todos os elementos recursivamente (fallback sem namespace)."""
        results = []
        for elem in parent:
            # Remove namespace do tag
            local_tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local_tag == tag:
                results.append(elem)
            results.extend(self._findall_recursive(elem, tag))
        return results

    def _get_child_text(self, parent: ET.Element, tag: str, default: str = "") -> str:
        """Retorna texto do filho com namespace ou sem namespace."""
        child = self._find_element(parent, tag)
        if child is not None and child.text:
            return child.text.strip()
        return default
