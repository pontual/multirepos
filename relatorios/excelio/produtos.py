import xlrd
from datetime import date
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Create produtos from UploadedFile f.
    f is Relatorios > Produtos > Precos e Quantidades
    """
    response = "<pre>"
    response_err = "<div style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 1).value

    if typecheck != "Relatório Preço Unitário e Estoque":
        response_err += "Planilha nao parece ser Preco e Quantidades. Celula B2 deve ser 'Relatorio Preco Unitário e Estoque'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</div>" + response
    
    # columns
    CODIGO = 0
    NOME = 1

    for ROW in range(rows):
        codigoCellValue = sheet.cell(ROW, CODIGO).value
        if isinstance(codigoCellValue, str):
            codigo = codigoCellValue
        else:
            codigo = str(int(codigoCellValue))

        if valid_codigo_pat.match(codigo):
            # bug in loja virtual
            if codigo == "140975":
                codigo = "140975E"
                
            nome = str(sheet.cell(ROW, NOME).value)
            produto, created = Produto.objects.update_or_create(codigo=codigo, defaults={'nome': nome})
            if created:
                response += "{} saved\n".format(codigo)
            else:
                response += "{} exists, updating\n".format(codigo)

    return response_err + "</div>" + response
