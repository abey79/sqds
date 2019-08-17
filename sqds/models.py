from copy import copy
from typing import Union, Collection, List

import pandas
from django.db import models, transaction
from django.db.models import Q, Sum, Count, Subquery, OuterRef, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.html import format_html
from django_enumfield import enum

from . import swgoh

LEFT_HAND_G12_GEAR_ID = [158, 159, 160, 161, 162, 163, 164, 165]
RIGHT_HAND_G12_GEAR_ID = [166, 167, 168, 169, 170, 171]


def update_game_data(ability_data_list=None,
                     skill_data_list=None,
                     unit_data_list=None,
                     category_data_list=None):
    if ability_data_list is None:
        ability_data_list = swgoh.api.get_ability_list()
    if skill_data_list is None:
        skill_data_list = swgoh.api.get_skill_list()
    if unit_data_list is None:
        unit_data_list = swgoh.api.get_unit_list()
    if category_data_list is None:
        category_data_list = swgoh.api.get_category_list()

    skill_dict = {item['id']: item for item in skill_data_list}
    ability_dict = {item['id']: item for item in ability_data_list}

    with transaction.atomic():
        for category_data in category_data_list:
            category, _ = Category.objects.update_or_create(
                api_id=category_data['id'],
                defaults={'name': category_data['descKey']})

        unit_id_list = []
        for unit_data in unit_data_list:
            unit, _ = Unit.objects.update_or_create(
                api_id=unit_data['baseId'],
                defaults={'name': unit_data['nameKey']}
            )
            unit_id_list.append(unit.id)

            for skill_ref in unit_data['skillReferenceList']:
                skill_data = skill_dict[skill_ref['skillId']]
                skill, _ = Skill.objects.update_or_create(
                    api_id=skill_data['id'],
                    defaults={
                        'unit': unit,
                        'name': ability_dict[
                            skill_data['abilityReference']]['nameKey'],
                        'is_zeta': skill_data['isZeta']})

            for category in Category.objects.filter(
                    api_id__in=unit_data['categoryIdList']).all():
                unit.categories.add(category)

        Unit.objects.exclude(id__in=unit_id_list).delete()


class Category(models.Model):
    api_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):  # pragma: no cover
        return self.name


class Unit(models.Model):
    api_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200, default='')
    categories = models.ManyToManyField(Category, related_name='unit_set')

    def __str__(self):  # pragma: no cover
        return self.name


class Skill(models.Model):
    api_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    is_zeta = models.BooleanField()

    def __str__(self):  # pragma: no cover
        return self.name


class GearManager(models.Manager):
    @staticmethod
    def update_or_create_from_swgoh():
        """Update gear table from server"""

        gear_data_list = swgoh.api.get_gear_list()
        with transaction.atomic():
            gear_id_list = []
            for gear_data in gear_data_list:
                gid = int(gear_data['id']) if str.isdigit(gear_data['id']) \
                    else 0
                is_left = gid in LEFT_HAND_G12_GEAR_ID
                is_right = gid in RIGHT_HAND_G12_GEAR_ID or gear_data['id'].startswith(
                    'G12Finisher')
                gear, _ = Gear.objects.update_or_create(
                    api_id=gear_data['id'],
                    defaults={
                        'name': gear_data['nameKey'],
                        'tier': gear_data['tier'],
                        'required_rarity': gear_data['requiredRarity'],
                        'required_level': gear_data['requiredLevel'],
                        'is_left_hand_g12': is_left,
                        'is_right_hand_g12': is_right,
                    })
                gear_id_list.append(gear.id)
            Gear.objects.exclude(id__in=gear_id_list).delete()


class Gear(models.Model):
    api_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    tier = models.IntegerField()
    required_rarity = models.IntegerField()
    required_level = models.IntegerField()

    is_left_hand_g12 = models.BooleanField()
    is_right_hand_g12 = models.BooleanField()

    objects = GearManager()

    def __str__(self):  # pragma: no cover
        return self.name


class GuildManager(models.Manager):

    # pylint: disable=too-many-locals
    # noinspection PyMethodMayBeStatic
    def update_or_create_from_swgoh(
            self, ally_code=116235559, guild_only=False):
        """ Create a guild that contains provided ally_code, or update it if
            it already exists. If all_player is True, all players are then
            fully imported. Otherwise, only ally_code is imported. """

        # Get guild data from server
        guild_data = swgoh.api.get_guild_list(ally_code)

        # Create or update Guild instance
        guild_id = guild_data['id']
        guild, _ = Guild.objects.update_or_create(api_id=guild_id, defaults={
            'name': guild_data['name'],
            'gp': guild_data['gp']})

        if guild_only:
            return guild

        # For all of the guild players, download their info, roster, mods and skills.

        ally_codes = [p['allyCode'] for p in guild_data['roster']]
        all_player_data = swgoh.api.get_player_data_batch(ally_codes)

        # Create or update all Player instance, deleting players no longer present
        with transaction.atomic():
            player_id_array = []

            for player_data in all_player_data:
                player = Player.objects.update_or_create_from_data(player_data, guild)
                player_id_array.append(player.id)

            guild.player_set.exclude(id__in=player_id_array).delete()

        return guild


class GuildSet(models.QuerySet):
    def annotate_stats(self):
        player_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set'))
        gp_char = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Sum('player_set__gp_char'))
        gp_ship = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Sum('player_set__gp_ship'))
        unit_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set'))
        seven_star_unit_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set', filter=Q(player_set__unit_set__rarity=7)))
        g13_unit_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set', filter=Q(player_set__unit_set__gear=13)))
        g12_unit_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set', filter=Q(player_set__unit_set__gear=12)))
        g11_unit_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set', filter=Q(player_set__unit_set__gear=11)))
        g10_unit_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set', filter=Q(player_set__unit_set__gear=10)))
        zeta_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__zeta_set'))
        g12_gear_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count(
                'player_set__unit_set__pug_set',
                filter=(Q(
                    player_set__unit_set__pug_set__gear__is_right_hand_g12=True)
                        | Q(
                            player_set__unit_set__pug_set__gear__is_left_hand_g12=True))))
        right_hand_g12_gear_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__pug_set',
                      filter=Q(
                          player_set__unit_set__pug_set__gear__is_right_hand_g12=True)))
        left_hand_g12_gear_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__pug_set',
                      filter=Q(
                          player_set__unit_set__pug_set__gear__is_left_hand_g12=True)))
        mod_count = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__mod_set'))
        mod_count_6dot = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__mod_set',
                      filter=Q(player_set__unit_set__mod_set__pips__gte=6)))
        mod_count_speed_25 = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__mod_set',
                      filter=(Q(player_set__unit_set__mod_set__speed__gte=25) & ~Q(
                          player_set__unit_set__mod_set__slot=1))))
        mod_count_speed_20 = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__mod_set',
                      filter=(Q(player_set__unit_set__mod_set__speed__gte=20) & Q(
                          player_set__unit_set__mod_set__speed__lt=25) & ~Q(
                          player_set__unit_set__mod_set__slot=1))))
        mod_count_speed_15 = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__mod_set',
                      filter=(Q(player_set__unit_set__mod_set__speed__gte=15) & Q(
                          player_set__unit_set__mod_set__speed__lt=20) & ~Q(
                          player_set__unit_set__mod_set__slot=1))))
        mod_count_speed_10 = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('player_set__unit_set__mod_set',
                      filter=(Q(player_set__unit_set__mod_set__speed__gte=10) & Q(
                          player_set__unit_set__mod_set__speed__lt=15) & ~Q(
                          player_set__unit_set__mod_set__slot=1))))
        mod_total_speed_15plus = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            sum15=Sum('player_set__unit_set__mod_set__speed',
                      filter=(Q(player_set__unit_set__mod_set__speed__gte=15) & ~Q(
                          player_set__unit_set__mod_set__slot=1))))

        return self.annotate(
            player_count=Subquery(player_count.values('cnt'),
                                  output_field=models.IntegerField()),
            gp_char=Subquery(gp_char.values('cnt'),
                             output_field=models.IntegerField()),
            gp_ship=Subquery(gp_ship.values('cnt'),
                             output_field=models.IntegerField()),
            unit_count=Subquery(unit_count.values('cnt'),
                                output_field=models.IntegerField()),
            seven_star_unit_count=Subquery(seven_star_unit_count.values('cnt'),
                                           output_field=models.IntegerField()),
            g13_unit_count=Subquery(g13_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),
            g12_unit_count=Subquery(g12_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),
            g11_unit_count=Subquery(g11_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),
            g10_unit_count=Subquery(g10_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),

            zeta_count=Subquery(zeta_count.values('cnt'),
                                output_field=models.IntegerField()),
            g12_gear_count=Subquery(g12_gear_count.values('cnt'),
                                    output_field=models.IntegerField()),
            right_hand_g12_gear_count_g12_only=Subquery(right_hand_g12_gear_count.values(
                'cnt'), output_field=models.IntegerField()),
            left_hand_g12_gear_count_g12_only=Subquery(left_hand_g12_gear_count.values(
                'cnt'), output_field=models.IntegerField()),
            right_hand_g12_gear_count=F('right_hand_g12_gear_count_g12_only') + 3 * F(
                'g13_unit_count'),
            left_hand_g12_gear_count=F('left_hand_g12_gear_count_g12_only') + 3 * F(
                'g13_unit_count'),
            mod_count=Subquery(mod_count.values('cnt'),
                               output_field=models.IntegerField()),
            mod_count_6dot=Subquery(mod_count_6dot.values('cnt'),
                                    output_field=models.IntegerField()),
            mod_count_speed_25=Subquery(mod_count_speed_25.values('cnt'),
                                        output_field=models.IntegerField()),
            mod_count_speed_20=Subquery(mod_count_speed_20.values('cnt'),
                                        output_field=models.IntegerField()),
            mod_count_speed_15=Subquery(mod_count_speed_15.values('cnt'),
                                        output_field=models.IntegerField()),
            mod_count_speed_10=Subquery(mod_count_speed_10.values('cnt'),
                                        output_field=models.IntegerField()),

            mod_total_speed_15plus=Subquery(mod_total_speed_15plus.values('sum15'),
                                            output_field=models.IntegerField())
        )

    def annotate_faction_gp(self):
        unit_ids = Unit.objects.filter(
            categories__api_id='affiliation_separatist').values('id')
        sep_gp = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            sep_gp=Sum('player_set__unit_set__gp',
                       filter=Q(player_set__unit_set__unit__id__in=unit_ids)))

        gr_unit_ids = Unit.objects.filter(
            categories__api_id='affiliation_republic').values('id')
        gr_gp = Guild.objects.filter(pk=OuterRef('pk')).annotate(
            gr_gp=Sum('player_set__unit_set__gp',
                      filter=Q(player_set__unit_set__unit__id__in=gr_unit_ids)))

        return self.annotate(
            sep_gp=Subquery(sep_gp.values('sep_gp'), output_field=models.IntegerField()),
            gr_gp=Subquery(gr_gp.values('gr_gp'), output_field=models.IntegerField()))


class Guild(models.Model):
    api_id = models.CharField(max_length=50, unique=True, db_index=True)

    name = models.CharField(max_length=200)
    gp = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    objects = GuildManager.from_queryset(GuildSet)()

    def __str__(self):  # pragma: no cover
        return self.name


class PlayerManager(models.Manager):
    def ensure_exist(
            self, ally_codes: Union[int, Collection[int]],
            max_days: int = -1) -> List['Player']:
        """
        Ensure players are loaded in the database.
        :param ally_codes: ally code or ally code list of player to check
        :param max_days: maximum acceptable number of days Player data may be outdated
        (will be refreshed if more). If set to negative value, last updated will not be
        checked
        :return: list of Player object
        """
        # If a single ally code is passed, make it a list
        if type(ally_codes) == int:
            ally_codes = [ally_codes]
        else:
            # We make a copy because we modify the list
            ally_codes = copy(ally_codes)

        # Check which players we already have and remove them from ally code list. We
        # check how old the data is
        players = []
        now = timezone.now()
        for player in Player.objects.filter(ally_code__in=ally_codes):
            time_diff = now - player.last_updated
            if max_days < 0 or time_diff.days < max_days:
                ally_codes.remove(player.ally_code)
                players.append(player)

        # Download data for all remaining players
        if ally_codes:
            players.extend(self.update_or_create_multiple_from_swgoh(ally_codes))

        return players

    def update_or_create_multiple_from_swgoh(
            self, ally_codes: Collection[int]) -> List['Player']:
        # Get data for all players
        all_player_data = swgoh.api.get_player_data_batch(ally_codes)

        with transaction.atomic():
            players = []
            for player_data in all_player_data:
                # find player guilds
                if player_data['guildRefId'] != '':
                    guild = Guild.objects.update_or_create_from_swgoh(
                        player_data['allyCode'], guild_only=True)
                else:
                    guild = None

                players.append(self.update_or_create_from_data(player_data, guild))

        return players

    def update_or_create_from_swgoh(self, ally_code: int) -> 'Player':
        player_data = swgoh.api.get_player_data(ally_code)[0]

        if player_data['guildRefId'] != '':
            guild = Guild.objects.update_or_create_from_swgoh(
                ally_code, guild_only=True)
        else:
            guild = None

        with transaction.atomic():
            player = self.update_or_create_from_data(player_data, guild)

        return player

    def update_or_create_from_data(self, player_data,
                                   guild: Union[Guild, None]) -> 'Player':
        """
        Update or create a player based on data from swgoh.help.
        Note: this function makes multiple calls to the database and is best wrapped in
        an transaction.atomic() statement to ensure consistency.
        :param player_data: the data from swgoh.help
        :param guild: the guild object for the player or None
        :return: the Player object created or updated
        """
        player, _ = Player.objects.update_or_create(
            api_id=player_data['id'],
            defaults={
                'guild': guild,
                'name': player_data['name'],
                'level': player_data['level'],
                'ally_code': player_data['allyCode'],
                'gp': player_data['stats'][0]['value'],
                'gp_char': player_data['stats'][1]['value'],
                'gp_ship': player_data['stats'][2]['value']})
        player.save()  # force last updated change
        self.update_player_units(player, all_units_data=player_data['roster'])
        return player

    @staticmethod
    def update_player_units(player, all_units_data):
        with transaction.atomic():
            # Delete everything and batch create
            PlayerUnit.objects.filter(player=player).delete()

            zetas_to_create = []
            pugs_to_create = []
            mods_to_create = []

            for unit_data in all_units_data:
                # ignore ships
                if unit_data['combatType'] != 1:
                    continue

                unit = Unit.objects.get(api_id=unit_data['defId'])
                unit_stats = unit_data['stats']['final']
                mod_stats = unit_data['stats']['mods']

                # (D1) Update player model
                player_unit = PlayerUnit(
                    player=player,
                    unit=unit,

                    gp=unit_data['gp'] if unit_data['gp'] is not None else 0,
                    rarity=unit_data['rarity'],
                    level=unit_data['level'],
                    gear=unit_data['gear'],
                    equipped_count=len(unit_data['equipped']),

                    speed=unit_stats['Speed'],
                    health=unit_stats['Health'],
                    protection=unit_stats.get('Protection', 0),

                    physical_damage=unit_stats['Physical Damage'],
                    physical_crit_chance=unit_stats[
                        'Physical Critical Chance'],
                    special_damage=unit_stats['Special Damage'],
                    special_crit_chance=unit_stats['Special Critical Chance'],
                    crit_damage=unit_stats['Critical Damage'],

                    potency=unit_stats.get('Potency', 0.0),
                    tenacity=unit_stats.get('Tenacity', 0.0),
                    armor=unit_stats.get('Armor', 0.0),
                    resistance=unit_stats.get('Resistance', 0.0),
                    armor_penetration=unit_stats.get('Armor Penetration', 0),
                    resistance_penetration=unit_stats.get(
                        'Resistance Penetration', 0),
                    health_steal=unit_stats.get('Health Steal', 0.0),
                    accuracy=unit_stats.get('Accuracy', 0.0),

                    mod_speed=mod_stats.get('Speed', 0.0),
                    mod_health=mod_stats.get('Health', 0.0),
                    mod_protection=mod_stats.get('Protection', 0.0),
                    mod_physical_damage=mod_stats.get('Physical Damage', 0.0),
                    mod_special_damage=mod_stats.get('Special Damage', 0.0),
                    mod_physical_crit_chance=mod_stats.get('Physical Critical Chance',
                                                           0.0),
                    mod_special_crit_chance=mod_stats.get('Special Critical Chance', 0.0),
                    mod_crit_damage=mod_stats.get('Critical Damage', 0.0),
                    mod_potency=mod_stats.get('Potency', 0.0),
                    mod_tenacity=mod_stats.get('Tenacity', 0.0),
                    mod_armor=mod_stats.get('Armor', 0.0),
                    mod_resistance=mod_stats.get('Resistance', 0.0),
                    mod_critical_avoidance=mod_stats.get('Critical Avoidance', 0.0),
                    mod_accuracy=mod_stats.get('Accuracy', 0.0)
                )
                player_unit.save()

                # (D2) Update Zeta model
                for skill_data in unit_data['skills']:
                    if skill_data['isZeta'] and skill_data['tier'] == 8:
                        zeta = Zeta(
                            player_unit=player_unit,
                            skill=Skill.objects.get(api_id=skill_data['id']))
                        zetas_to_create.append(zeta)

                # (D3) Update PlayerUnitGear model
                for gear_data in unit_data['equipped']:
                    pug = PlayerUnitGear(
                        player_unit=player_unit,
                        gear=Gear.objects.get(api_id=gear_data['equipmentId']))
                    pugs_to_create.append(pug)

                # (D4) Update Mod model
                for mod_data in unit_data['mods']:
                    mod = Mod(
                        api_id=mod_data['id'],
                        player_unit=player_unit,
                        mod_set=mod_data['set'],
                        slot=mod_data['slot'] - 1,
                        level=mod_data['level'],
                        pips=mod_data['pips'],
                        tier=mod_data['tier'])
                    mod.update_stats(mod_data)
                    mods_to_create.append(mod)

            Zeta.objects.bulk_create(zetas_to_create)
            PlayerUnitGear.objects.bulk_create(pugs_to_create)
            Mod.objects.bulk_create(mods_to_create)


class PlayerSet(models.QuerySet):
    def annotate_stats(self):
        unit_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set'))
        seven_star_unit_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set', filter=Q(unit_set__rarity=7)))
        g13_unit_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set', filter=Q(unit_set__gear=13)))
        g12_unit_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set', filter=Q(unit_set__gear=12)))
        g11_unit_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set', filter=Q(unit_set__gear=11)))
        g10_unit_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set', filter=Q(unit_set__gear=10)))
        zeta_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__zeta_set'))
        g12_gear_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__pug_set',
                      filter=(Q(unit_set__pug_set__gear__is_right_hand_g12=True) | Q(
                          unit_set__pug_set__gear__is_left_hand_g12=True))))
        right_hand_g12_gear_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__pug_set',
                      filter=Q(unit_set__pug_set__gear__is_right_hand_g12=True)))
        left_hand_g12_gear_count = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__pug_set',
                      filter=Q(unit_set__pug_set__gear__is_left_hand_g12=True)))
        mod_count_6dot = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__mod_set',
                      filter=Q(unit_set__mod_set__pips__gte=6)))
        mod_count_speed_25 = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__mod_set',
                      filter=(Q(unit_set__mod_set__speed__gte=25) & ~Q(
                          unit_set__mod_set__slot=1))))
        mod_count_speed_20 = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__mod_set',
                      filter=(Q(unit_set__mod_set__speed__gte=20) & Q(
                          unit_set__mod_set__speed__lt=25) & ~Q(
                          unit_set__mod_set__slot=1))))
        mod_count_speed_15 = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__mod_set',
                      filter=(Q(unit_set__mod_set__speed__gte=15) & Q(
                          unit_set__mod_set__speed__lt=20) & ~Q(
                          unit_set__mod_set__slot=1))))
        mod_count_speed_10 = Player.objects.filter(pk=OuterRef('pk')).annotate(
            cnt=Count('unit_set__mod_set',
                      filter=(Q(unit_set__mod_set__speed__gte=10) & Q(
                          unit_set__mod_set__speed__lt=15) & ~Q(
                          unit_set__mod_set__slot=1))))
        mod_total_speed_15plus = Player.objects.filter(pk=OuterRef('pk')).annotate(
            sum15=Sum('unit_set__mod_set__speed',
                      filter=(Q(unit_set__mod_set__speed__gte=15) & ~Q(
                          unit_set__mod_set__slot=1))))

        return self.annotate(
            unit_count=Subquery(unit_count.values('cnt'),
                                output_field=models.IntegerField()),
            seven_star_unit_count=Subquery(seven_star_unit_count.values('cnt'),
                                           output_field=models.IntegerField()),
            g13_unit_count=Subquery(g13_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),
            g12_unit_count=Subquery(g12_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),
            g11_unit_count=Subquery(g11_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),
            g10_unit_count=Subquery(g10_unit_count.values('cnt'),
                                    output_field=models.IntegerField()),
            zeta_count=Subquery(zeta_count.values('cnt'),
                                output_field=models.IntegerField()),
            g12_gear_count=Subquery(g12_gear_count.values('cnt'),
                                    output_field=models.IntegerField()),
            right_hand_g12_gear_count_g12_only=Subquery(right_hand_g12_gear_count.values(
                'cnt'), output_field=models.IntegerField()),
            left_hand_g12_gear_count_g12_only=Subquery(left_hand_g12_gear_count.values(
                'cnt'), output_field=models.IntegerField()),
            right_hand_g12_gear_count=F('right_hand_g12_gear_count_g12_only') + 3 * F(
                'g13_unit_count'),
            left_hand_g12_gear_count=F('left_hand_g12_gear_count_g12_only') + 3 * F(
                'g13_unit_count'),
            mod_count_6dot=Subquery(mod_count_6dot.values('cnt'),
                                    output_field=models.IntegerField()),
            mod_count_speed_25=Subquery(mod_count_speed_25.values('cnt'),
                                        output_field=models.IntegerField()),
            mod_count_speed_20=Subquery(mod_count_speed_20.values('cnt'),
                                        output_field=models.IntegerField()),
            mod_count_speed_15=Subquery(mod_count_speed_15.values('cnt'),
                                        output_field=models.IntegerField()),
            mod_count_speed_10=Subquery(mod_count_speed_10.values('cnt'),
                                        output_field=models.IntegerField()),
            mod_total_speed_15plus=Subquery(mod_total_speed_15plus.values('sum15'),
                                            output_field=models.IntegerField()))

    def annotate_faction_gp(self):
        unit_ids = Unit.objects.filter(
            categories__api_id='affiliation_separatist').values('id')
        sep_gp = Player.objects.filter(pk=OuterRef('pk')).annotate(
            sep_gp=Sum('unit_set__gp',
                       filter=Q(unit_set__unit__id__in=unit_ids)))

        gr_unit_ids = Unit.objects.filter(
            categories__api_id='affiliation_republic').values('id')
        gr_gp = Player.objects.filter(pk=OuterRef('pk')).annotate(
            gr_gp=Sum('unit_set__gp',
                      filter=Q(unit_set__unit__id__in=gr_unit_ids)))

        return self.annotate(
            sep_gp=Subquery(sep_gp.values('sep_gp'), output_field=models.IntegerField()),
            gr_gp=Subquery(gr_gp.values('gr_gp'), output_field=models.IntegerField()))


class Player(models.Model):
    api_id = models.CharField(max_length=50, unique=True, db_index=True)

    guild = models.ForeignKey(Guild, null=True, on_delete=models.CASCADE,
                              related_name="player_set")
    name = models.CharField(max_length=200)
    level = models.IntegerField()
    ally_code = models.IntegerField(db_index=True)

    gp = models.IntegerField(verbose_name='GP')
    gp_char = models.IntegerField(verbose_name='GP (Characters)')
    gp_ship = models.IntegerField(verbose_name='GP (Ships)')

    last_updated = models.DateTimeField(auto_now=True)

    objects = PlayerManager.from_queryset(PlayerSet)()

    def __str__(self):  # pragma: no cover
        return self.name


class PlayerUnitManager(models.Manager):
    def dict_from_ally_code(self, ally_code: int, unit_ids=None):
        """
        Return a dictionary of Pandas' Series for each of the player's unit. Keys are
        corresponding Unit's `api_id`. The returned series behaves like a `PlayerUnit`
        instances but related models are only available through `unit_name`,
        `unit_api_id`, `player_name` and `player_ally_code` attributes
        :param ally_code: the player's ally code
        :param unit_ids: (optional) list of Unit's API ID to restrict the scopes
        :return: the dictionary
        """
        if unit_ids is None:
            unit_ids = []
        unit_filter = {'unit__api_id__in': unit_ids} if unit_ids else {}
        qs = (self.model.objects
              .filter(player__ally_code=ally_code, **unit_filter)
              .select_related('unit', 'player')
              .annotate(unit_name=F('unit__name'),
                        unit_api_id=F('unit__api_id'),
                        player_name=F('player__name'),
                        player_ally_code=F('player__ally_code'))
              .annotate_stats()
              .values())
        if qs.count() > 0:
            df = pandas.DataFrame(qs)
            df.set_index(df['unit_api_id'], inplace=True)
            return {unit_key: df.loc[unit_key] for unit_key in df.index}
        else:
            return {}


class PlayerUnitSet(models.QuerySet):
    def annotate_stats(self):
        mod_speed_no_set = PlayerUnit.objects.filter(pk=OuterRef('pk')).annotate(
            mod_speed_no_set=Coalesce(Sum('mod_set__speed'), 0))
        zeta_count = PlayerUnit.objects.filter(pk=OuterRef('pk')).annotate(
            zeta_count=Count('zeta_set'))
        return self.annotate(
            mod_speed_no_set=Subquery(mod_speed_no_set.values('mod_speed_no_set'),
                                      output_field=models.IntegerField()),
            zeta_count=Subquery(zeta_count.values('zeta_count'),
                                output_field=models.IntegerField()))


class PlayerUnit(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name='unit_set')

    gp = models.IntegerField(verbose_name='GP')
    rarity = models.IntegerField()
    level = models.IntegerField()
    gear = models.IntegerField()

    # TODO: this should be removed
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
    accuracy = models.FloatField(verbose_name="Acc.")

    mod_speed = models.IntegerField(verbose_name="Mod speed")
    mod_health = models.IntegerField(verbose_name="Mod HP")
    mod_protection = models.IntegerField(verbose_name="Mod prot.")
    mod_physical_damage = models.IntegerField(verbose_name="Mod phys. dmg")
    mod_special_damage = models.IntegerField(verbose_name="Mod spec. dmg")
    mod_physical_crit_chance = models.FloatField(verbose_name="Mod phys. CC")
    mod_special_crit_chance = models.FloatField(verbose_name="Mod spec. CC")
    mod_crit_damage = models.FloatField(verbose_name="Mod CD")
    mod_potency = models.FloatField(verbose_name="Mod pot.")
    mod_tenacity = models.FloatField(verbose_name="Mod ten.")
    mod_armor = models.FloatField(verbose_name="Mod armor")
    mod_resistance = models.FloatField(verbose_name="Mod res.")
    mod_critical_avoidance = models.FloatField(verbose_name="Mod CA")
    mod_accuracy = models.FloatField(verbose_name="Mod acc.")

    last_updated = models.DateTimeField(auto_now=True)

    objects = PlayerUnitManager.from_queryset(PlayerUnitSet)()

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
        elif self.gear in [13]:
            color_code = 'D53'
        return format_html(
            '<b style="color: #{}; text-shadow: -1px -1px 0 #333,'
            ' 1px -1px 0 #333, -1px 1px 0 #333, 1px 1px 0 #333">G{}</b>',
            color_code,
            self.gear)

    colored_gear.admin_order_field = 'gear'

    def summary(self):
        return format_html(
            '{}&nbsp;L{}&nbsp;{}{}',
            self.star_count(),
            self.level,
            self.colored_gear(),
            '+' + str(self.equipped_count) if self.equipped_count > 0 else '')

    summary.admin_order_field = ['rarity', 'level', 'gear', 'equipped_count']


class Zeta(models.Model):
    player_unit = models.ForeignKey(PlayerUnit,
                                    on_delete=models.CASCADE,
                                    related_name='zeta_set')
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT)


class PlayerUnitGear(models.Model):
    player_unit = models.ForeignKey(PlayerUnit, on_delete=models.CASCADE,
                                    related_name='pug_set')
    gear = models.ForeignKey(Gear, on_delete=models.PROTECT)


MOD_STAT_MAP = {
    1: {'name': 'health', 'mult': 1},
    5: {'name': 'speed', 'mult': 1},
    16: {'name': 'critical_damage', 'mult': .01},
    17: {'name': 'potency', 'mult': .01},
    18: {'name': 'tenacity', 'mult': .01},
    28: {'name': 'protection', 'mult': 1},
    41: {'name': 'offense', 'mult': 1},
    42: {'name': 'defense', 'mult': 1},
    48: {'name': 'offense_percent', 'mult': .01},
    49: {'name': 'defense_percent', 'mult': .01},
    52: {'name': 'accuracy', 'mult': .01},
    53: {'name': 'critical_chance', 'mult': .01},
    54: {'name': 'critical_avoidance', 'mult': .01},
    55: {'name': 'health_percent', 'mult': .01},
    56: {'name': 'protection_percent', 'mult': .01},
}


class ModSet(enum.Enum):
    HEALTH = 1
    OFFENSE = 2
    DEFENSE = 3
    SPEED = 4
    CRITICAL_CHANCE = 5
    CRITICAL_DAMAGE = 6
    POTENCY = 7
    TENACITY = 8

    labels = {
        HEALTH: 'Health',
        DEFENSE: 'Defense',
        CRITICAL_DAMAGE: 'Critical Damage',
        CRITICAL_CHANCE: 'Critical Chance',
        TENACITY: 'Tenacity',
        OFFENSE: 'Offense',
        POTENCY: 'Potency',
        SPEED: 'Speed',
    }


class Mod(models.Model):
    api_id = models.CharField(max_length=50, unique=True, db_index=True)
    player_unit = models.ForeignKey(PlayerUnit, on_delete=models.CASCADE,
                                    null=True, related_name='mod_set')

    mod_set = enum.EnumField(ModSet)
    slot = models.IntegerField()
    level = models.IntegerField()
    pips = models.IntegerField()
    tier = models.IntegerField()

    speed = models.IntegerField(default=0)
    health = models.IntegerField(default=0)
    health_percent = models.FloatField(default=0.)
    protection = models.IntegerField(default=0)
    protection_percent = models.FloatField(default=0.)
    offense = models.IntegerField(default=0)
    offense_percent = models.FloatField(default=0.)
    defense = models.IntegerField(default=0)
    defense_percent = models.FloatField(default=0.)
    critical_chance = models.FloatField(default=0.)
    critical_damage = models.FloatField(default=0.)
    potency = models.FloatField(default=0.)
    tenacity = models.FloatField(default=0.)
    critical_avoidance = models.FloatField(default=0.)
    accuracy = models.FloatField(default=0.)

    def update_stats(self, mod_data):
        for stat in [mod_data['primaryStat'], *mod_data['secondaryStat']]:
            modified_stat_info = MOD_STAT_MAP[stat['unitStat']]
            setattr(self, modified_stat_info['name'],
                    stat['value'] * modified_stat_info['mult'])
