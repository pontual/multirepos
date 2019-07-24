from django.shortcuts import render
from fichas.models import Atualizado
from .forms import UploadExcelForm, UploadTwoExcelsForm
from .excelio import produtos as xlprodutos
from .excelio import estoques as xlestoques
from .excelio import caixas as xlcaixas
from .excelio import ativos as xlativos


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
    tipos = ["produtos", "caixas", "ativos", "estoques", "containers", "pedidos", "itenspedidos", "encomendas"]
    atualizados = { t: dataAtualizado(t) for t in tipos }
    return render(request, 'relatorios/index.html', {'atualizados': atualizados})


def formDescription(request, tipo, callback):
    return fileUploadView(request, callback, 'relatorios/' + tipo + '.html', {'tipo': tipo, 'data': dataAtualizado(tipo)})


def produtos(request):
    return formDescription(request, "produtos", xlprodutos.create)
 

def estoques(request):
    return fileUploadTwoView(request, xlestoques.create, 'relatorios/estoques.html', {'tipo': 'estoques', 'data': dataAtualizado('estoques')})


def caixas(request):
    return formDescription(request, "caixas", xlcaixas.create)


def ativos(request):
    return formDescription(request, "ativos", xlativos.create)


