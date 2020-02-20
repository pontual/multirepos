from fichas.models import Produto
from movimento.models import Compra

def getcont(cod):
    cod = cod.upper()
    p = Produto.objects.get(codigo=cod)
    return Compra.objects.filter(produto=p).order_by('-data')[:1]
