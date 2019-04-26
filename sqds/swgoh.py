import datetime
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

        super(SwgohError, self).__init__(args, kwargs)


class AuthenticationError(SwgohError):
    """Could not authenticate."""


class ApiError(SwgohError):
    """Api error."""


class Swgoh:
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
            self.auth_expiry_time = now + \
                datetime.timedelta(seconds=data['expires_in'])
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
            raise ApiError(response=response)

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
            raise ApiError(response=response)

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
            raise ApiError(response=response)

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
            raise ApiError(response=response)

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
            return response.json()[0]
        except requests.exceptions.RequestException:
            raise ApiError(response=response)

    def get_player_unit_list(self, ally_code):
        try:
            response = requests.get(
                url="https://crinolo-swgoh.glitch.me"
                "/statCalc/api/characters/player/%d" % ally_code,
                # headers=self.get_auth_header(),
                params={'flags': 'withModCalc,gameStyle'})
            return response.json()
        except requests.exceptions.RequestException:
            raise ApiError(response=response)


# pylint: disable=invalid-name
api = Swgoh()
