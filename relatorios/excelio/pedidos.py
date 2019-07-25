import xlrd
from datetime import date, datetime
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Atualizado
from movimento.models import Pedido
from .patterns import valid_codigo_pat


@transaction.atomic
def create(f):
    """Create pedido from UploadedFile f.
    f is Relatorios > Vendas > Por Numero > Sintetico
    """
    response = "<pre>"
    response_err = "<pre style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 1).value
    typecheck2 = sheet.cell(1, 2).value

    if typecheck[:18] == "Vendas - Sintético":
        # columns
        NUMERO = 1
        CLIENTE = 2
        DATA = 5
        empresa_cell = sheet.cell(0, 1).value
        empresa = empresa_cell.split()[0][:3]
        
    elif typecheck2[:18] == "Vendas - Sintético":
        # columns
        NUMERO = 1
        CLIENTE = 3
        DATA = 6
        empresa_cell = sheet.cell(0, 2).value
        empresa = empresa_cell.split()[0][:3]

    else:
        response_err += "Planilha nao parece ser Numero - sintetico. Celula B2 deve ser 'Vendas - Sintético'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</pre>" + response


    for ROW in range(rows):
        numeroCellValue = sheet.cell(ROW, NUMERO).value

        if isinstance(numeroCellValue, str):
            continue

        try:
            numero = int(numeroCellValue)
        except ValueError:
            response_err += "Could not read numero {}. Skipping\n".format(numeroCellValue)
            continue

        nomeCliente = sheet.cell(ROW, CLIENTE).value
        response += "Cliente {}\n".format(nomeCliente)

        dataValue = sheet.cell(ROW, DATA).value

        data = datetime.strptime(dataValue, "%d/%m/%Y").strftime("%Y-%m-%d")
        response += "Data {}\n".format(data)

        pedido, pedidoCreated = Pedido.objects.update_or_create(empresa_numero=empresa + "_" + str(numero), defaults={'cliente': nomeCliente, 'data': data})
        if pedidoCreated:
            response += "{} saved\n".format(numero)
        else:
            response += "{} already exists, updating\n".format(numero)    

    else:        
        response += "ALL OK\n"
        Atualizado.atualizar('pedidos')

    return response_err + "</pre>" + response
