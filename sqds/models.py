from django.db import models, transaction
from django.utils.html import format_html

from . import swgoh


def update_game_data(ability_data_list=None,
                     skill_data_list=None,
                     unit_data_list=None):
    if ability_data_list is None:
        ability_data_list = swgoh.api.get_ability_list()
    if skill_data_list is None:
        skill_data_list = swgoh.api.get_skill_list()
    if unit_data_list is None:
        unit_data_list = swgoh.api.get_unit_list()

    with transaction.atomic():
        placeholder_unit = Unit.objects.create()
        placeholder_ability = Ability.objects.create()

        for ability_data in ability_data_list:
            ability, _ = Ability.objects.get_or_create(
                api_id=ability_data['id'])
            ability.set_from_data(ability_data)

        Skill.objects.update(unit=placeholder_unit)
        for skill_data in skill_data_list:
            skill, _ = Skill.objects.get_or_create(
                api_id=skill_data['id'],
                defaults={
                    'unit': placeholder_unit,
                    'ability': placeholder_ability})
            skill.set_from_data(skill_data)

        Unit.objects.update(name="DELETE_ME")
        for unit_data in unit_data_list:
            unit, _ = Unit.objects.get_or_create(api_id=unit_data['baseId'])
            unit.set_from_data(unit_data)

        # Clean-up
        Skill.objects.filter(unit=placeholder_unit).delete()
        Unit.objects.filter(name="DELETE_ME").delete()
        placeholder_unit.delete()
        placeholder_ability.delete()


class Ability(models.Model):
    api_id = models.CharField(max_length=200)
    name = models.CharField(max_length=200, default='')
    type = models.IntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=['api_id'])]

    def __str__(self):  # pragma: no cover
        return self.name

    def set_from_data(self, data):
        self.api_id = data['id']
        self.name = data['nameKey']
        self.type = data['abilityType']
        self.save()


class Unit(models.Model):
    api_id = models.CharField(max_length=200)
    name = models.CharField(max_length=200, default='')

    class Meta:
        ordering = ['name', ]
        indexes = [models.Index(fields=['api_id'])]

    def __str__(self):  # pragma: no cover
        return self.name

    def set_from_data(self, data):
        self.api_id = data['baseId']
        self.name = data['nameKey']
        self.save()

        for skill_ref in data['skillReferenceList']:
            skill = Skill.objects.get(api_id=skill_ref['skillId'])
            skill.unit = self
            skill.save()

    @staticmethod
    def create_from_dict(unit_data):
        with transaction.atomic():
            Unit.objects.all().delete()

            for unit in unit_data:
                Unit.objects.create(
                    api_id=unit['baseId'],
                    name=unit['nameKey'])


class Skill(models.Model):
    api_id = models.CharField(max_length=200, default='')
    ability = models.ForeignKey(Ability, on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    is_zeta = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=['api_id'])]

    def __str__(self):  # pragma: no cover
        return self.ability.name

    def set_from_data(self, data):
        self.api_id = data['id']
        self.ability = Ability.objects.get(api_id=data['abilityReference'])
        self.is_zeta = data['isZeta']
        self.save()


class GuildManager(models.Manager):
    def update_or_create_from_swgoh(self, ally_code=116235559):
        ''' Create a guild that contains provided ally_code, or update it if
            it alread exists. '''

        # TODO:
        # - add a last_updated field to Guild and check against it before
        #   loading from Swgoh
        # - check last_updated to conditionally update player's unit

        # (A) Get guild data from server
        guild_data = swgoh.api.get_guild_list(ally_code)

        # (B) Create or update Guild instance
        guild_id = guild_data['id']
        guild, _ = Guild.objects.update_or_create(api_id=guild_id, defaults={
            'name': guild_data['name'],
            'gp': guild_data['gp']})

        # (C) Create or update all Player instance, deleting players no longer
        # present
        with transaction.atomic():
            player_id_array = []

            for player_data in guild_data['roster']:
                player, _ = Player.objects.update_or_create(
                    api_id=player_data['id'],
                    defaults={
                        'guild': guild,
                        'name': player_data['name'],
                        'level': player_data['level'],
                        'ally_code': player_data['allyCode'],
                        'gp': player_data['gp'],
                        'gp_char': player_data['gpChar'],
                        'gp_ship': player_data['gpShip']})
                player_id_array.append(player.id)

            guild.player_set.exclude(id__in=player_id_array).delete()

        # D) For each Player, create or update PlayerUnits and Zetas
        # Note:
        # - We assume that a PlayerUnit never disappear
        # - It's ok to fail a player's units update (504 error are common),
        #   just print some error message.
        for player in guild.player_set.all():
            try:
                player_data = swgoh.api.get_player_unit_list(
                    int(player.ally_code))
            except swgoh.SwgohError as error:
                s = "Error downloading data for player {} (status code: {})"
                print(s.format(player.name, error.response.status_code))

                continue

            with transaction.atomic():
                for unit_id in player_data:
                    unit = Unit.objects.get(api_id=unit_id)
                    unit_data = player_data[unit_id]
                    unit_stats = unit_data['stats']['final']

                    player_unit, _ = PlayerUnit.objects.update_or_create(
                        player=player, unit=unit,
                        defaults={
                            'gp': unit_data['unit']['gp'],
                            'rarity': unit_data['unit']['starLevel'],
                            'level': unit_data['unit']['level'],
                            'gear': unit_data['unit']['gearLevel'],
                            'equipped_count': len(unit_data['unit']['gear']),

                            'speed': unit_stats['Speed'],
                            'health': unit_stats['Health'],
                            'protection': unit_stats.get('Protection', 0),

                            'physical_damage': unit_stats['Physical Damage'],
                            'physical_crit_chance':
                                unit_stats['Physical Critical Chance'],
                            'special_damage':
                                unit_stats['Special Damage'],
                            'special_crit_chance':
                                unit_stats['Special Critical Chance'],
                            'crit_damage': unit_stats['Critical Damage'],

                            'potency': unit_stats.get('Potency', 0.0),
                            'tenacity': unit_stats.get('Tenacity', 0.0),
                            'armor': unit_stats.get('Armor', 0.0),
                            'resistance': unit_stats.get('Resistance', 0.0),
                            'armor_penetration':
                                unit_stats.get('Armor Penetration', 0),
                            'resistance_penetration':
                                unit_stats.get('Resistance Penetration', 0),
                            'health_steal': unit_stats.get('Health Steal', 0.0)
                        })

                    zeta_id_array = []

                    for zeta_data in unit_data['unit']['zetas']:
                        zeta, _ = Zeta.objects.update_or_create(
                            player_unit=player_unit,
                            skill=Skill.objects.get(api_id=zeta_data['id']))
                        zeta_id_array.append(zeta.id)

                    Zeta.objects.filter(player_unit=player_unit).exclude(
                        id__in=zeta_id_array).delete()


class Guild(models.Model):
    api_id = models.CharField(max_length=20)

    name = models.CharField(max_length=200)
    gp = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    objects = GuildManager()

    class Meta:
        ordering = ['name', ]
        indexes = [models.Index(fields=['api_id'])]

    def __str__(self):  # pragma: no cover
        return self.name


class Player(models.Model):
    api_id = models.CharField(max_length=20)

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    level = models.IntegerField()
    ally_code = models.IntegerField()

    gp = models.IntegerField(verbose_name='GP')
    gp_char = models.IntegerField(verbose_name='GP (Characters)')
    gp_ship = models.IntegerField(verbose_name='GP (Ships)')

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-gp', ]
        indexes = [models.Index(fields=['api_id'])]

    def __str__(self):  # pragma: no cover
        return self.name

    def zeta_count(self):
        return Zeta.objects.filter(player_unit__player=self).count()


class PlayerUnit(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name='unit_set')

    gp = models.IntegerField(verbose_name='GP')
    rarity = models.IntegerField()
    level = models.IntegerField()
    gear = models.IntegerField()
    equipped_count = models.IntegerField()

    speed = models.IntegerField()
    health = models.IntegerField(verbose_name='HP')
    protection = models.IntegerField(verbose_name='Prot.')

    physical_damage = models.IntegerField(verbose_name='Phys. dmg')
    physical_crit_chance = models.FloatField(verbose_name='Phys. CC')
    special_damage = models.IntegerField(verbose_name='Spec. dmg')
    special_crit_chance = models.FloatField(verbose_name='Spec. CC')
    crit_damage = models.FloatField(verbose_name='CD')

    potency = models.FloatField(verbose_name='Pot.')
    tenacity = models.FloatField(verbose_name='Ten.')
    armor = models.FloatField()
    resistance = models.FloatField(verbose_name='Res.')
    armor_penetration = models.IntegerField()
    resistance_penetration = models.IntegerField()
    health_steal = models.FloatField()

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['player__name', 'unit__name']

    def __str__(self):  # pragma: no cover
        return "%s's %s" % (self.player.name, self.unit.name)

    def star_count(self):
        return "%d★" % self.rarity
    star_count.admin_order_field = 'rarity'

    def colored_gear(self):
        color_code = 'FFF'
        if self.gear in [2, 3]:
            color_code = 'BF6'
        elif self.gear in [4, 5, 6]:
            color_code = '5CF'
        elif self.gear in [7, 8, 9, 10, 11]:
            color_code = '95F'
        elif self.gear in [12]:
            color_code = 'FD6'
        return format_html(
            '<b style="color: #{}; text-shadow: -1px -1px 0 #333,'
            ' 1px -1px 0 #333, -1px 1px 0 #333, 1px 1px 0 #333">G{}</b>',
            color_code,
            self.gear)
    colored_gear.admin_order_field = 'gear'

    def summary(self):
        return format_html('{} / L{} / {}+{}',
                           self.star_count(),
                           self.level,
                           self.colored_gear(),
                           self.equipped_count)
    summary.admin_order_field = ['rarity', 'level', 'gear', 'equipped_count']

    def zeta_count(self):
        return self.zeta_set.count()

    def zeta_summary(self):
        str_list = []
        for skill in self.unit.skill_set.filter(is_zeta=True):
            if self.zeta_set.filter(skill=skill).exists():
                s = '<b style="color: #96f">Z</b>'
            else:
                s = '<span style="color: #EEE">Z</span>'
            str_list.append(s)
        return format_html('&nbsp'.join(str_list) if str_list else '&nbsp')


class Zeta(models.Model):
    player_unit = models.ForeignKey(PlayerUnit, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT)
