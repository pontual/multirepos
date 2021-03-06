import xlrd
from datetime import date, datetime
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Create Update  from UploadedFile f.
    f is  > 
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 1).value

    if typecheck != "":
        response_err += "Planilha nao parece ser . Celula  deve ser ''"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response
    
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
                
            obj, created = OBJ.objects.update_or_create(codigo=codigo, defaults={'nome': nome})
            if created:
                response += "{} saved\n".format(codigo)
            else:
                response += "{} exists, updating\n".format(codigo)

                
            # Update codigo
            try:
                updated = Produto.objects.filter(codigo=codigo).update(estoque_disp=disp, estoque_resv=resv, estoque_last_updated=today)
                if not updated:
                    response_err += "{} not found, skipping\n".format(codigo)
                else:
                    response += "{} updated\n".format(codigo)
            
            except IntegrityError:
                response_err += "IntegrityError in adding or updating {} \n".format(codigo)
    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('CATEGORIES')

    return response_err + "</pre>" + response
