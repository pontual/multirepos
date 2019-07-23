import re
import xlrd
from datetime import date
from django.db import IntegrityError, transaction

from decimal import Decimal
from fichas.models import Produto, Atualizado

@transaction.atomic
def create(f):
    """Create ITEM from UploadedFile f.
    f is Relatorios > Produtos > 
    """
    response = "<pre>"
    response_err = "<div style='color: red;'>"

    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)

    rows = sheet.nrows

    typecheck = sheet.cell(1, 1).value

    assert typecheck == "SHEET NAME"
    
    # columns
    CODIGO = 0
    NOME = 1

    return response_err + "</div>" + response
