# Generated by Django 5.0.7 on 2025-07-04 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlineStore', '0020_cartitems_product_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitems',
            name='product_name',
        ),
        migrations.AddField(
            model_name='order',
            name='product_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
