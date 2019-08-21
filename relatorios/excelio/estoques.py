import xlrd
from datetime import date
from django.db import IntegrityError, transaction
from django.db.models import F

from decimal import Decimal
from fichas.models import Produto, Atualizado
from .patterns import valid_codigo_pat
from .uniadj import uniadj

@transaction.atomic
def create(f, f2):
    """Update estoques from UploadedFile f.
    f is Relatorios > Produtos > Conferencia de Estoque
    f2 is the second Relatorios > Produtos > Conferencia de Estoque
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
    
    book2 = xlrd.open_workbook(file_contents=f2.read())
    sheet2 = book2.sheet_by_index(0)

    rows2 = sheet2.nrows

    typecheck2 = sheet2.cell(1, 2).value

    if typecheck2 != "Relatório de Produtos":
        response_err += "Planilha2 nao parece ser Conferencia de Estoque. Celula C2 deve ser 'Relatório de Produtos'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response

    # columns
    CODIGO = 0
    DISP = 5
    RESV = 8

    today = date.today()

    # reset all estoque to 0
    Produto.objects.update(disp=0, resv=0)
    
    # process f
    
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

            disp = int(sheet.cell(ROW, DISP).value)
            resv = int(sheet.cell(ROW, RESV).value)

            if disp < 0:
                disp = 0
            if resv < 0:
                resv = 0
                
            # Update codigo
            try:
                updated = Produto.objects.filter(codigo=codigo).update(disp=F('disp')+disp, resv=F('resv')+resv, estoque_last_updated=today)
                if not updated:
                    response_err += "{} not found, skipping\n".format(codigo)
                else:
                    response += "{} updated\n".format(codigo)
            
            except IntegrityError:
                response_err += "IntegrityError in adding or updating {} \n".format(codigo)

    else:        
        response += "File f ALL OK\n"
                
    # process f2
    
    for ROW in range(rows2):
        codigoCellValue = sheet2.cell(ROW, CODIGO).value
        if isinstance(codigoCellValue, str):
            codigo = codigoCellValue
        else:
            codigo = str(int(codigoCellValue))

        if valid_codigo_pat.match(codigo):
            # bug in loja virtual
            if codigo == "140975":
                codigo = "140975E"

            # try:
            #     adj = uniadj[codigo]
            # except KeyError:
            #     if codigo < "143312":
            #         response_err += "{} not found in uniadj\n".format(codigo)
                
            disp = int(sheet2.cell(ROW, DISP).value)
            resv = int(sheet2.cell(ROW, RESV).value) - adj

            if disp < 0:
                disp = 0
            if resv < 0:
                resv = 0

            # Update codigo
            try:
                updated = Produto.objects.filter(codigo=codigo).update(disp=F('disp')+disp, resv=F('resv')+resv, estoque_last_updated=today)
                if not updated:
                    response_err += "{} not found, skipping\n".format(codigo)
                else:
                    response += "{} updated\n".format(codigo)
            
            except IntegrityError:
                response_err += "IntegrityError in adding or updating {} \n".format(codigo)
    else:        
        response += "File f2 ALL OK\n"
        Atualizado.atualizar('estoques')

    return response_err + "</pre>" + response
