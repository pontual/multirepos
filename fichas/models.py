from django.db import models

class Produto(models.Model):
    codigo = models.CharField(max_length=60, primary_key=True)

    disp = models.IntegerField(default=0)
    resv = models.IntegerField(default=0)
    ultimo_estoque = models.IntegerField(default=-1)
    estoque_last_updated = models.DateField(blank=True, null=True)

    nome = models.CharField(max_length=120)
    cx = models.IntegerField(default=0)

    inativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['codigo']

    def __str__(self):
        return "{} {}".format(self.codigo, self.nome)
    

class Incluido(models.Model):
    produto = models.ForeignKey(Produto, related_name="relatorios_incluidos", on_delete=models.CASCADE)
    data = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return "{} {}".format(self.data, self.produto.codigo)


class Atualizado(models.Model):
    tipo = models.CharField(max_length=32)
    data = models.DateField(auto_now_add=True)

    @classmethod
    def atualizar(cls, tipo):
        atualizado, atualizadoCreated = cls.objects.update_or_create(tipo=tipo)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return "{} {}".format(self.data, self.tipo)
    
