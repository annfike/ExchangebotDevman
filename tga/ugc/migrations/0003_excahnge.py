# Generated by Django 3.2.7 on 2021-10-01 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ugc', '0002_auto_20210929_1239'),
    ]

    operations = [
        migrations.CreateModel(
            name='Excahnge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_user_id', models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name='Первый пользователь для обмена')),
                ('second_user_id', models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name='Второй пользователь для обмена')),
                ('first_stuff_descr', models.CharField(blank=True, db_index=True, max_length=256, null=True)),
                ('second_stuff_descr', models.CharField(blank=True, db_index=True, max_length=256, null=True)),
            ],
            options={
                'verbose_name': 'Пользователи для обмена',
                'verbose_name_plural': 'Пользователи для обмена',
            },
        ),
    ]
