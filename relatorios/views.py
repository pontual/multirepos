from datetime import date, timedelta, datetime

from django.shortcuts import render, redirect
from django.db import transaction
from django.db.models import Sum

from fichas.models import Produto, Atualizado
from movimento.models import Chegando, Compra, ItemPedido
from .forms import UploadExcelForm, UploadTwoExcelsForm, PreliminaryReportForm
from .excelio import produtos as xlprodutos
from .excelio import estoques as xlestoques
from .excelio import caixas as xlcaixas
from .excelio import ativos as xlativos
from .excelio import containers as xlcontainers
from .excelio import pedidos as xlpedidos
from .excelio import itenspedidos as xlitenspedidos
from .excelio import encomendas as xlencomendas


def dataAtualizado(tipo):
    try:
        data = Atualizado.objects.get(tipo=tipo).data.strftime("%d/%m")
    except Atualizado.DoesNotExist:
        data = "--"
    return data


def fileUploadView(request, callback, formTemplate, templateVars):
    # https://docs.djangoproject.com/en/1.11/topics/http/file-uploads/
    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            response = callback(request.FILES['file'])
            return render(request, 'relatorios/result.html', {'response': response})
    else:
        form = UploadExcelForm()
        templateVars.update({'form': form})
        return render(request, formTemplate, templateVars)


def fileUploadTwoView(request, callback, formTemplate, templateVars):
    if request.method == "POST":
        form = UploadTwoExcelsForm(request.POST, request.FILES)
        if form.is_valid():
            response = callback(request.FILES['file1'], request.FILES['file2'])
            return render(request, 'relatorios/result.html', {'response': response})
    else:
        form = UploadTwoExcelsForm()
        templateVars.update({'form': form})
        return render(request, formTemplate, templateVars)
    
    
def index(request):
    # tipos = ["produtos", "caixas", "ativos", "estoques", "containers", "pedidos", "itenspedidos", "encomendas"]
    # atualizados = { t: dataAtualizado(t) for t in tipos }
    return render(request, 'relatorios/index.html')


def formDescription(request, tipo, callback):
    return fileUploadView(request, callback, 'relatorios/' + tipo + '.html', {'tipo': tipo, 'data': dataAtualizado(tipo)})


def produtos(request):
    return formDescription(request, "produtos", xlprodutos.create)
 

def caixas(request):
    return formDescription(request, "caixas", xlcaixas.create)


def ativos(request):
    return formDescription(request, "ativos", xlativos.create)


def estoques(request):
    return fileUploadTwoView(request, xlestoques.create, 'relatorios/estoques.html', {'tipo': 'estoques', 'data': dataAtualizado('estoques')})


def containers(request):
    return formDescription(request, "containers", xlcontainers.create)


def pedidos(request):
    return formDescription(request, "pedidos", xlpedidos.create)


def itenspedidos(request):
    return formDescription(request, "itenspedidos", xlitenspedidos.create)


def encomendas(request):
    return formDescription(request, "encomendas", xlencomendas.create)


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


def totalChegando(produto):
    produtoChegandos = Chegando.objects.filter(produto=produto)
    total = 0
    for pc in produtoChegandos:
        total += pc.qtde
    return total


def verificar(request):
    if request.method == "POST":
        form = PreliminaryReportForm(request.POST)
        if form.is_valid():
            return preliminaryReport(request, form.cleaned_data['codigos'])
    else:
        form = PreliminaryReportForm()
        warnings = ""
        produtos = Produto.objects.all()
        for p in produtos:
            if p.disp < 0 or p.resv < 0:
                warnings += f"{p.codigo} has negative estoque\n"
            if not p.inativo:
                if p.cx < 1:
                    warnings += f"{p.codigo} has 0 cx\n"

        atualizados = {at.tipo: at.data for at in Atualizado.objects.all()}

        containers_chegaram = list(Compra.objects.order_by('-container').values_list('container').distinct()[:3])
        containers_chegaram = [item[0] for item in containers_chegaram[::-1]]

        containers_vao_chegar = list(Chegando.objects.order_by('nome').values_list('nome').distinct()[:5])
        containers_vao_chegar = [item[0] for item in containers_vao_chegar]

        return render(request, 'relatorios/verificar.html',
                      {'form': form,
                       'warnings': warnings,
                       'atualizados': atualizados,
                       'containers_chegaram': containers_chegaram,
                       'containers_vao_chegar': containers_vao_chegar,
                      })


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

        blocks.append({'codigo': codigo,
                       'nome': produto.nome.title(),
                       'chegando': reportChegando(produto),
                       'totalVendasLastYear': totalVendasLastYear,
                       'totalVendasThisYear': totalVendasThisYear,
                       'disp': produto.disp,
                       'resv': produto.resv,
                       'ultcont': ultcont,
        })
        
    return blocks


def preliminaryReport(request, codigoBangs):
    blocks, response_err = getBlocks(codigoBangs)
    thisyr = int(datetime.strftime(date.today(), "%Y"))
    lastyr = thisyr - 1

    return render(request, 'relatorios/preliminaryReport.html', { 'err': response_err, 'blocks': blocks, 'thisyr': thisyr, 'lastyr': lastyr })
    

def xlsReport(request):
    if request.method == "POST":
        selected = request.POST.getlist('selected_cod')
        blocks = getXlsBlocks(selected)
        # Create Excel file 
        return render(request, 'relatorios/xlsReport.html', {"blocks": blocks})
    else:
        return redirect('relatorios:verificar')
