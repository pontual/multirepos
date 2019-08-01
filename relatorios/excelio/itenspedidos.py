import xlrd
from datetime import date, datetime
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado
from movimento.models import Pedido, ItemPedido
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Create item pedido from UploadedFile f.
    f is Relatorios > Vendas > Por Produto > Analitico
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 2).value

    if typecheck[:19] == "Relatório de Vendas":
        # columns
        NUMERO = 1
        CODIGO_PRODUTO = 2
        QTDE = 7
        empresa_cell = sheet.cell(0, 2).value
        empresa = empresa_cell.split()[0][:3]
        
    else:
        response_err += "Planilha nao parece ser Produto - analitico. Celula C2 deve ser 'Relatório de Vendas'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response


    skipuniao = set()
    skippontual = set()
    
    for ROW in range(rows):
        numeroCellValue = sheet.cell(ROW, NUMERO).value

        if isinstance(numeroCellValue, str):
            continue

        try:
            numero = int(numeroCellValue)
        except ValueError:
            response_err += "Could not read numero {}. Skipping\n".format(numeroCellValue)
            continue

        try:
            pedido = Pedido.objects.get(empresa_numero=empresa + "_" + str(numero))
            response += "Processing pedido {}\n".format(numero)
        except Pedido.DoesNotExist:
            response_err += "Could not find pedido {}, aborting\n".format(numero)
            break

        if pedido.cliente.startswith("UNIAO BRINDES IMPORT"):
            skipuniao.add(numero)
        elif pedido.cliente.startswith("PONTUAL EXPORT"):
            skippontual.add(numero)
        else:
            produtoCellValue = sheet.cell(ROW, CODIGO_PRODUTO).value
            if isinstance(produtoCellValue, str):
                codigoProduto = produtoCellValue
            else:
                codigoProduto = str(int(produtoCellValue))

            if codigoProduto == "DESC":
                continue

            if codigoProduto == "140975":
                codigoProduto = "140975E"

            try:
                produto = Produto.objects.get(codigo=codigoProduto)
            except Produto.DoesNotExist:
                response_err += "Could not find produto {}, aborting\n".format(codigoProduto)
                break

            qtdeCellValue = sheet.cell(ROW, QTDE).value
            if isinstance(qtdeCellValue, str):
                continue
            qtde = int(qtdeCellValue)

            # create itemPedido
            item, itemCreated = ItemPedido.objects.update_or_create(pedido=pedido, produto=produto, defaults={'qtde': qtde})
            if itemCreated:
                response += "Created item {} {}\n".format(numero, codigoProduto)
            else:
                response += "Item {} {} exists, updating\n".format(numero, codigoProduto)

    for n in skipuniao:
        response_err += "Pedido " + str(n) + " is Uniao, skipping\n"
    for n in skippontual:
        response_err += "Pedido " + str(n) + " is Pontual, skipping\n"

    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('itenspedidos')

    return response_err + "</pre>" + response
