from django.shortcuts import render

def index(request):
    return render(request, 'relatorios/index.html')


def produtos(request):
    return render(request, 'relatorios/produtos.html')


def estoques(request):
    return render(request, 'relatorios/estoques.html')


