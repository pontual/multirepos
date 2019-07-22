from django.contrib import admin
from . import models

admin.site.register(models.Produto)
admin.site.register(models.Incluido)
admin.site.register(models.Atualizado)
