# Generated by Django 4.2.7 on 2023-12-04 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinebanking', '0008_accounttransaction_transaction_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='accounttransaction',
            name='exported',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='exported',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customer',
            name='exported',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customeraddress',
            name='exported',
            field=models.BooleanField(default=False),
        ),
    ]