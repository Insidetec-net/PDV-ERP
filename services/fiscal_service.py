"""
Serviço de Integração Fiscal - Focus NFe
Responsável por emitir NFC-e (Nota Fiscal de Consumidor Eletrônica)
"""

import requests
import json
import uuid
import logging
from datetime import datetime

from models.configuracao import ConfiguracaoModel

logger = logging.getLogger(__name__)

class FiscalService:
    def __init__(self):
        self.config_model = ConfiguracaoModel()
        self._load_config()

    def _load_config(self):
        """Carrega as configurações do banco (Token, Ambiente, CNPJ, etc)."""
        configs = self.config_model.get_all_as_dict()
        
        self.token = configs.get("focus_nfe_token", "")
        self.ambiente = configs.get("ambiente_fiscal", "homologacao") # homologacao ou producao
        self.cnpj_emitente = configs.get("cnpj_empresa", "")
        
        # Base URLs
        if self.ambiente == "producao":
            self.base_url = "https://api.focusnfe.com.br/v2"
        else:
            self.base_url = "https://homologacao.focusnfe.com.br/v2"

    def gerar_danfe_fake_pdf(self, venda_id: int, itens: list, pagamentos: list, total: float, output_path: str):
        from PyQt6.QtGui import QTextDocument
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtCore import QSizeF, QMarginsF
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: monospace; font-size: 10px; color: #000; }}
                .center {{ text-align: center; }}
                .bold {{ font-weight: bold; }}
                .line {{ border-bottom: 1px dashed #000; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="center bold" style="font-size: 14px;">MEU BAZAR LTDA</div>
            <div class="center">CNPJ: 00.000.000/0001-00</div>
            <div class="center">Rua das Flores, 123 - Centro</div>
            <div class="line"></div>
            <div class="center bold">Documento Auxiliar da NFC-e</div>
            <div class="line"></div>
            <table width="100%">
                <tr><th align="left">Qtd</th><th align="left">Produto</th><th align="right">Vl Unit</th><th align="right">Vl Total</th></tr>
        """
        for item in itens:
            qtd = item.get("quantidade", item.get("qtd", 1))
            nome = item.get("nome", "PRODUTO DIVERSO")
            v_unit = float(item.get("preco_unitario", item.get("v_unit", 0)))
            subt = qtd * v_unit
            html += f"<tr><td>{qtd}</td><td>{nome[:15]}</td><td align='right'>{v_unit:.2f}</td><td align='right'>{subt:.2f}</td></tr>"
            
        html += f"""
            </table>
            <div class="line"></div>
            <div class="bold" style="text-align:right; font-size: 12px;">TOTAL R$ {total:.2f}</div>
            <div class="line"></div>
        """
        for p in pagamentos:
            v = float(p.get('valor', total))
            forma = p.get('forma', 'dinheiro').upper()
            html += f"<div>PAGAMENTO: {forma} - R$ {v:.2f}</div>"
        
        import random
        chave = f"4326 {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
        
        html += f"""
            <div class="line"></div>
            <div class="center">
                Consulte pela Chave de Acesso em<br>
                http://www.sefaz.rs.gov.br/nfce<br>
                <br>
                CHAVE DE ACESSO (SIMULADA)<br>
                {chave}
            </div>
            <div class="center" style="margin-top: 10px;">
                *** OBRIGADO PELA PREFERÊNCIA ***
            </div>
        </body>
        </html>
        """
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageSize(QPrinter.PageSize(QSizeF(80, 200), QPrinter.Unit.Millimeter))
        printer.setPageMargins(QMarginsF(2, 2, 2, 2), QPrinter.PageLayout.Unit.Millimeter)
        
        doc.print(printer)

    def emitir_nfce(self, venda_id: int, itens: list, pagamentos: list, total: float) -> dict:
        """
        Gera um PDF local simulando a impressora térmica 80mm para fins de teste fakes.
        """
        import os
        from datetime import datetime
        import platform
        import subprocess
        
        filename = f"NFCe_Fake_{venda_id}_{datetime.now().strftime('%H%M%S')}.pdf"
        output_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        
        try:
            self.gerar_danfe_fake_pdf(venda_id, itens, pagamentos, total, output_path)
            
            # Abre o PDF na tela do usuario
            if platform.system() == 'Darwin':
                subprocess.call(('open', output_path))
            elif platform.system() == 'Windows':
                os.startfile(output_path)
            else:
                subprocess.call(('xdg-open', output_path))
                
            return {
                "status": "sucesso",
                "referencia": f"VENDA_FAKE_{venda_id}",
                "chave": "43260800000000000000650010000000011000000001",
                "caminho_xml": "",
                "caminho_danfe": output_path,
                "status_sefaz": "autorizada_fake"
            }
        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}

    def consultar_nfce(self, referencia: str) -> dict:
        """Consulta o status de uma NFC-e previamente enviada."""
        try:
            url = f"{self.base_url}/nfce/{referencia}"
            response = requests.get(url, auth=(self.token, ""), timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    "status": data.get("status"),
                    "caminho_xml": data.get("caminho_xml_nota_fiscal"),
                    "caminho_danfe": data.get("caminho_danfe")
                }
            return {"status": "erro_consulta", "mensagem": data.get("mensagem", "Erro ao consultar.")}
        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}

    def _montar_payload(self, itens: list, pagamentos: list, total: float) -> dict:
        """
        Monta o JSON no padrão exigido pela Focus NFe.
        Regra assumida: Empresa optante pelo Lucro Presumido (ME), venda consumidor final.
        """
        
        # Mapeamento interno para códigos de pagamento da SEFAZ
        sefaz_pagamentos = {
            "dinheiro": "01",
            "credito": "03",
            "debito": "04",
            "crediario": "05",
            "pix": "17"
        }

        itens_payload = []
        for i, item in enumerate(itens, start=1):
            # Para Lucro Presumido, usar CST padrão (ex: 00 - Tributada Integralmente) 
            # na vida real isso viria do cadastro do produto
            itens_payload.append({
                "numero_item": i,
                "codigo_produto": str(item["produto_id"]),
                "descricao": item.get("nome", "PRODUTO DIVERSO"),
                "cfop": "5102", # Venda de mercadoria adquirida de terceiros no estado
                "unidade_comercial": "UN",
                "quantidade_comercial": item["quantidade"],
                "valor_unitario_comercial": item["preco_unitario"],
                "unidade_tributavel": "UN",
                "quantidade_tributavel": item["quantidade"],
                "valor_unitario_tributavel": item["preco_unitario"],
                "valor_bruto": item["quantidade"] * item["preco_unitario"],
                
                # Impostos (Simulação Lucro Presumido - ICMS 18%)
                "icms_situacao_tributaria": "00",
                "icms_origem": "0",
                "icms_modalidade_base_calculo": "3",
                "icms_base_calculo": item["quantidade"] * item["preco_unitario"],
                "icms_aliquota": "18.00",
                "icms_valor": (item["quantidade"] * item["preco_unitario"]) * 0.18,
                
                "pis_situacao_tributaria": "07", # Operação Isenta de PIS
                "cofins_situacao_tributaria": "07" # Operação Isenta de COFINS
            })

        pagamentos_payload = []
        for p in pagamentos:
            pagamentos_payload.append({
                "forma_pagamento": sefaz_pagamentos.get(p["forma"], "01"),
                "valor_pagamento": p["valor"]
            })

        payload = {
            "natureza_operacao": "Venda de Mercadoria",
            "data_emissao": datetime.now().isoformat(),
            "tipo_documento": "1", # 1=Saída
            "local_destino": "1", # 1=Operação interna (dentro do estado)
            "finalidade_emissao": "1", # 1=Normal
            "consumidor_final": "1", # 1=Sim
            "presenca_comprador": "1", # 1=Operação presencial
            "cnpj_emitente": self.cnpj_emitente,
            "itens": itens_payload,
            "pagamentos": pagamentos_payload
        }
        
        return payload
