# Generated by Django 2.2.2 on 2019-06-20 14:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sqds', '0012_auto_20190620_1429'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScoredUnit',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('sqds.unit',),
        ),
        migrations.CreateModel(
            name='ScoreZetaRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='score_zeta_rule_set', to='sqds.Unit')),
                ('zeta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sqds.Skill')),
            ],
        ),
        migrations.CreateModel(
            name='ScoreStatRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stat', models.CharField(choices=[('level', 'Level'), ('gear', 'Gear tier'), ('rarity', 'Rarity'), ('speed', 'Speed'), ('health', 'Health'), ('protection', 'Protection'), ('physical_damage', 'Physical Damage'), ('physical_crit_chance', 'Physical CC'), ('special_damage', 'Special Damage'), ('special_crit_chance', 'Special CC'), ('crit_damage', 'Critical Damage'), ('potency', 'Potency'), ('tenacity', 'Tenacity'), ('mod_speed', 'Mod Speed'), ('mod_critical_chance', 'Mod CC'), ('mod_potency', 'Mod Potency'), ('mod_tenacity', 'Mod Tenacity')], max_length=200)),
                ('value', models.FloatField(null=True)),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='score_stat_rule_set', to='sqds.Unit')),
            ],
        ),
    ]