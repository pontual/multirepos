from django.urls import path
from . import views

app_name = "relatorios"

urlpatterns = [
    path('', views.index, name="index"),
    path('produtos/', views.produtos, name="produtos"),
    path('caixas/', views.caixas, name="caixas"),
    path('ativos/', views.ativos, name="ativos"),
    path('estoques/', views.estoques, name="estoques"),
    path('containers/', views.containers, name="containers"),
    path('pedidos/', views.pedidos, name="pedidos"),
    path('itenspedidos/', views.itenspedidos, name="itenspedidos"),
    path('encomendas/', views.encomendas, name="encomendas"),
    path('verificar/', views.verificar, name="verificar"),
    path('xlsreport/', views.xlsReport, name="xlsreport"),
]
