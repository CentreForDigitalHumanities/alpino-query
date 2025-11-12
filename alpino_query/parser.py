import asyncio
import os
import re
from typing import Union, cast
from datetime import date
from urllib.parse import quote_plus
from enum import Enum
import requests

DEFAULT_GRETEL_GET = "https://gretel.hum.uu.nl/parse/parse-sentence?s="

closing_punctuation = re.compile(r"([^\s])([\.?!])$")
sentence_id_matcher = re.compile(r'(?<=sentid=")[^"]+(?=")')
sentence_tag_matcher = re.compile(r"(?<=<sentence)(?![\w-])")


class Protocol(Enum):
    NATIVE = 1
    """Connect to Alpino using the built in server mode
    https://www.let.rug.nl/vannoord/alp/Alpino/AlpinoUserGuide.html#_running_alpino_as_a_server
Pass the host and port separated by a colon e.g. localhost:7001
    """

    POST_JSON = 2
    """Uses a POST request to parse the sentence. Specify a property name in the address
     by prefixing it with a hashtag followed by the output key name.
     E.g. the address https://server#input#output will send a POST request to
     https://server and will put the sentence in a JSON data object like
     {input: 'sentence'}. It will expect an output JSON of the format
     {output: '<ALPINO XML>}
    """

    GET = 3
    """Uses a GET request to parse the sentence. The address is assumed to have the right
query parameter and the server is assumed to accept a quote_plus escaped sentence.
    """


def determine_alpino_version(alpino_directory: Union[str, None]):
    try:
        if alpino_directory is None:
            raise KeyError
        version_path = os.path.join(cast(str, alpino_directory), "version")
        version = cast(Union[str, None], open(version_path).read().strip())
        version_date = cast(
            Union[date, None], date.fromtimestamp(os.path.getmtime(version_path))
        )
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
        parsed = self.parse_line("hallo wereld !", "42")
        if '"42|hallo"' in parsed:
            self.prefix_id = False  # Add it ourselves
            parsed = self.parse_line("hallo wereld !", "42")
            if '"hallo"' not in parsed:
                raise Exception("Alpino has unsupported sentence ID behavior")

        # validate that the match can be found
        match = sentence_id_matcher.search(parsed)
        if not match:
            # no sentence ID added, add it ourselves
            self.write_id = True
        else:
            if self.prefix_id and match.group(0) != "42":
                raise Exception(
                    "Unexpected sentence id: {0} instead of 42".format(match.group(0))
                )

        # detect version
        try:
            alpino_home = cast(Union[str, None], os.environ["ALPINO_HOME"])
        except KeyError:
            alpino_home = None
        self.version, self.version_date = determine_alpino_version(alpino_home)

    async def communicate(self, line: str, sentence_id: str) -> str:
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
        line = closing_punctuation.sub(lambda m: m.group(1) + " " + m.group(2), line)
        xml = asyncio.run(self.communicate(line, sentence_id))

        if "<alpino_ds" not in xml:
            raise Exception(xml)

        if not self.prefix_id:
            xml = sentence_id_matcher.sub(sentence_id, xml)
        if self.write_id:
            xml = sentence_tag_matcher.sub(f' sentid="{sentence_id}"', xml)

        return xml


def parse_sentence(
    sentence: str, address: str = DEFAULT_GRETEL_GET, protocol: Protocol = Protocol.GET
) -> str:
    if protocol == Protocol.NATIVE:
        host, port = address.split(":")
        client = AlpinoServerClient(host, int(port))
        return client.parse_line(sentence, "zin")
    elif protocol == Protocol.GET:
        url = address + quote_plus(sentence)
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    elif protocol == Protocol.POST_JSON:
        url, name, response_key = address.split("#")
        response = requests.post(url, json={name: sentence})
        response.raise_for_status()
        return response.json()[response_key]
