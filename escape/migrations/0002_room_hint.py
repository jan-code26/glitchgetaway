# Generated by Django 5.2 on 2025-05-03 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escape', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='hint',
            field=models.TextField(blank=True, default='No hint available.'),
        ),
    ]
