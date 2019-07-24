import xlrd
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Update caixas from UploadedFile f.
    f is Movimento > Lista de precos > Lista Geral - Ativos
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 3).value

    if typecheck != "Lista Geral de Preços - Ativos":
        response_err += "Planilha nao parece ser Lista Geral. Celula D2 deve ser 'Lista Geral de Preços - Ativos'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response
    
    # columns
    CODIGO = 0
    CAIXA = 11

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

            caixa = int(sheet.cell(ROW, CAIXA).value)
            
            # Update codigo
            try:
                updated = Produto.objects.filter(codigo=codigo).update(cx=caixa)
                if not updated:
                    response_err += "{} not found, skipping\n".format(codigo)
                else:
                    response += "{} updated\n".format(codigo)
            
            except IntegrityError:
                response_err += "IntegrityError in adding or updating {} \n".format(codigo)
    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('caixas')
                
    return response_err + "</pre>" + response
