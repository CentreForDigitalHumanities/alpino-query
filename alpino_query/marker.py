#!/usr/bin/env python3
# mark the matched tokens in the tree with include/exclude attributes
import re
from typing import cast, List, Set
from lxml import etree
from .xpath_generator import escape_xpath_attribute


def mark(twig: etree._Element, tokens: List[str], attributes: List[str]) -> None:
    # add info annotation matrix to alpino parse
    for begin, token in enumerate(tokens):
        if re.match(r"([_<>\.,\?!\(\)\"\'])|(\&quot;)|(\&apos;)", token):
            xp = cast(
                List[etree._Element],
                twig.xpath(f"//node[@begin={escape_xpath_attribute(begin)}]"),
            )
        else:
            xp = cast(
                List[etree._Element],
                twig.xpath(
                    f"//node[@word={escape_xpath_attribute(token)} and @begin={escape_xpath_attribute(begin)}]"
                ),
            )
        if begin < len(attributes):
            attrs = attributes[begin].split(",")
            for x in xp:
                include: Set[str] = set()
                exclude: Set[str] = set()
                case_insensitive = None
                for attr in attrs:
                    if attr[0] == "-":
                        target = exclude
                        attr = attr[1:]
                    else:
                        target = include

                    if attr == "cs":
                        # cs: case sensitive
                        # -cs: case insensitive
                        case_insensitive = target is exclude
                    elif attr == "word":
                        target.add("word")
                        if case_insensitive is None:
                            case_insensitive = True
                    else:
                        target.add(attr)

                if case_insensitive:
                    x.attrib["caseinsensitive"] = "yes"

                if include:
                    x.attrib["include"] = str.join(",", sorted(include))
                if exclude:
                    x.attrib["exclude"] = str.join(",", sorted(exclude))


def main(inputxml: str, tokens: List[str], attributes: List[str]) -> etree._Element:
    twig: etree._Element = etree.fromstring(bytes(inputxml, encoding="utf-8"))
    mark(twig, tokens, attributes)
    return twig
