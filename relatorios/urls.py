from django.urls import path
from . import views

app_name = "relatorios"

urlpatterns = [
    path('', views.index, name="index"),
    path('produtos/', views.produtos, name="produtos"),
    path('caixas/', views.caixas, name="caixas"),
    path('ativos/', views.ativos, name="ativos"),
    path('estoques/', views.estoques, name="estoques"),

]
