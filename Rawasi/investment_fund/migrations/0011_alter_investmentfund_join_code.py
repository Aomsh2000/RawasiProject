# Generated by Django 4.2.16 on 2024-12-17 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("investment_fund", "0010_investmentfund_profit_balance_wallet_profit_balance"),
    ]

    operations = [
        migrations.AlterField(
            model_name="investmentfund",
            name="join_code",
            field=models.CharField(blank=True, max_length=6, null=True, unique=True),
        ),
    ]
