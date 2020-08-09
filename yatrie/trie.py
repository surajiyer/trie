"""
    description: Trie data structure for fast string lookups
    author: Suraj Iyer
"""

__all__ = ['Trie', 'StringTrie', 'WordCountTrie']

from collections.abc import MutableMapping
import dill
import operator


class Node:
    __slots__ = 'value', 'children', 'n_items', 'parent'
    ChildrenFactory = dict

    def __init__(self, value=None, parent=None):
        self.value = value
        self.children = self.ChildrenFactory()
        self.parent = parent
        self.n_items = 0
        if parent and value:
            self.update_n_items()

    def update_n_items(self, op: str = '+', amt: int = 1):
        op = {'+': operator.add, '-': operator.sub}[op]
        parent = self.parent
        while parent is not None:
            parent.n_items = op(parent.n_items, amt)
            parent = parent.parent

    def clear(self):
        self.children.clear()
        self.update_n_items('-', self.n_items)
        self.n_items = 0

    def __len__(self):
        return self.n_items

    def __repr__(self):
        return f'{self.value}'

    def __setstate__(self, state):
        self.value, self.children,\
            self.n_items, self.parent = state

    def __getstate__(self):
        return self.value, self.children,\
            self.n_items, self.parent


class Trie(MutableMapping):
    """
    Usage
    -----
    >>> t = Trie(cat=0, cats=1, catacomb=2, apple=3)
    >>> list(t.iter_prefixes('catacombs'))
    [(('c', 'a', 't'), 0), (('c', 'a', 't', 'a', 'c', 'o', 'm', 'b'), 2)]
    >>> list(t.find_prefix('app'))
    [('a', 'p', 'p', 'l', 'e')]
    >>> list(t.iterkeys())
    [('c', 'a', 't'), ('c', 'a', 't', 's'), ('c', 'a', 't', 'a', 'c', 'o', 'm', 'b'), ('a', 'p', 'p', 'l', 'e')]
    >>> list(t.itervalues())
    [0, 1, 2, 3]
    >>> list(t.iteritems())
    [(('c', 'a', 't'), 0), (('c', 'a', 't', 's'), 1), (('c', 'a', 't', 'a', 'c', 'o', 'm', 'b'), 2), (('a', 'p', 'p', 'l', 'e'), 3)]
    >>> t['yolo'] = 4
    >>> t['yolo']
    4
    >>> del t['yolo']
    >>> t['yolo']
    Traceback (most recent call last):
        ...
    KeyError
    >>> list(iter(t))
    [('c', 'a', 't'), ('c', 'a', 't', 's'), ('c', 'a', 't', 'a', 'c', 'o', 'm', 'b'), ('a', 'p', 'p', 'l', 'e')]
    >>> len(t)
    4
    >>> 'apple' in t
    True
    >>> 'yolo' in t
    False
    >>> t.clear()
    >>> list(iter(t))
    []
    >>> len(t)
    0
    """
    NodeFactory = Node
    KeyFactory = tuple

    def __init__(self, *args, **kwargs):
        self.root = self.NodeFactory()
        self.update(*args, **kwargs)

    def _find(self, key):
        node = self.root
        for part in key:
            next_node = node.children.get(part)
            if next_node is None:
                return None
            node = next_node
        return node

    def iter_prefixes(self, key):
        node = self.root
        parts = []
        for part in key:
            parts.append(part)
            next_node = node.children.get(part)
            if next_node is None:
                return
            if next_node.value is not None:
                yield (self.KeyFactory(parts), next_node.value)
            node = next_node

    @staticmethod
    def _generator(keyfactory, node, keys=[]):
        if node.value is not None:
            yield (keyfactory(keys), node.value)
        for k, child in node.children.items():
            keys.append(k)
            for result in Trie._generator(keyfactory, child, keys):
                yield result
            keys.pop(-1)

    def find_prefix(self, key):
        node = self._find(key)
        if node is None:
            return None
        return tuple(
            k for k, v in Trie._generator(
                self.KeyFactory, node, list(key)))

    def iterkeys(self):
        for k, _ in Trie._generator(
            self.KeyFactory, self.root):
            yield k

    def itervalues(self):
        for _, v in Trie._generator(
            self.KeyFactory, self.root):
            yield v

    def iteritems(self):
        return Trie._generator(
            self.KeyFactory, self.root)

    def __setitem__(self, key, value):
        node = self.root
        for part in key:
            next_node = node.children.get(part)
            if next_node is None:
                node = node.children.setdefault(
                    part, self.NodeFactory(parent=node))
            else:
                node = next_node
        node.value = value
        node.update_n_items()

    def __getitem__(self, key):
        node = self._find(key)
        if node is None or node.value is None:
            raise KeyError
        return node.value

    def __delitem__(self, key):
        node = self._find(key)
        if node is None:
            raise KeyError
        if not node.children:
            del node.parent.children[key[-1]]
            node.update_n_items('-')

    def __iter__(self):
        return self.iterkeys()

    def __len__(self):
        return len(self.root)

    def __contains__(self, key):
        return self._find(key) is not None

    def clear(self):
        self.root.clear()

    def save(self, file_path):
        with open(file_path, "wb") as f:
            dill.dump(self.root, f)

    @classmethod
    def load(cls, file_path):
        self = cls()
        with open(file_path, "rb") as f:
            self.root = dill.load(f)
        return self


class StringTrie(Trie):
    KeyFactory = ''.join


class WordCountTrie(StringTrie):
    """
    Usage
    -----
    >>> t = WordCountTrie.from_text(text='cat cats catacomb apple cats')
    >>> list(t.iter_prefixes('catacombs'))
    [('cat', 1), ('catacomb', 1)]
    >>> list(t.find_prefix('app'))
    ['apple']
    >>> list(t.find_within_distance('app'))
    ['apple']
    >>> list(t.iterkeys())
    ['cat', 'cats', 'catacomb', 'apple']
    >>> list(t.itervalues())
    [1, 2, 1, 1]
    >>> list(t.iteritems())
    [('cat', 1), ('cats', 2), ('catacomb', 1), ('apple', 1)]
    >>> t['yolo'] = 4
    >>> t['yolo']
    4
    >>> del t['yolo']
    >>> t['yolo']
    Traceback (most recent call last):
        ...
    KeyError
    >>> list(iter(t))
    ['cat', 'cats', 'catacomb', 'apple']
    >>> len(t)
    4
    >>> 'apple' in t
    True
    >>> 'yolo' in t
    False
    >>> t.clear()
    >>> list(iter(t))
    []
    >>> len(t)
    0
    """

    @classmethod
    def from_text(
            cls, text: str = None,
            file_path: str = None, lowercase=True):
        import re
        from collections import Counter
        if file_path:
            text = open(file_path).read()
        if text is None:
            raise ValueError('Need either `text` or `file_path` as input.')
        if lowercase:
            text = text.lower()
        word_counts = Counter(re.findall(r'\w+', text))
        self = cls()
        for word, count in word_counts.items():
            self[word] = count
        return self

    def find_within_distance(self, key, dist=2):
        from .utils import edits_n
        return set(k for k in self if k in edits_n(key, dist))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
