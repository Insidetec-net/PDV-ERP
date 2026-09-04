import os
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPainter, QFont, QImage, QPageSize, QPageLayout
from PyQt6.QtCore import QSizeF, Qt, QRectF, QMarginsF

class BarcodeService:
    """
    Serviço responsável pela geração de Código de Barras
    e layout de impressão para impressoras térmicas.
    """

    @staticmethod
    def gerar_pdf_etiquetas_termicas(produtos: list, output_path: str):
        """
        Gera um PDF formatado para impressora térmica 40x30mm.
        produtos: Lista de dicts [{'nome', 'preco', 'codigo', 'quantidade'}]
        """
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        
        # Etiqueta Térmica: 40mm x 30mm
        page_size = QPageSize(QSizeF(40, 30), QPageSize.Unit.Millimeter)
        layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, QMarginsF(0.5, 0.5, 0.5, 0.5))
        printer.setPageLayout(layout)

        painter = QPainter()
        painter.begin(printer)
        
        first_page = True
        
        for prod in produtos:
            codigo = str(prod.get('codigo', '')).strip()
            nome = str(prod.get('nome', '')).strip()
            preco = float(prod.get('preco', 0.0))
            quantidade = int(prod.get('quantidade', 1))
            
            if not codigo:
                continue

            try:
                ean = barcode.get('ean13', codigo, writer=ImageWriter())
            except barcode.errors.BarcodeNotFoundError:
                ean = barcode.get('code128', codigo, writer=ImageWriter())
                
            fp = BytesIO()
            options = {
                'module_width': 0.15,
                'module_height': 5.0,
                'quiet_zone': 0.5,
                'font_size': 7,
                'text_distance': 3.0,
                'background': 'white',
                'foreground': 'black',
                'write_text': True,
                'dpi': 300
            }
            ean.write(fp, options)
            fp.seek(0)
            img = QImage.fromData(fp.read(), 'PNG')
            
            for _ in range(quantidade):
                if not first_page:
                    printer.newPage()
                first_page = False
                
                rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                
                font_titulo = QFont('Arial', 6, QFont.Weight.Normal)
                painter.setFont(font_titulo)
                titulo_rect = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.15)
                painter.drawText(titulo_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, 'SISTEMA MEU BAZAR')
                
                font_nome = QFont('Arial', 7, QFont.Weight.Bold)
                painter.setFont(font_nome)
                nome_rect = QRectF(rect.x(), rect.y() + (rect.height() * 0.15), rect.width(), rect.height() * 0.25)
                painter.drawText(nome_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, nome[:40])
                
                font_preco = QFont('Arial', 14, QFont.Weight.Black)
                painter.setFont(font_preco)
                preco_rect = QRectF(rect.x(), rect.y() + (rect.height() * 0.40), rect.width(), rect.height() * 0.25)
                texto_preco = f'R$ {preco:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                painter.drawText(preco_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, texto_preco)
                
                barcode_rect = QRectF(rect.x() + (rect.width()*0.02), rect.y() + (rect.height() * 0.65), rect.width()*0.96, rect.height() * 0.35)
                painter.drawImage(barcode_rect, img)
                
        painter.end()
        return True
