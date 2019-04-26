# Generated by Django 2.2 on 2019-04-26 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sqds', '0002_auto_20190424_2104_squashed_0006_auto_20190425_1647'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_id', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('tier', models.IntegerField()),
                ('required_rarity', models.IntegerField()),
                ('required_level', models.IntegerField()),
            ],
        ),
        migrations.AddIndex(
            model_name='gear',
            index=models.Index(fields=['api_id'], name='sqds_gear_api_id_f26730_idx'),
        ),
    ]
