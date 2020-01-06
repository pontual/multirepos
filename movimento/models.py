from django.db import models
from fichas.models import Produto


class Compra(models.Model):
    data = models.DateField()
    container = models.CharField(max_length=60)
    produto = models.ForeignKey(Produto, related_name="movimento_compras", on_delete=models.CASCADE)
    qtde = models.IntegerField(default=0)

    class Meta:
        unique_together = ('container', 'produto')
        ordering = ['-data', 'produto']

    def __str__(self):
        return "{} {}".format(self.container, self.produto.codigo)


class Chegando(models.Model):
    produto = models.ForeignKey(Produto, related_name="movimento_chegandos", on_delete=models.CASCADE)
    nome = models.CharField(max_length=60)
    qtde = models.IntegerField()

    class Meta:
        unique_together = ('produto', 'nome', 'qtde')
        ordering = ['produto', 'nome', 'qtde']

    def __str__(self):
        return "{} {} {}".format(self.produto.codigo, self.qtde, self.nome)


class Pedido(models.Model):
    empresa_numero = models.CharField(max_length=60, primary_key=True)
    cliente = models.CharField(max_length=200)
    data = models.DateField()

    class Meta:
        ordering = ['empresa_numero']

    def __str__(self):
        return "{} {} {}".format(self.empresa_numero, self.data, self.cliente)


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="movimento_itempedidos", on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, related_name="movimento_itempedidos", on_delete=models.CASCADE)
    qtde = models.IntegerField()

    class Meta:
        unique_together = ('pedido', 'produto')
        ordering = ['pedido', 'produto']

    def __str__(self):
        return "{} {} {}".format(self.pedido.empresa_numero, self.qtde, self.produto)
