#!/usr/bin/env python3
# XPathGenerator.pl
# Alpino-XML XPath Generator

# version 2.0 data: 10.11.2021 translated to Python, multiple includes/excludes per token
# version 1.7 date: 10.06.2015  bug fix (@number)
# version 1.6 date: 15.12.2014  bug fix (ignore not-function if word order is checked)
# version 1.5 date: 14.10.2014  RELEASED WITH GrETEL2.0
# written by Vincent Vandeghinste and Liesbeth Augustinus (c) 2014
# for the GrETEL2.0 project

# script converts an XML tree into an XPath expression

############################################################################
# argument: -xml: path to xml-subtree
# options: -order/-o: word order is important
#          -r: exclude root node from the XPath expression
#          -version/-v: script details
#          -in: attributes to include (comma-separated list)
#          -ex: attributes to exclude (comma-separated list)

############################################################################

import re
from typing import cast, List, Tuple, Iterable, Union
from lxml import etree


def generate_xpath(twig: etree._Element, order: bool) -> str:
    root = twig

    if root.xpath("/alpino_ds"):
        # for ALPINO XML, leave out the alpino_ds node
        subtree = cast(etree._Element, root.find("node"))
    else:
        subtree = root  # start at root node

    # generate XPath expression

    topxpath, negate = GetXPath(subtree)
    xpath = ProcessTree(subtree, order)

    if xpath and topxpath:  # if more than one node is selected
        if negate:
            xpath = f'//node[@rel="top" and not(..//{topxpath} and ..//{xpath}])]'
        else:
            xpath = f"//{topxpath} and {xpath}]"

    elif xpath and not topxpath:
        xpath = f"//*[{xpath}]"

    elif not xpath and topxpath:
        # if only one node is selected
        if negate:
            xpath = f'//node[@rel="top" and not(..//{topxpath}])]'
        else:
            xpath = f"//{topxpath}]"

    else:
        print("ERROR: no XPath expression could be generated.\n")

    return xpath


def ProcessTree(tree, order):
    xpath = ""
    children = tree.getchildren()
    childxpaths = []
    COUNTS = {}
    ALREADY = set()
    if len(children) > 0:
        for child in children:
            childxpath, negate = GetXPath(child)

            if childxpath:
                lower = ProcessTree(child, order)
                if lower:
                    childxpath += f" and {lower}]"

                else:
                    childxpath += "]"

                if negate:
                    childxpath = f"not({childxpath})"
                COUNTS[childxpath] = COUNTS.get(childxpath, 0) + 1
                childxpaths.append(childxpath)

        if childxpaths:
            i = 0
            while i < len(childxpaths):

                # ADD COUNT FUNCTION
                if COUNTS[childxpaths[i]] > 1:
                    childxpaths[i] = (
                        "count("
                        + childxpaths[i]
                        + ") > "
                        + str(COUNTS[childxpaths[i]] - 1)
                    )

                # REMOVE DOUBLE DAUGHTERS
                if childxpaths[i] in ALREADY:
                    childxpaths = childxpaths[:i] + childxpaths[i + 1:]
                    i -= 1

                else:
                    ALREADY.add(childxpaths[i])

                i += 1

            xpath = str.join(" and ", childxpaths)

        else:
            # die "not implemented yet\n";
            return None

    else:  # no children
        if order:
            xpath = "number(@begin)"
            next_term, nextpath = FindNextTerminalToCompare(tree)
            if next_term is not None:
                if float(tree.attrib.get("begin", "nan")) < float(
                    next_term.attrib.get("begin", "nan")
                ):

                    xpath += " < "

                else:
                    xpath += " > "

                xpath += nextpath

            else:
                return None

    return xpath


def FindNextTerminalToCompare(tree):
    next_sibling = tree.getnext()
    if next_sibling is not None:
        path = "../"
        next_terminal, xpath = FindNextLeafNode(next_sibling)
        path = path + xpath
        if "begin" in path:

            # $path='number('.$path.')';
            path = re.sub(r"\@begin", "number(@begin)", path)

    else:
        # go up the tree to find next sibling
        parent = tree.getparent()
        if parent is not None:
            next_terminal, nextpath = FindNextTerminalToCompare(parent)
            if not nextpath:
                return None, None

            path = "../" + nextpath

        else:
            return None, None

    return next_terminal, path


def FindNextLeafNode(node):
    children = node.getchildren()
    xpath, negate = GetXPath(node)
    if negate:
        xpath = f"not({xpath}])"
    else:
        xpath += "]"
    if len(children) > 0:
        node, childpath = FindNextLeafNode(children[0])
        xpath += "/" + childpath
        return node, xpath

    else:
        path = xpath + "/@begin"
        return node, path


def escape_xpath_attribute(value: Union[str, int]) -> str:
    """Escapes a value for use an XPATH attribute

    Args:
        value (Union[str, int]): the text or number to include

    Returns:
        str: valid XPATH attribute
    """
    if type(value) is int:
        return str(value)

    escaped = []
    for part in re.findall('("|\'|[^"]+)', cast(str, value)):
        if '"' in part:
            escaped.append(f"'{part}'")
        else:
            escaped.append(f'"{part}"')

    if len(escaped) == 1:
        return escaped[0]

    return "concat(" + ", ".join(escaped) + ")"


def property_selector(key: str, value: str, lower: bool, negative: bool) -> str:
    operator = "!=" if negative else "="

    if lower and value.lower() != value.upper():
        selector = (
            f"lower-case(@{key}){operator}{escape_xpath_attribute(value.lower())}"
        )
    elif value:
        selector = f"@{key}{operator}{escape_xpath_attribute(value)}"
    else:
        selector = f"@{key}"
        if negative:
            selector = f"not({selector})"

    return selector


def GetXPath(tree: etree._Element) -> Tuple[str, bool]:
    """Generates an XPath from the passed tree structure. Might also
    return a value indicating whether the entire query should be
    negated (using not())

    Args:
        tree (etree._Element): marked tree to process

    Returns:
        str, bool: query, negate
    """
    att = tree.attrib
    exclude = cast(str, att.get("exclude", "")).split(",")

    selectors: List[str] = []
    # if all selectors are exclusive, use the positive selectors
    # and negate the entire node
    positive_selectors = []

    for key, value in cast(Iterable[Tuple[str, str]], att.items()):
        # all attributes are included in the XPath expression...
        # ...except these ones
        if key not in ["postag", "begin", "end", "caseinsensitive", "exclude"]:
            lower = False

            if value and key in ["word", "lemma"]:
                caseinsensitive = cast(str, att.get("caseinsensitive", "no"))
                if caseinsensitive == "yes":
                    lower = True

            if key in exclude:
                selectors.append(property_selector(key, value, lower, True))
                positive_selectors.append(property_selector(key, value, lower, False))
            else:
                selectors.append(property_selector(key, value, lower, False))

    if not selectors:

        # no matching attributes found
        return "", False

    else:
        # one or more attributes found
        if len(selectors) == len(positive_selectors):
            selectors = positive_selectors
            negate = True
        else:
            negate = False
        string = str.join(" and ", selectors)
        xstring = "node[" + string

        return xstring, negate


def main(inputxml, order):
    twig = etree.fromstring(bytes(inputxml, encoding="utf-8"))
    if order in ["false", "False", "0", 0, False]:
        order = False
    else:
        order = True

    xpath = generate_xpath(twig, order)
    return xpath
