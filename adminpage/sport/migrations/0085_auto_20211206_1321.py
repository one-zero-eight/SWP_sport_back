# Generated by Django 3.1.8 on 2021-12-06 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0084_auto_20211205_1921'),
    ]

    operations = [
        migrations.AddField(
            model_name='semester',
            name='points_fitness_test',
            field=models.IntegerField(default=40),
        ),
    ]
