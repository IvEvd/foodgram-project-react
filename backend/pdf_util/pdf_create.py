"""Создание pdf документа с таблицей."""
from io import BytesIO
from django.http import FileResponse

from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Spacer,
    SimpleDocTemplate,
    Table,
    TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.rl_config import defaultPageSize

pdfmetrics.registerFont(TTFont('DejaVuSerif', 'pdf_util/DejaVuSerif.ttf'))


PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
styles = getSampleStyleSheet()


class PdfCreator():
    """Класс для создания pdf."""

    def __init__(self, Title, pageinfo, data) -> None:
        """Init метод класса."""
        super().__init__()

        self.Title = Title
        self.pageinfo = pageinfo
        self.data = data

    def create_pdf_with_table(self, data):
        """Создать pdf с таблицей."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=(21 * cm, 29.7 * cm))
        Story = [Spacer(1, 2 * inch)]
        table = Table(
            data,
            colWidths=[9 * cm, 4 * cm, 3.5 * cm],
            rowHeights=30,
            spaceBefore=50
        )
        table_style = ([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('LEADING', (0, 0), (-1, -1), 24),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('LEFTPADDING', (0, 0), (0, -1), 0.5 * cm),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 0.5 * cm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.5 * cm),
        ])
        table_style.extend(
            [('ALIGN', (0, 0), (0, -1), 'LEFT'), ]
        )
        table.setStyle(TableStyle(table_style))

        Story.append(table)

        doc.build(Story,
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
        canvas.drawCentredString(
            PAGE_WIDTH / 2.0, PAGE_HEIGHT - 108, self.Title
        )
        canvas.setFont('DejaVuSerif', 9)
        canvas.drawString(inch, 0.75 * inch, "First Page / %s" % self.pageinfo)
        canvas.restoreState()

    def myLaterPages(self, canvas, doc):
        """Вторая и следующие страницы списка покупок."""
        canvas.saveState()
        canvas.setFont('DejaVuSerif', 16)
        canvas.drawCentredString(
            PAGE_WIDTH / 2.0, PAGE_HEIGHT - 54, self.Title
        )
        canvas.setFont('DejaVuSerif', 9)
        canvas.drawString(
            inch, 0.75 * inch, "Page %d %s" % (doc.page, self.pageinfo),
        )
        canvas.restoreState()
