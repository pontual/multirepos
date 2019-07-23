import re
import xlrd
from datetime import date
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado

@transaction.atomic
def create(f):
    """Create produtos from UploadedFile f"""
    response = ""
    response_err = ""
    
    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows
    
    # columns
    CODIGO = 0
    NOME = 2
    CAIXA = 11
    PRECO = 8

    # valid_codigo_pat = re.compile(r'\d{6}[A-Z]{0,2}$')
    valid_codigo_pat = re.compile(r'\w{5,8}$')
    
    response += "<pre>"
    response_err += "<pre style='color: red;'>"
    
    for ROW in range(rows):
        codigoCellValue = sheet.cell(ROW, CODIGO).value
        if isinstance(codigoCellValue, str):
            codigo = codigoCellValue
        else:
            codigo = str(int(codigoCellValue))
            
        nome = sheet.cell(ROW, NOME).value

        try:
            caixa = int(sheet.cell(ROW, CAIXA).value)
            preco = Decimal(str(sheet.cell(ROW, PRECO).value))
        except ValueError:
            response_err += "Row {}: Invalid caixa and preco values\n".format(ROW)
            continue

        # check if codigo is valid
        if not valid_codigo_pat.match(codigo):
            response_err += "{} is not a valid codigo\n".format(codigo)
            continue

        # add codigo
        try:
            produto, created = Produto.objects.update_or_create(codigo=codigo, defaults={'nome': nome, 'caixa': caixa, 'preco': preco})
            if created:
                response += "{} saved\n".format(codigo)
            else:
                response += "{} already exists, updating\n".format(codigo)
        except IntegrityError:
            response_err += "IntegrityError in adding or updating {} \n".format(codigo)
    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('produto')
        
    return response_err + "</pre>" + response
