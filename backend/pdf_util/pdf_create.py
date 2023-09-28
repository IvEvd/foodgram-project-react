from io import BytesIO
from django.http import FileResponse

from reportlab.lib import colors
from reportlab.lib.units import mm, inch, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultPageSize

pdfmetrics.registerFont(TTFont('DejaVuSerif', 'pdf_util/DejaVuSerif.ttf'))


PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
styles = getSampleStyleSheet()


class PdfCreator():
    """Класс для создания pdf."""

    def __init__(self, Title, pageinfo, data) -> None:
        """init метод класса."""
        super().__init__()

        self.Title = Title
        self.pageinfo = pageinfo
        self.data = data

    def create_pdf_with_table(self, data):
        """Создать pdf с таблицей."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=(21*cm, 29.7*cm))
        table = Table(data, colWidths=[9*cm, 4*cm, 3.5*cm])
        table_style = ([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (0, -1), 0.5*cm),  # Отступ левого края первого столбца
            ('RIGHTPADDING', (-1, 0), (-1, -1), 0.5*cm),  # Отступ правого края последнего столбца
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.5*cm),  # Расстояние между столбцами
        ])
        table_style.extend(
            [('ALIGN', (0, 0), (0, -1), 'LEFT'), ]  #Выравнивание для второй колонки
        )
        elements = [table]
        table.setStyle(TableStyle(table_style))
        doc.build(elements,
                  onFirstPage=self.myFirstPage,
                  onLaterPages=self.myLaterPages
                  )
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True,
            filename='shopping-list.pdf'
        )

    def myFirstPage(self, canvas, doc):
        """Первая страница списка покупок с заголовком."""
        canvas.saveState()
        canvas.setFont('DejaVuSerif', 16)
        canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-54, self.Title)
        canvas.setFont('DejaVuSerif', 9)
        canvas.drawString(inch, 0.75 * inch, "First Page / %s" % self.pageinfo)
        canvas.restoreState()

    def myLaterPages(self, canvas, doc):
        """Вторая и следующие страницы списка покупок."""
        canvas.saveState()
        canvas.setFont('DejaVuSerif', 9)
        canvas.drawString(inch, 0.75 * inch,
                          "Page %d %s" % (doc.page, self.pageinfo)
                          )
        canvas.restoreState()
