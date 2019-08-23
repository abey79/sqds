import math
import queue
import time
from concurrent import futures
from typing import Collection

import requests

from django.core.cache import cache


class SwgohError(Exception):
    """Base class for swgoh module exceptions."""

    def __init__(self, message, request=None, response=None):
        """Initialize SwgohError with `request` and `response` objects."""
        super().__init__(message)

        self.response = response
        self.request = request
        if (self.response is not None and self.request is None
                and hasattr(self.response, 'request')):
            self.request = self.response.request


class AuthenticationError(SwgohError):
    """Raised upon failure to authenticate to the service."""
    pass


class ApiError(SwgohError):
    """Raised upon error returned by API."""
    pass


class BatchError(SwgohError):
    """Raised if too many errors occurred during batch download."""
    pass


class MultipleGetQueue(queue.Queue):
    def get_n(self, n):
        """
        Pop up to n items from the queue. The function will block until at least one
        item is available. Then it will immediately get every item available up to a total
        of n.
        """
        result = [self.get()]  # block until at least 1
        try:  # add more until `q` is empty or `n` items obtained
            while len(result) < n:
                result.append(self.get(block=False))
        except queue.Empty:
            pass
        return result


class Swgoh:
    # Configuration variable for player batch download
    INITIAL_BATCH_SIZE = 5
    MAX_WORKER_COUNT = 5
    MAX_ERROR_COUNT = 5

    def __init__(self):
        self.base_url = "https://api.swgoh.help"

    def get_access_token(self):
        access_token = cache.get('access_token')

        # If an access_token has been cached, we can return it directly.
        if access_token is not None:
            return access_token

        # We don't have a cached access token, so we must authenticate.
        try:
            from .swgoh_local import SWGOH_USERNAME, SWGOH_PASSWORD
        except ImportError:
            raise AuthenticationError(
                'Missing credentials. Credentials must be '
                'defined in a file named swgoh_local.py') from ImportError

        auth_payload = {
            "username": SWGOH_USERNAME,
            "password": SWGOH_PASSWORD,
            "grant_type": "password",
            "client_id": "abc",
            "client_secret": "123"
        }

        start_time = time.time()
        url = "%s/auth/signin" % self.base_url
        response = requests.post(
            url, data=auth_payload)

        if response.status_code != 200:
            raise AuthenticationError(
                f'Unexpected status code returned by {url}: {response.status_code}',
                response=response)
        try:
            data = response.json()
            access_token = data['access_token']

            # Cache the access token and set a conservative timeout before it expires
            stop_time = time.time()
            cache.set('access_token', access_token,
                      data['expires_in'] - math.ceil(stop_time - start_time))
        except KeyError:
            raise AuthenticationError(
                f'Unexpected content returned by {url}', response=response)

        return access_token

    def get_auth_header(self):
        return {'Authorization': 'Bearer %s' % self.get_access_token()}

    def _call_swgoh_help_api(self, endpoint, json, accept_404=False):
        """
        Call a swgoh.help end-point with json payload and return the response,
        interpreted as json.
        :param endpoint: end-point to call, e.g. /swgoh/data
        :param json: json POSTed to end-point
        :param accept_404: if True, return None upon 404, otherwise an exception will
        be raised
        :return: objects returned by the end-point, interpreted as json
        """
        url = f'{self.base_url}{endpoint}'
        try:
            response = requests.post(
                url=url,
                headers=self.get_auth_header(),
                json=json)
        except requests.exceptions.RequestException as exc:
            raise ApiError(f'Unexpected {type(exc).__name__} while accessing {url}')

        ok = (accept_404 and response.status_code == 404) or response.status_code == 200
        if not ok:
            raise ApiError(
                f'Unexpected {response.status_code} status code returned by {url}',
                response=response)

        if response.status_code == 404:
            return None
        else:
            return response.json()

    def get_unit_list(self):
        return self._call_swgoh_help_api(
            endpoint='/swgoh/data',
            json={
                "collection": "unitsList",
                "language": "ENG_US",
                "match": {
                    "rarity": 7,
                    "obtainable": True,
                    "obtainableTime": 0,
                    "combatType": 1
                },
                "enums": True
            })

    def get_skill_list(self):
        return self._call_swgoh_help_api(
            endpoint='/swgoh/data',
            json={
                "collection": "skillList",
                "language": "eng_us",
                # "enums": True,
                "project": {
                    "id": True,
                    "abilityReference": True,
                    "skillType": True,
                    "isZeta": True
                }
            })

    def get_ability_list(self):
        return self._call_swgoh_help_api(
            endpoint='/swgoh/data',
            json={
                "collection": "abilityList",
                "language": "eng_us",
                "enums": "true",
                "project": {
                    "id": True,
                    "nameKey": True,
                    "abilityType": True
                }
            })

    def get_gear_list(self):
        return self._call_swgoh_help_api(
            endpoint='/swgoh/data',
            json={
                "collection": "equipmentList",
                "language": "eng_us",
                "enums": "true",
                "project": {
                    "nameKey": True,
                    "id": True,
                    "equipmentStat": True,
                    "tier": True,
                    "type": True,
                    "requiredRarity": True,
                    "requiredLevel": True
                }
            })

    def get_category_list(self):
        return self._call_swgoh_help_api(
            endpoint='/swgoh/data',
            json={
                "collection": "categoryList",
                "language": "eng_us",
                "match": {
                    "visible": True
                },
                "project": {
                    "id": True,
                    "descKey": True
                },
                "enums": "true"
            })

    def get_guild_list(self, ally_code):
        guild_data = self._call_swgoh_help_api(
            endpoint='/swgoh/guild',
            json={
                "allycodes": [ally_code],
                "language": "eng_us",
                "project": {
                    "roster": {
                        "gpChar": True,
                        "gpShip": True,
                        "gp": True,
                        "id": True,
                        "level": True,
                        "allyCode": True,
                        "name": True
                    },
                    "id": True,
                    "name": True,
                    "gp": True
                },
                "enums": True
            },
            accept_404=True)

        if guild_data is None:
            return None
        else:
            return guild_data[0]

    def get_player_data(self, ally_codes, calc_stats=True):
        player_data = self._call_swgoh_help_api(
            endpoint='/swgoh/players',
            json={
                "allycodes": ally_codes,
                "language": "eng_us",
                "enums": False,
                "project": {
                    "roster": True,
                    "updated": True,
                    "id": True,
                    "guildRefId": True,
                    "allyCode": True,
                    "level": True,
                    "stats": True,
                    "lastActivity": True,
                    "name": True
                }
            },
            accept_404=True)

        if player_data is None:
            return None

        if calc_stats:
            # url = "https://crinolo-swgoh.glitch.me/statCalc/api/characters"
            url = "https://swgoh-stat-calc.glitch.me/api/characters"
            try:
                response = requests.post(
                    url=url,
                    params={
                        "flags": "gameStyle",
                        "language": "eng_us",
                    },
                    headers={
                        "Content-Type": "application/json",
                    },
                    json=player_data)
            except requests.exceptions.RequestException as exc:
                raise ApiError(f'Unexpected {type(exc).__name__} while accessing {url}')

            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise ApiError(
                    f'Unexpected {response.status_code} status code return by {url}',
                    response=response)

            return response.json()
        else:
            return player_data

    def _download_players(self, ally_codes: Collection[int]):
        print(f"Downloading {ally_codes}")
        return self.get_player_data(ally_codes)

    def get_player_data_batch(self, ally_code_list: Collection[int]):
        """
        Download player data for multiple player using a thread pool and adaptable
        batch size
        :param ally_code_list: list of player ally codes to download
        :return: array of player data (the order is arbitrary and may be different from
                 ally code list provided
        """
        ## Setup

        # Storage for all player's data
        results = []

        # Input queue filled with all ally codes to be downloaded
        ally_codes_queue = MultipleGetQueue()
        _ = list(map(ally_codes_queue.put, ally_code_list))

        # Initial batch size. We try to be smart and use all worker available if the list
        # is small.
        batch_size = min(self.INITIAL_BATCH_SIZE,
                         math.ceil(len(ally_code_list) / self.MAX_WORKER_COUNT))

        # Work count. For very small batch, we may reduce the default worker count.
        worker_count = min(self.MAX_WORKER_COUNT,
                           math.ceil(len(ally_code_list) / batch_size))

        # Let's keep track of the number of error
        error_count = 0

        ## Run
        print(f"Batch download with {worker_count} workers and batches of {batch_size} "
              f"ally codes")
        with futures.ThreadPoolExecutor(max_workers=worker_count) as executor:

            # We keep a map of futures to the corresponding list of ally codes
            futures_to_ally_codes = {}

            # First, let's feed all workers with something to download. Thanks to the
            # smart definition of batch_size and worker_count, we are guaranteed to
            # have a batch available for every single worker.
            for _ in range(worker_count):
                ally_code_batch = ally_codes_queue.get_n(batch_size)
                futures_to_ally_codes[executor.submit(self._download_players,
                                                      ally_code_batch)] = ally_code_batch

            # We iterate until either we have the same amount of result as initially
            # requested. If the error count exceed the maximum allowed before we
            # complete all download, an exception will be raised
            while len(results) < len(ally_code_list):

                # wait for at least one worker to complete
                done_list, _ = futures.wait(futures_to_ally_codes,
                                            return_when=futures.FIRST_COMPLETED)

                for done in done_list:
                    try:
                        # This will raise an ApiError if the corresponding futures
                        # failed to download the player data
                        res = done.result()
                    except ApiError as exc:
                        # We put back the things we needed to get do in the queue
                        _ = list(map(ally_codes_queue.put, futures_to_ally_codes[done]))

                        # We adapt the batch size and increase the error count
                        if batch_size > 1:
                            batch_size = math.ceil(batch_size / 2)
                        error_count += 1
                        print(f"Error caught ({str(exc)}), batch size reduced to"
                              f" {batch_size}")
                    else:
                        # Download was successful, keep the results
                        results.extend(res)

                    # The future is complete and must be deleted from our maps
                    del futures_to_ally_codes[done]

                    # Since we have freed a worker, we can schedule more download.
                    # Unless we have too many errors, in which case we throw a BatchError
                    if not ally_codes_queue.empty():
                        if error_count <= self.MAX_ERROR_COUNT:
                            ally_code_batch = ally_codes_queue.get_n(batch_size)
                            futures_to_ally_codes[
                                executor.submit(self._download_players,
                                                ally_code_batch)] = ally_code_batch
                        else:
                            raise BatchError(
                                f'Unexpected number of errors ({error_count}) during '
                                f'batch player download')
        return results


# pylint: disable=invalid-name
api = Swgoh()
