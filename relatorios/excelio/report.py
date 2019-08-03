from datetime import date, timedelta, datetime

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.writer.excel import save_virtual_workbook

from django.db import transaction
from django.db.models import Sum

from fichas.models import Produto
from movimento.models import Chegando, Compra, Pedido, ItemPedido


def reportChegando(produto):
    produtoChegandos = Chegando.objects.filter(produto=produto)
    lenProdutoChegando = len(produtoChegandos)
    chegandoDisplay = ""
    if lenProdutoChegando > 0:
        for i, pc in enumerate(produtoChegandos):
            chegandoDisplay += "{} ({})".format(str(pc.qtde), pc.nome)
            if i != lenProdutoChegando - 1:
                chegandoDisplay += ", "
    else:
        chegandoDisplay = "0"
    return chegandoDisplay


def chegandoList(produto):
    produtoChegandos = Chegando.objects.filter(produto=produto)
    lenProdutoChegando = len(produtoChegandos)
    out = []
    if lenProdutoChegando > 0:
        for i, pc in enumerate(produtoChegandos):
            out.append("Chegando - {} ({})".format(fmtThousands(pc.qtde), pc.nome))
    return out


def totalChegando(produto):
    produtoChegandos = Chegando.objects.filter(produto=produto)
    total = 0
    for pc in produtoChegandos:
        total += pc.qtde
    return total


@transaction.atomic
def getBlocks(codigoBangs):
    """A bang! is an exclamation point used to mark codigos that
    should be checked manually"""
    
    # load everything into memory, there isn't that much data
    codigoBangs = list(map(str.upper, codigoBangs.split()))
    
    today = date.today()
    thisYear = today.year
    lastYear = thisYear - 1
    
    oneYearAgo = today - timedelta(days=365)
    lastYearBegin = date(lastYear, 1, 1)
    thisYearBegin = date(thisYear, 1, 1)
    startDate = lastYearBegin

    allVendas = ItemPedido.objects.filter(pedido__data__gte=startDate)
    vendas365 = allVendas.filter(pedido__data__gte=oneYearAgo)
    vendasLastYear = allVendas.filter(pedido__data__gte=lastYearBegin, pedido__data__lt=thisYearBegin)
    vendasThisYear = allVendas.filter(pedido__data__gte=thisYearBegin)

    response_err = ""
    thisyr = int(datetime.strftime(date.today(), "%Y"))
    lastyr = thisyr - 1

    blocks = []
    
    for codigo in codigoBangs:
        if not Produto.objects.filter(codigo=codigo).exists():
            response_err += "Warning: codigo {} not found\n".format(codigo)

    MONTH_AVG_FACTOR = 7

    for produto in Produto.objects.filter(inativo=False).order_by('codigo'):
        codigo = produto.codigo
        codigoDisplay = codigo
        if codigo in codigoBangs:
            codigoDisplay += " (!)"
            
        # vendasProdutoAll = allVendas.filter(produto__codigo=codigo)
        totalVendas365 = vendas365.filter(produto__codigo=codigo).aggregate(Sum('qtde')).get('qtde__sum')
        if totalVendas365 is None:
            totalVendas365 = 0
        
        totalVendasLastYear = vendasLastYear.filter(produto__codigo=codigo).aggregate(Sum('qtde')).get('qtde__sum')
        totalVendasThisYear = vendasThisYear.filter(produto__codigo=codigo).aggregate(Sum('qtde')).get('qtde__sum')

        if totalVendasLastYear is None:
            totalVendasLastYear = 0
            
        if totalVendasThisYear is None:
            totalVendasThisYear = 0
            
        # consider last "large" container (>= 5 boxes)
        cx5 = produto.cx * 5
        ultcont = Compra.objects.filter(produto=produto, qtde__gte=cx5).first()
        firstcont = Compra.objects.filter(produto=produto).last()
        if ultcont is None:
            period_back_begin = oneYearAgo
            half = int(cx5 / 2)
        else:
            period_back_begin = max(oneYearAgo, firstcont.data)
            half = int(ultcont.qtde / 4)

        months_back = int(abs((today - period_back_begin).days) / 30)
        months_back = max(1, months_back)

        estoqueTotal = produto.disp + produto.resv
        if vendas365 == 0 or estoqueTotal < half or (totalVendas365 / months_back * MONTH_AVG_FACTOR) > (estoqueTotal + totalChegando(produto)):
            blocks.append({'codigo': codigoDisplay,
                           'nome': produto.nome.title(),
                           'chegando': reportChegando(produto),
                           'totalVendasLastYear': totalVendasLastYear,
                           'totalVendasThisYear': totalVendasThisYear,
                           'ultimoest': produto.ultimo_estoque,
                           'estoque': estoqueTotal,
                           'disp': produto.disp,
                           'resv': produto.resv,
                           'ultcont': ultcont,
            })

        
    return blocks, response_err


@transaction.atomic
def getXlsBlocks(cods):
    today = date.today()
    
    thisYear = today.year
    lastYear = thisYear - 1

    lastYearBegin = date(lastYear, 1, 1)
    thisYearBegin = date(thisYear, 1, 1)
    startDate = lastYearBegin

    allVendas = ItemPedido.objects.filter(pedido__data__gte=startDate)
    vendasLastYear = allVendas.filter(pedido__data__gte=lastYearBegin, pedido__data__lt=thisYearBegin)
    vendasThisYear = allVendas.filter(pedido__data__gte=thisYearBegin)

    thisyr = int(datetime.strftime(date.today(), "%Y"))
    lastyr = thisyr - 1

    blocks = []
    
    for produto in Produto.objects.filter(codigo__in=cods).order_by('codigo'):
        codigo = produto.codigo        
        
        totalVendasLastYear = vendasLastYear.filter(produto__codigo=codigo).aggregate(Sum('qtde')).get('qtde__sum')
        totalVendasThisYear = vendasThisYear.filter(produto__codigo=codigo).aggregate(Sum('qtde')).get('qtde__sum')

        if totalVendasLastYear is None:
            totalVendasLastYear = 0
            
        if totalVendasThisYear is None:
            totalVendasThisYear = 0
            
        cx5 = produto.cx * 5
        ultcont = Compra.objects.filter(produto=produto, qtde__gte=cx5).first()

        if ultcont:
            ultcontStr = "Último container - {} - {} - {} pçs".format(
                datetime.strftime(ultcont.data, "%d/%m/%Y"),
                ultcont.container,
                fmtThousands(ultcont.qtde))
        else:
            ultcontStr = ""
            
        threelargestsales = ItemPedido.objects.filter(produto=produto).order_by('-qtde')[:3]
        threelargest = ["{} - {} pçs - {}".format(s.pedido.data, fmtThousands(s.qtde), s.pedido.cliente) for s in threelargestsales]
        
        blocks.append({'codigo': codigo,
                       'disp': produto.disp,
                       'resv': produto.resv,
                       'nome': produto.nome.title(),
                       'chegando': chegandoList(produto),
                       'chegandoTot': totalChegando(produto),
                       'totalVendasLastYear': totalVendasLastYear,
                       'totalVendasThisYear': totalVendasThisYear,
                       'caixa': produto.cx,
                       'ultcont': ultcontStr,
                       'threelargest': threelargest,
        })
        
    return blocks


def fmtThousands(x):
    return format(x, ',d').replace(',', '.')


def generateXlsReport(blocks):
    wb = Workbook()
    ws = wb.active

    thisyr = int(datetime.strftime(date.today(), "%Y"))
    lastyr = thisyr - 1

    todayStr = datetime.strftime(date.today(), "%d-%m-%Y")
    ws.title = todayStr

    ws.oddHeader.center.text = "Reposição " + todayStr
    ws.evenHeader.center.text = "Reposição " + todayStr
    ws.oddFooter.center.text = "Página &[Page] of &N"
    ws.evenFooter.center.text = "Página &[Page] of &N"
    
    ws.print_title_rows = "1:1"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    arial_font = Font(name="Arial")
    for col in 'ABCDEFG':
        for cell in ws[col+":"+col]:
            cell.font = arial_font
        
    # define title row
    ws['A1'] = "Código"
    ws['B1'] = "Disponível"
    ws['C1'] = "Reservado"
    ws['D1'] = "Chegando"
    ws['E1'] = "Vendas " + str(lastyr)
    ws['F1'] = "Vendas " + str(thisyr)
    ws['G1'] = "Caixa"

    bold_font = Font(bold=True)
    
    for cell in ws["1:1"]:
        cell.font = bold_font
    
    # begin writing data
    row = 2

    for cod in blocks:
        ws['A' + str(row)] = str(cod['codigo'])
        ws['B' + str(row)] = fmtThousands(cod['disp'])
        ws['C' + str(row)] = fmtThousands(cod['resv'])
        ws['D' + str(row)] = fmtThousands(cod['chegandoTot'])
        ws['E' + str(row)] = fmtThousands(cod['totalVendasLastYear'])
        ws['F' + str(row)] = fmtThousands(cod['totalVendasThisYear'])
        ws['G' + str(row)] = fmtThousands(cod['caixa'])

        for cell in ws[str(row) + ":" + str(row)]:
            cell.font = bold_font

        row += 1
        ws['A' + str(row)] = cod['nome']

        if cod['ultcont']:
            row += 1
            ws['A' + str(row)] = cod['ultcont']

        # Sem estoque
        # row += 1
        # ws['A' + str(row)] = cod.semestoque

        for ch in cod['chegando']:
            row += 1
            ws['A' + str(row)] = ch
                       
        for large in cod['threelargest']:
            row += 1
            ws['A' + str(row)] = large

        row += 2

    return save_virtual_workbook(wb)
