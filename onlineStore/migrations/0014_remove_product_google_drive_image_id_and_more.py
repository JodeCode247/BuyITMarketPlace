# Generated by Django 5.0.7 on 2025-04-15 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlineStore', '0013_product_image_product_updated_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='google_drive_image_id',
        ),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
