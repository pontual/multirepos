from datetime import datetime
from .models import Produto, Incluido

def importincluido(fname):
    with open(fname) as f:
        for line in f:
            cod, ymd = line.split(',')
            data = datetime.strptime(ymd.strip(), "%Y-%m-%d")
            p = Produto.objects.get(codigo=cod)
            i = Incluido.objects.create(produto=p, data=data)
            print(i, "saved")


def importultest(fname):
    with open(fname) as f:
        for line in f:
            cod, est = line.split(',')
            Produto.objects.filter(codigo=cod).update(ultimo_estoque=int(est))
