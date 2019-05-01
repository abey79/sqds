# Generated by Django 2.2 on 2019-04-26 08:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sqds', '0003_auto_20190426_0804'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerUnitGear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gear', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sqds.Gear')),
                ('player_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sqds.PlayerUnit')),
            ],
        ),
    ]