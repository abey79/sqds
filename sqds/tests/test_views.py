from bs4 import BeautifulSoup
from django.test import TestCase
from django.urls import reverse

from sqds.models import Player, Guild, Category, Unit
from sqds.tests.utils import generate_game_data, generate_guild
from sqds.templatetags.sqds_filters import big_number
from sqds_seed.factories import CategoryFactory, UnitFactory, PlayerUnitFactory, \
    PlayerFactory


def string_to_float(s):
    s = s.strip().replace(',', '')
    if s.endswith('%'):
        return float(s.replace('%', '')) / 100.
    else:
        return 0. if s == '-' else float(s)


def string_to_int(s):
    s = s.strip().replace(',', '')
    return 0 if s == '-' else int(s)


def table_column_contains_int(table, column_header):
    try:
        column_index = 0
        for header in table.thead.find_all('th'):
            if header.text.strip() == column_header:
                break
            column_index += 1

        for row in table.tbody.find_all('tr'):
            string_to_int(row.find_all('td')[column_index].string)
    except ValueError:
        return False
    return True


def table_get_cell(table, column_header, row_index):
    try:
        column_index = 0
        for header in table.thead.find_all('th'):
            if header.text.strip() == column_header:
                break
            column_index += 1

        return table.tbody.find_all('tr')[row_index].find_all('td')[column_index].string
    except ValueError:
        return None


class TableTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate_game_data()

    def test_player_unit_table_single_unit(self):
        player = PlayerFactory()
        pus = [
            PlayerUnitFactory(player=player, unit=Unit.objects.first(), gp=1000),
            PlayerUnitFactory(player=player, unit=Unit.objects.last(), gp=999,
                              speed=0,
                              health=0,
                              mod_speed=0,
                              mod_potency=0.,
                              mod_tenacity=0)
        ]

        url = reverse('sqds:units')
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        column_to_test = [
            ('Speed', 'speed'),
            ('Mod speed', 'mod_speed'),
            ('HP', 'health'),
            ('Mod HP', 'mod_health'),
            ('Prot.', 'protection'),
            ('Mod prot.', 'mod_protection'),
            ('Phys. dmg', 'physical_damage'),
            ('Mod phys. dmg', 'mod_physical_damage'),
            ('Phys. CC', 'physical_crit_chance'),
            ('Mod phys. CC', 'mod_physical_crit_chance'),
            ('Spec. dmg', 'special_damage'),
            ('Mod spec. dmg', 'mod_special_damage'),
            ('Spec. CC', 'special_crit_chance'),
            ('Mod spec. CC', 'mod_special_crit_chance'),
            ('CD', 'crit_damage'),
            ('Pot.', 'potency'),
            ('Mod pot.', 'mod_potency'),
            ('Ten.', 'tenacity'),
            ('Mod ten.', 'mod_tenacity'),
            ('Armor', 'armor'),
            ('Res.', 'resistance'),
        ]

        self.assertEqual(response.status_code, 200)
        for row_index, pu in enumerate(pus):
            for col in column_to_test:
                self.assertAlmostEqual(
                    string_to_float(table_get_cell(table, col[0], row_index)),
                    getattr(pu, col[1]), places=2)
        self.assertTrue(table_column_contains_int(table, 'Speed'))


class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate_game_data()

        # ensure everyone has some some Separatist
        sep_category = CategoryFactory(api_id='affiliation_separatist')
        sep_unit = UnitFactory(categories=[sep_category])

        generate_guild()
        for player in Player.objects.all():
            PlayerUnitFactory(player=player, unit=sep_unit)

        print('setup completed')

    def test_index_view(self):
        response = self.client.get(reverse('sqds:index'))
        self.assertEqual(response.status_code, 200)

    def test_single_player_view_valid(self):
        player = Player.objects.order_by('?').first()
        url = reverse('sqds:player', args=[player.ally_code])
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['player'].ally_code, player.ally_code)
        self.assertTrue(table_column_contains_int(table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/single_player.html')

    def test_single_player_compare_view_valid(self):
        qs = Player.objects.order_by('?')
        player1 = qs.first()
        player2 = qs.last()
        url = reverse('sqds:player_compare', kwargs={'ally_code1': player1.ally_code,
                                                     'ally_code2': player2.ally_code})
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['player1'].ally_code, player1.ally_code)
        self.assertEqual(response.context['player2'].ally_code, player2.ally_code)
        self.assertTrue(table_column_contains_int(table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/player_compare.html')

    def test_guild_view_valid(self):
        guild = Guild.objects.first()
        url = reverse('sqds:guild', args=[guild.api_id])
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guild'].api_id, guild.api_id)
        self.assertTrue(table_column_contains_int(table, 'Level'))
        self.assertTrue(table_column_contains_int(table, 'Zeta count'))
        self.assertTemplateUsed(response, 'sqds/guild.html')

    def test_guild_view_total_separatists(self):
        guild = generate_guild(player_count=0)
        players = PlayerFactory.create_batch(3, guild=guild)
        unit = UnitFactory(
            categories=Category.objects.filter(api_id='affiliation_separatist'))
        for player in players:
            PlayerUnitFactory(player=player, gp=1000, unit=unit)
        url = reverse('sqds:guild', args=[guild.api_id])
        response = self.client.get(url)
        text = big_number(3000.)
        self.assertContains(response, text)

    def test_guild_units_view_valid(self):
        guild = Guild.objects.first()
        url = reverse('sqds:guild_units', args=[guild.api_id])
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(table_column_contains_int(soup.table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/guild_units.html')

    def test_guild_comparison_units_view(self):
        generate_guild(player_count=20)
        guild1 = Guild.objects.first()
        guild2 = Guild.objects.last()
        url = reverse('sqds:guild_compare_units',
                      kwargs={'api_id1': guild1.api_id, 'api_id2': guild2.api_id})
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')

        self.assertContains(response, guild1.name)
        self.assertContains(response, guild2.name)
        self.assertTrue(table_column_contains_int(soup.table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/guild_units.html')

    def test_players_view(self):
        url = reverse('sqds:players')
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertContains(response, "Player list")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(table_column_contains_int(table, 'Level'))
        self.assertTrue(table_column_contains_int(table, 'Zeta count'))
        self.assertTrue(table_column_contains_int(table, 'Sep GP'))
        self.assertTemplateUsed(response, 'sqds/player_list.html')

    def test_units_view(self):
        url = reverse('sqds:units')
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertContains(response, "Unit list")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(table_column_contains_int(table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/unit_list.html')
