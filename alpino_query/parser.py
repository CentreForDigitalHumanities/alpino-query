#!/usr/bin/env python3
from urllib.parse import quote
import requests

BASE_URL = 'https://gretel.hum.uu.nl/'


def parse_sentence(sentence: str) -> str:
    url = BASE_URL + 'parse/parse-sentence/' + quote(sentence)
    response = requests.get(url)
    response.raise_for_status()
    return response.text
