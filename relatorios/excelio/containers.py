import xlrd
from datetime import datetime
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from movimento.models import Compra
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Create Compra from UploadedFile f.
    f is Loja Virtual > Secao PAC > Escolha o container > Clique em Imprimir
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(0, 4).value

    if typecheck != "Fornecedor":
        response_err += "Planilha nao parece ser Container. Celula E1 deve ser 'Fornecedor'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response
    
    # columns
    CONTAINER_ROW = 0
    CONTAINER_COL = 14

    DATA_ROW = 4
    DATA_COL = 17
    
    CODIGO = 1
    QTDE = 12

    compraNome = sheet.cell(CONTAINER_ROW, CONTAINER_COL).value
    compraDataRaw = sheet.cell(DATA_ROW, DATA_COL).value
    compraData = datetime.strptime(compraDataRaw, "%d/%m/%Y").strftime("%Y-%m-%d")
    
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
                
            try:
                produto = Produto.objects.get(codigo=codigo)
            except:
                response_err += "Could not find produto {}, aborting\n".format(codigo)
                break

            try:
                qtde = int(sheet.cell(ROW, QTDE).value)
            except ValueError:
                response_err += "Could not read codigo {}'s qtde. Skipping\n".format(codigoCellValue)
                continue
            
            compra, compraCreated = Compra.objects.update_or_create(data=compraData, container=compraNome, produto=produto, defaults={'qtde': qtde})
            if compraCreated:
                response += "{} saved\n".format(codigo)
            else:
                response += "{} exists, updating\n".format(codigo)

    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('containers')

    return response_err + "</pre>" + response
