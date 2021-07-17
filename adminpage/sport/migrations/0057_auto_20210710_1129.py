# Generated by Django 3.1.8 on 2021-07-10 08:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0056_student_course'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'permissions': [('go_to_another_group', 'Can go to another group in the same type of sport')], 'verbose_name_plural': 'groups'},
        ),
        migrations.AlterModelOptions(
            name='selfsporttype',
            options={'permissions': [('more_than_10_hours_of_self_sport', 'Can have more then 10 hours of self sport')]},
        ),
    ]
