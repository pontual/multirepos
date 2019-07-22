from django.contrib import admin
from . import models

admin.site.register(models.Compra)
admin.site.register(models.Chegando)
admin.site.register(models.Pedido)
admin.site.register(models.ItemPedido)

