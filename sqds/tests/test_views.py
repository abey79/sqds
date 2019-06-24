from bs4 import BeautifulSoup
from django.test import TestCase
from django.urls import reverse

from sqds.models import Player, Guild
from sqds.tests.utils import generate_game_data, generate_guild
from sqds_seed.factories import CategoryFactory, UnitFactory, PlayerUnitFactory


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

    @staticmethod
    def table_column_contains_int(table, column_header):
        try:
            column_index = 0
            for header in table.thead.find_all('th'):
                if header.text.strip() == column_header:
                    break
                column_index += 1

            for row in table.tbody.find_all('tr'):
                int(row.find_all('td')[column_index].string.strip().replace(',', ''))
        except ValueError:
            return False
        return True

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
        self.assertTrue(self.table_column_contains_int(table, 'Speed'))
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
        self.assertTrue(self.table_column_contains_int(table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/player_compare.html')

    def test_guild_view_valid(self):
        guild = Guild.objects.first()
        url = reverse('sqds:guild', args=[guild.api_id])
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guild'].api_id, guild.api_id)
        self.assertTrue(self.table_column_contains_int(table, 'Level'))
        self.assertTrue(self.table_column_contains_int(table, 'Zeta count'))
        self.assertTemplateUsed(response, 'sqds/guild.html')

    def test_guild_units_view_valid(self):
        guild = Guild.objects.first()
        url = reverse('sqds:guild_units', args=[guild.api_id])
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.table_column_contains_int(soup.table, 'Speed'))
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
        self.assertTrue(self.table_column_contains_int(soup.table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/guild_units.html')

    def test_players_view(self):
        url = reverse('sqds:players')
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertContains(response, "Player list")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.table_column_contains_int(table, 'Level'))
        self.assertTrue(self.table_column_contains_int(table, 'Zeta count'))
        self.assertTrue(self.table_column_contains_int(table, 'Sep GP'))
        self.assertTemplateUsed(response, 'sqds/player_list.html')

    def test_units_view(self):
        url = reverse('sqds:units')
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find_all('div', class_='table-container')[0].table

        self.assertContains(response, "Unit list")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.table_column_contains_int(table, 'Speed'))
        self.assertTemplateUsed(response, 'sqds/unit_list.html')
