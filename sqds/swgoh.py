import datetime
import math
import queue
from concurrent import futures
from typing import Collection

import requests


class SwgohError(BaseException):
    """Base class for swgoh module exceptions."""

    def __init__(self, *args, **kwargs):
        """Initialize SwgohError with `request` and `response` objects."""
        response = kwargs.pop('response', None)
        self.response = response
        self.request = kwargs.pop('request', None)
        if (response is not None and not self.request
                and hasattr(response, 'request')):
            self.request = self.response.request

        super().__init__(*args)


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
        self.auth_expiry_time = datetime.datetime.now()
        self.access_token = ''
        self.base_url = "https://api.swgoh.help"

    def get_auth_header(self):
        if datetime.datetime.now() > self.auth_expiry_time:
            self.authenticate()

        return {'Authorization': 'Bearer %s' % self.access_token}

    def authenticate(self):
        try:
            from .swgoh_local import SWGOH_USERNAME, SWGOH_PASSWORD
        except ImportError:
            raise AuthenticationError() from ImportError

        auth_payload = {
            "username": SWGOH_USERNAME,
            "password": SWGOH_PASSWORD,
            "grant_type": "password",
            "client_id": "abc",
            "client_secret": "123"
        }

        now = datetime.datetime.now()

        response = requests.post(
            "%s/auth/signin" % self.base_url, data=auth_payload)

        if response.status_code != 200:
            raise AuthenticationError(response=response)
        try:
            data = response.json()
            self.access_token = data['access_token']
            self.auth_expiry_time = now + datetime.timedelta(seconds=data['expires_in'])
        except KeyError:
            raise AuthenticationError(response=response)

    def get_unit_list(self):
        try:
            response = requests.post(
                url="%s/swgoh/data" % self.base_url,
                headers=self.get_auth_header(),
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
            return response.json()
        except requests.exceptions.RequestException:
            raise ApiError()

    def get_skill_list(self):
        try:
            response = requests.post(
                url="%s/swgoh/data" % self.base_url,
                headers=self.get_auth_header(),
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
            return response.json()
        except requests.exceptions.RequestException:
            raise ApiError()

    def get_ability_list(self):
        try:
            response = requests.post(
                url="%s/swgoh/data" % self.base_url,
                headers=self.get_auth_header(),
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
            return response.json()
        except requests.exceptions.RequestException:
            raise ApiError()

    def get_gear_list(self):
        try:
            response = requests.post(
                url="%s/swgoh/data" % self.base_url,
                headers=self.get_auth_header(),
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
            return response.json()
        except requests.exceptions.RequestException:
            raise ApiError()

    def get_category_list(self):
        try:
            response = requests.post(
                url="%s/swgoh/data" % self.base_url,
                headers=self.get_auth_header(),
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
            return response.json()
        except requests.exceptions.RequestException:
            raise ApiError()

    def get_guild_list(self, ally_code):
        try:
            response = requests.post(
                url="%s/swgoh/guild" % self.base_url,
                headers=self.get_auth_header(),
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
                })

            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise ApiError(response=response)
            return response.json()[0]
        except requests.exceptions.RequestException:
            raise ApiError()

    def get_player_data(self, ally_codes, calc_stats=True):
        try:
            response = requests.post(
                url="%s/swgoh/player" % self.base_url,
                headers=self.get_auth_header(),
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
                })
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise ApiError(response=response)

            if calc_stats:
                response2 = requests.post(
                    url="https://crinolo-swgoh.glitch.me/testCalc/api/characters",
                    params={
                        "flags": "gameStyle",
                        "language": "eng_us",
                    },
                    headers={
                        "Content-Type": "application/json",
                    },
                    json=response.json()
                )

                if response2.status_code == 404:
                    return None
                if response2.status_code != 200:
                    raise ApiError(response=response2)

                return response2.json()
            else:
                return response.json()
        except requests.exceptions.RequestException:
            raise ApiError()

    def _download_players(self, ally_codes: Collection[int]):
        print(f"Downloading {ally_codes}")
        data = self.get_player_data(ally_codes)
        return data

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
                        # print(f"Checking results for things {futures_to_ally_codes[
                        # done]}")

                        # This will raise an ApiError if the corresponding futures
                        # failed to download the player data
                        res = done.result()
                    except ApiError:
                        # We put back the things we needed to get do in the queue
                        _ = list(map(ally_codes_queue.put, futures_to_ally_codes[done]))

                        # We adapt the batch size and increase the error count
                        if batch_size > 1:
                            batch_size = math.ceil(batch_size / 2)
                        error_count += 1
                        print(f"Error caught, batch size reduced to {batch_size}")
                    else:
                        # Download was successful, keep the results
                        results.extend(res)

                    # The future is complete and must be deleted from our maps
                    del futures_to_ally_codes[done]

                    # print(
                    #    f"Loop status: batch size {batch_size}, error count {
                    #    error_count}, "
                    #    f"result length {len(results)}")

                    # Since we have freed a worker, we can schedule more download.
                    # Unless we have too many errors, in which case we throw a BatchError
                    if not ally_codes_queue.empty():
                        if error_count <= self.MAX_ERROR_COUNT:
                            ally_code_batch = ally_codes_queue.get_n(batch_size)
                            futures_to_ally_codes[
                                executor.submit(self._download_players,
                                                ally_code_batch)] = ally_code_batch
                        else:
                            # print(
                            #    f"BATCH ERROR: too many errors, error count {
                            #    error_count}")
                            raise BatchError
        return results


# pylint: disable=invalid-name
api = Swgoh()
