import xlrd
from datetime import date
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Update estoques from UploadedFile f.
    f is Relatorios > Produtos > Conferencia de Estoque
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 2).value

    if typecheck != "Relatório de Produtos":
        response_err += "Planilha nao parece ser Conferencia de Estoque. Celula C2 deve ser 'Relatório de Produtos'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response
    
    # columns
    CODIGO = 0
    NOME = 1
    DISP = 5
    RESV = 8

    today = date.today()
    
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
            disp = int(sheet.cell(ROW, DISP).value)
            resv = int(sheet.cell(ROW, RESV).value)
                
            produto, created = Produto.objects.update_or_create(codigo=codigo, defaults={'nome': nome, 'disp': disp, 'resv': resv, 'estoque_last_updated': today})
            
            if created:
                response += "{} saved\n".format(codigo)
            else:
                response += "{} exists, updating\n".format(codigo)

    return response_err + "</pre>" + response
