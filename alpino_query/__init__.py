#!/usr/bin/env python3
from typing import List, Optional
from lxml import etree

from .parser import parse_sentence, parse_sentence_legacy
from .marker import main as mark
from .subtree import generate_subtree
from .xpath_generator import main as generate_xpath


class AlpinoQuery:
    subtree: Optional[etree._Element]

    def __init__(self, server=None):
        self.server = server

    @property
    def marked_xml(self) -> str:
        return self.__get_xml(self.marked)

    @marked_xml.setter
    def marked_xml(self, value: str) -> None:
        self.marked = etree.fromstring(bytes(value, encoding='utf-8'))

    @property
    def subtree_xml(self):
        if self.subtree is None:
            return '<node cat="top" rel="top"></node>\n'
        return self.__get_xml(self.subtree)

    @subtree_xml.setter
    def subtree_xml(self, value: str) -> None:
        self.subtree = etree.fromstring(bytes(value, encoding='utf-8'))

    def parse(self, tokens: List[str]) -> str:
        if self.server is None:
            return self.parse_legacy(tokens)
        return parse_sentence(' '.join(tokens), server=self.server)

    def parse_legacy(self, tokens: List[str]) -> str:
        parse = parse_sentence_legacy(' '.join(tokens))
        self.subtree_xml = parse
        return parse

    def mark(self, inputxml: str, tokens: List[str], attributes: List[str]) -> etree._Element:
        self.marked = mark(inputxml, tokens, attributes)
        return self.marked

    def generate_subtree(self, remove: List[str]) -> None:
        """
        Generate subtree, removes the top "rel" and/or "cat"
        """
        self.subtree = generate_subtree(self.marked, remove)

    def generate_xpath(self, order: bool) -> str:
        self.xpath = generate_xpath(self.subtree_xml, order)
        return self.xpath

    def __get_xml(self, twig) -> str:
        return etree.tostring(twig, pretty_print=True).decode()
