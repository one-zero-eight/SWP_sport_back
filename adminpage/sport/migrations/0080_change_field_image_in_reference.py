# Generated by Django 3.1.8 on 2021-08-23 14:59

from django.db import migrations
import smartfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0079_auto_20210816_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reference',
            name='image',
            field=smartfields.fields.ImageField(upload_to=''),
        ),
    ]
