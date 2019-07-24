from django.urls import path
from . import views

app_name = "relatorios"

urlpatterns = [
    path('', views.index, name="index"),
    path('produtos/', views.produtos, name="produtos"),
    path('estoques/', views.estoques, name="estoques"),
    path('caixas/', views.caixas, name="caixas"),
    # ativos
]
