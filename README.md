# Alpino Query
[![DOI](https://zenodo.org/badge/421861899.svg)](https://zenodo.org/doi/10.5281/zenodo.10418665)
[![PyPI version](https://badge.fury.io/py/alpino-query.svg)](https://badge.fury.io/py/alpino-query)
[![Actions Status](https://github.com/CentreForDigitalHumanities/alpino-query/workflows/Python%20package/badge.svg)](https://github.com/CentreForDigitalHumanities/alpino-query/actions)

```bash
pip install alpino-query
```

When running locally without installing, instead of `alpino-query` use `python -m alpino_query`.

## Parse

Parse a (tokenized) sentence using the Alpino instance running on [gretel.hum.uu.nl](https://gretel.hum.uu.nl).

For example:

```bash
alpino-query parse Dit is een voorbeeldzin.
```

It also works when the sentence is passed as a single argument.

```bash
alpino-query parse "Dit is een voorbeeldzin ."
```

## Mark

Mark which part of the treebank should be selected for filtering. It has three inputs:

1. [Lassy/Alpino XML](https://www.let.rug.nl/~vannoord/Lassy/)
2. the tokens of the sentence
3. for each token specify the properties which should be marked

For example:

```bash
alpino-query mark "$(<tests/data/001.xml)" "Dit is een voorbeeldzin ." "pos pos pos pos pos"
```

It is also possible to mark multiple properties for a token, this is done by separating them with a comma. Each of these can also be specified to be negated. These will then be marked as 'exclude' in the tree.

```bash
alpino-query mark "$(<tests/data/001.xml)" "Dit is een voorbeeldzin ." "pos pos,-word,rel pos pos pos"
```

## Subtree

Generates a subtree containing only the marked properties. It will also contain additional attributes to mark that properties should be excluded and/or case sensitive.

The second argument can be empty, `cat`, `rel` or both (i.e. `catrel` or `cat,rel`). This indicates which attributes should be removed from the top node. When only one node is left in the subtree, this argument is ignored.

```bash
alpino-query subtree "$(<tests/data/001.marked.xml)" cat
```

## XPath

Generates an XPath to query a treebank from the generated subtree. Second argument indicates whether a query should be generated which is order-sensitive.

```bash
alpino-query xpath "$(<tests/data/001.subtree.xml)" 0
```

## Using as Module

```python
from alpino_query import AlpinoQuery

tokens = ["Dit", "is", "een", "voorbeeldzin", "."]
attributes = ["pos", "pos,-word,rel", "pos", "pos", "pos"]

query = AlpinoQuery()
alpino_xml = query.parse(tokens)
query.mark(alpino_xml, tokens, attributes)
print(query.marked_xml) # query.marked contains the lxml Element

query.generate_subtree(["rel", "cat"])
print(query.subtree_xml) # query.subtree contains the lxml Element

query.generate_xpath(False) # True to make order sensitive
print(query.xpath)
```

## Considerations

### Exclusive

When querying a node this could be exclusive in multiple ways.
For example:

* a node should not be a noun `node[@pos!="noun"]`
* it should not have a node which is a noun `not(node[@pos="noun"])`

The first statement does *require* the existence of a node, whereas the second also holds true if there is no node at all. When a token is only exclusive (e.g. not a noun) a query of the second form will be generated, if a token has both inclusive and exclusive properties a query of the first form will be generated.

### Relations

`@cat` and `@rel` are always preserved for nodes which have children. The only way for this to be dropped is for when all the children are removed by specifying the `na` property for the child tokens.

## Upload to PyPi

```bash
pip install twine
python setup.py sdist
twine upload dist/*
```

## Credits

This was original part of the [GrETEL](https://github.com/CentreForDigitalHumanities/gretel) codebase and is (still) used by its Example Based Search functionality.

* [Liesbeth Augustinus](http://www.ccl.kuleuven.be/~liesbeth/) and [Vincent Vandeghinste](http://www.ccl.kuleuven.be/~vincent/ccl): concept and initial implementation
* [Bram Vanroy](http://bramvanroy.be/): GrETEL 3 improvements and design
* [Sheean Spoel](http://www.uu.nl/staff/SJJSpoel): rewritten in Python, moved to separate library and added some improvements

## License

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (cc-by-sa-4.0). See the [LICENSE](LICENSE) file for license rights and limitations.
