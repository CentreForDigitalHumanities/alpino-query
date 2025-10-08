import asyncio
import os
import re
from typing import Tuple, Union, cast
from datetime import date
from urllib.parse import quote_plus
import requests

GRETEL_BASE_URL = 'https://gretel.hum.uu.nl/'

closing_punctuation = re.compile(r'([^\s])([\.?!])$')
sentence_id_matcher = re.compile(r'(?<=sentid=")[^"]+(?=")')
sentence_tag_matcher = re.compile(r'(?<=<sentence)(?![\w-])')


def determine_alpino_version(alpino_directory: Union[str, None]):
    try:
        if alpino_directory == None:
            raise KeyError
        version_path = os.path.join(cast(str, alpino_directory), 'version')
        version = cast(Union[str, None], open(version_path).read().strip())
        version_date = cast(Union[date, None], date.fromtimestamp(
            os.path.getmtime(version_path)))
    except KeyError:
        version = None
        version_date = None
    return (version, version_date)


class AlpinoServerClient:
    """
    Wrapper for connecting to an Alpino parser server.
    """

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.prefix_id = True
        self.write_id = False
        parsed = self.parse_line("hallo wereld !", '42')
        if '"42|hallo"' in parsed:
            self.prefix_id = False  # Add it ourselves
            parsed = self.parse_line("hallo wereld !", '42')
            if not '"hallo"' in parsed:
                raise Exception("Alpino has unsupported sentence ID behavior")

        # validate that the match can be found
        match = sentence_id_matcher.search(parsed)
        if not match:
            # no sentence ID added, add it ourselves
            self.write_id = True
        else:
            if self.prefix_id and match.group(0) != "42":
                raise Exception(
                    "Unexpected sentence id: {0} instead of 42".format(match.group(0)))

        # detect version
        try:
            alpino_home = cast(Union[str, None], os.environ['ALPINO_HOME'])
        except KeyError:
            alpino_home = None
        self.version, self.version_date = determine_alpino_version(alpino_home)

    async def communicate(self, line: str, sentence_id: str) ->str:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        if self.prefix_id:
            line = "{0}|{1}".format(sentence_id, line)
        writer.write((line + "\n\n").encode())
        await writer.drain()
        return (await reader.read()).decode()

    def parse_line(self, line: str, sentence_id: str) -> str:
        """Parse a line using the Alpino parser.


        Arguments:
            line {str} -- Tokenized text
            sentence_id {str} -- Id to record in the XML output

        Returns:
            {str} -- Lassy XML
        """
        # add a whitespace before the closing punctuation when it's missing
        line = closing_punctuation.sub(
            lambda m: m.group(1) + ' ' + m.group(2), line)
        xml = asyncio.run(self.communicate(line, sentence_id))

        if "<alpino_ds" not in xml:
            raise Exception(xml)

        if not self.prefix_id:
            xml = sentence_id_matcher.sub(sentence_id, xml)
        if self.write_id:
            xml = sentence_tag_matcher.sub(f" sentid=\"{sentence_id}\"", xml)

        return xml



def parse_sentence_legacy(sentence: str) -> str:
    # legacy behaviour is to always use the live gretel server for alpino access
    url = GRETEL_BASE_URL + 'parse/parse-sentence?s=' + quote_plus(sentence)
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def parse_sentence(sentence: str, server: Tuple[str, int]) -> str:
    client = AlpinoServerClient(*server)
    return client.parse_line(sentence, 'zin')
