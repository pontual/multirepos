from datetime import date, timedelta, datetime
from calendar import monthrange

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db import transaction
from django.db.models import Sum

from fichas.models import Produto, Atualizado
from movimento.models import Chegando, Compra, Pedido, ItemPedido
from .forms import UploadExcelForm, UploadTwoExcelsForm, PreliminaryReportForm
from .excelio import produtos as xlprodutos
from .excelio import estoques as xlestoques
from .excelio import caixas as xlcaixas
from .excelio import ativos as xlativos
from .excelio import containers as xlcontainers
from .excelio import pedidos as xlpedidos
from .excelio import itenspedidos as xlitenspedidos
from .excelio import encomendas as xlencomendas
from .excelio.report import getBlocks, getXlsBlocks, generateXlsReport


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
            return render(request, 'relatorios/result.html', {'response': response, 'templateVars': templateVars})
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

        containers_chegaram = list(Compra.objects.order_by('-container').values_list('container').distinct())
        containers_chegaram = "\n".join(item[0] for item in containers_chegaram)

        containers_vao_chegar = list(Chegando.objects.order_by('nome').values_list('nome').distinct())
        containers_vao_chegar = "\n".join(item[0] for item in containers_vao_chegar)

        thisYear = date.today().year
        lastYear = thisYear - 1
    
        lastYearBegin = date(lastYear, 1, 1)

        def getPedidoDates(pedidos):
            return sorted(set(datetime.strftime(p.data, "%Y-%m-%d") for p in pedidos), reverse=True)

        def getPedidoDateObjects(pedidos):
            return sorted(set(p.data for p in pedidos), reverse=True)

        datas_com_pedidos = getPedidoDates(Pedido.objects.filter(data__gte=lastYearBegin))
        
        datasStr = "\n".join(datas_com_pedidos)

        # check quality of data
        ptl_pedidos_since_last_year = Pedido.objects.filter(empresa_numero__gte="PON_", data__gte=lastYearBegin)

        uni_pedidos_since_last_year = Pedido.objects.filter(empresa_numero__gte="UNI_", data__gte=lastYearBegin)

        ptl_dates = getPedidoDateObjects(ptl_pedidos_since_last_year)
        uni_dates = getPedidoDateObjects(uni_pedidos_since_last_year)

        for year in range(lastYear, thisYear+1):
            for month in range(1, 13):
                beginningOfMonth = date(year, month, 1)
                endOfMonth = date(year, month, monthrange(year, month)[1])
                if endOfMonth <= date.today():
                    if sum(1 if beginningOfMonth <= d <= endOfMonth else 0 for d in ptl_dates) < 12:
                        warnings += "PTL pedidos for {}/{} is low\n".format(year, month)

                    if year > 2018 and sum(1 if beginningOfMonth <= d <= endOfMonth else 0 for d in uni_dates) < 5:
                        warnings += "UNI pedidos for {}/{} is low\n".format(year, month)

        return render(request, 'relatorios/verificar.html',
                      {'form': form,
                       'warnings': warnings,
                       'atualizados': atualizados,
                       'containers_chegaram': containers_chegaram,
                       'containers_vao_chegar': containers_vao_chegar,
                       'datas_com_pedidos': datasStr,
                      })

   
def preliminaryReport(request, codigoBangs):
    blocks, response_err = getBlocks(codigoBangs)
    thisyr = int(datetime.strftime(date.today(), "%Y"))
    lastyr = thisyr - 1

    return render(request, 'relatorios/preliminaryReport.html', { 'err': response_err, 'blocks': blocks, 'thisyr': thisyr, 'lastyr': lastyr })
    

def xlsReport(request):
    if request.method == "POST":
        selected = request.POST.getlist('selected_cod')
        blocks = getXlsBlocks(selected)
        todayStr = datetime.strftime(date.today(), "%Y-%m-%d")
        
        response = HttpResponse(generateXlsReport(blocks), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=relatorio-' + todayStr + '.xlsx'
        return response
                                    
    else:
        return redirect('relatorios:verificar')
