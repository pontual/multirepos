from django.contrib import admin
from . import models


class ProdutoAdmin(admin.ModelAdmin):
    model = models.Produto
    search_fields = ['codigo']

    
admin.site.register(models.Produto, ProdutoAdmin)
admin.site.register(models.Incluido)
admin.site.register(models.Atualizado)

