# -*- coding: utf-8 -*-

import json
import requests
from urllib.error import URLError
from urllib.request import urlopen

API_KEY = '6217fdd8f6360d58dea99eaa3b230271a2f340d8'
BASE_URL = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/%s'


def test_access_url():
    try:
        urlopen(BASE_URL % 'party')
    except URLError:
        return False
    finally:
        return True


def dadataapi_getdata_party(inn):
    if len(inn) == 10:
        type = 'LEGAL'
    else:
        type = 'INDIVIDUAL'

    url = BASE_URL % 'party'
    headers = {
        'Authorization': 'Token %s' % API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        'query': inn,
        'type': type,
        'status': ['ACTIVE', 'LIQUIDATING', 'BANKRUPT', 'REORGANIZING']
    }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    return r.json()


def dadataapi_getdata_banki(bik):
    url = BASE_URL % 'bank'
    headers = {
        'Authorization': 'Token %s' % API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        'query': bik,
        'status': ['ACTIVE']
    }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    return r.json()
