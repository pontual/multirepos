import xlrd
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from movimento.models import Chegando
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Create encomendas from UploadedFile f.
    f is a user-generated sheet
    [Encomendas | Container | Quantidade]
    [codigo     | container | qtde]
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(0, 0).value

    if typecheck != "Encomendas":
        response_err += "Planilha nao parece ser Encomendas. Celula A1 deve ser 'Encomendas'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response
    
    # columns
    CODIGO = 0
    NOME = 1
    QTDE = 2

    # delete all (since sheet can change arbitrarily)
    Chegando.objects.all().delete()
    

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
            qtde = int(sheet.cell(ROW, QTDE).value)

            try:
                produto = Produto.objects.get(codigo=codigo)
                print(produto, nome, qtde)
                chegando = Chegando.objects.create(produto=produto, nome=nome, qtde=qtde)
                response += "{} saved\n".format(codigo)
            except:
                response_err += "Could not find produto {}\n".format(codigo)

    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('encomendas')

    return response_err + "</pre>" + response
