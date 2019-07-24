import xlrd
from django.db import IntegrityError, transaction

from fichas.models import Produto, Atualizado
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Update ativos from UploadedFile f.
    f is user-generated, one codigo per row 
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows
    
    # columns
    CODIGO = 0

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
                
            # Update codigo
            try:
                updated = Produto.objects.filter(codigo=codigo).update(inativo=False)
                if not updated:
                    response_err += "{} not found, skipping\n".format(codigo)
                else:
                    response += "{} updated\n".format(codigo)
            
            except IntegrityError:
                response_err += "IntegrityError in adding or updating {} \n".format(codigo)
    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('ativos')

    return response_err + "</pre>" + response
