import re
import time
import json
from typing import List

from django.db import connection

from sqds.models import Guild, Player


def format_large_int(value):
    return '{0:n}'.format(value) if value != 0 else '-'


ally_code_regex = re.compile(r'(?<!\d)([1-9]{3}-?[1-9]{3}-?[1-9]{3})(?!\d)')


def extract_all_ally_codes(text: str) -> List[int]:
    return [int(s.replace('-', '')) for s in
            ally_code_regex.findall(text)]


class QueryLogger:
    def __init__(self):
        self.queries = []

    def __call__(self, execute, sql, params, many, context):
        current_query = {'sql': sql, 'params': params, 'many': many}
        start = time.time()
        try:
            result = execute(sql, params, many, context)
        except Exception as e:
            current_query['status'] = 'error'
            current_query['exception'] = e
            raise
        else:
            current_query['status'] = 'ok'
            return result
        finally:
            duration = time.time() - start
            current_query['duration'] = duration
            self.queries.append(current_query)

    def dump(self, path):
        with open(path, 'w') as f:
            json.dump(self.queries, f)


def create_or_update_guild(ally_code=116235559):
    ql = QueryLogger()
    with connection.execute_wrapper(ql):
        Guild.objects.update_or_create_from_swgoh(ally_code)
    ql.dump('ql_import_prepare.json')


def create_or_update_player(ally_code=116235559):
    ql = QueryLogger()
    with connection.execute_wrapper(ql):
        Player.objects.update_or_create_from_swgoh(ally_code)
    ql.dump('ql_import_hhip.json')
