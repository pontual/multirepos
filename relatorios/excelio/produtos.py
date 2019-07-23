import re
import xlrd
from datetime import date
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado

@transaction.atomic
def create(f):
    """Create produtos from UploadedFile f.
    f is Relatorios > Produtos > Precos e Quantidades
    """
    response = "<pre>"
    response_err = "<div style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 1).value

    if typecheck != "Relatório Preço Unitário e Estoque":
        response_err += "Planilha nao parece ser Preco e Quantidades. Celula B2 deve ser 'Relatorio Preco Unitário e Estoque'"
        response += "<a href='javascript:window.history.back();'>Voltar</a>"
        return response_err + "</div>" + response
    
    # columns
    CODIGO = 0
    NOME = 1
    CAIXA = 11
    PRECO = 8

    valid_codigo_pat = re.compile(r'\d{5,6}[A-Za-z]{0,2}$')

    for ROW in range(rows):
        pass

    response = "Dummy response"
    response_err += "Dummy error"
    return response_err + "</div>" + response
