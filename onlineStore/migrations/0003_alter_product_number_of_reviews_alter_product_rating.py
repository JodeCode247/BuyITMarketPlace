# Generated by Django 5.0.7 on 2025-03-16 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlineStore', '0002_alter_product_number_of_reviews_alter_product_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='number_of_reviews',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='rating',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
