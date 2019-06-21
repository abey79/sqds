# Generated by Django 2.2.2 on 2019-06-21 17:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sqds', '0012_auto_20190620_1429'),
    ]

    operations = [
        migrations.CreateModel(
            name='GP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('player_api_id', models.CharField(db_index=True, max_length=50)),
                ('gp', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sqds.Unit')),
            ],
        ),
    ]
