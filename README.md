# MultiRepos

Aplicativo Django 2.2 para coletar dados da Loja Virtual e classificar produtos de acordo com as vendas dos últimos dois anos.

## Instalação

Use Python 3 e instale os pacotes do arquivo `requirements.txt`, opcionalmente num virtualenv.

`pip install -r requirements.txt`

`python manage.py runserver`

## Fotos

Copie os arquivos diretamente para o diretório `fichas/static/fotos/`

## Criterio para inclusao

`relatorios/excelio/report.py` linha 134

## Acessar dados pelo Django shell

`python manage.py shell`

```
>>> from ishell.movimento import getcont
>>> getcont("141891p")
```