# Generated by Django 2.2.1 on 2019-08-06 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fichas', '0002_auto_20190722_1615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incluido',
            name='data',
            field=models.DateField(),
        ),
    ]