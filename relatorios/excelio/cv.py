import xlrd
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from movimento.models import Produto
from .patterns import valid_codigo_pat

@transaction.atomic
def create(f):
    """Create cvs from UploadedFile f.
    f is Relatorios > Produtos > Precos e Qtdes
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 1).value

    if typecheck != "Relatório Preço Unitário e Estoque":
        response_err += "Planilha nao parece ser Precos e Qtdes. Celula B2 deve ser 'Relatório Preço Unitário e Estoque'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response
    
    # columns
    CODIGO = 0
    CV = 5
    
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
                
            cv = str("%.2f" % sheet.cell(ROW, CV).value).replace(".", ",")
            
            try:
                produto = Produto.objects.get(codigo=codigo)
                produto.cv = cv
                produto.save()

            except Produto.DoesNotExist:
                response_err += "{} does not exist\n".format(codigo)
            
            response += "{} saved\n".format(codigo)

    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('encomendas')

    return response_err + "</pre>" + response
