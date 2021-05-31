"""Base module contains basic Element class for use."""
import copy
from typing import Optional


class Element(object):
    """Basic element of other regen elements."""

    __slots__ = ['eid', 'parent', 'content']
    eid: str  # Element ID
    parent: Optional['Element']
    content: Optional[list['Element']]

    def __new__(cls, *args, **kwargs):
        """
        Initialize newly created ``Element`` instance.

        This is just to initialize ``self.parent`` and ``self.content`` to
        ``None``.
        """
        elem = super(Element, cls).__new__(cls)
        elem.eid = ''
        elem.parent = None
        elem.content = None
        return elem

    def __init__(self, eid='', parent=None):
        self.eid = eid
        self.parent = parent

    @property
    def id(self):
        """Get the simple ID."""
        return self.eid

    @property
    def full_id(self):
        """Get the full hierarchical ID."""
        return self.symbol()

    @property
    def identifier(self):
        """Get the proper hierarchical ID for HDL generation."""
        return self.symbol()

    def to_dict(self) -> dict:
        """
        Return a ``dict`` contains key attributes.

        The key attributes are necessary and sufficient attributes to rebuild
        this element.

        This is mainly intent for JSON serialize.
        """
        return {
            'id': self.eid,
            'content': self.content
        }

    def symbol(self, n=-1, sep='_') -> str:
        """
        Return the symbol represent of the element based on ``eid``.

        ``n`` controls how many ancestors' ID to be append to ``self.eid``.

        ``sep`` is the separator between each ancestors' ID.
        """
        s = [elem.eid for elem in self.ancestors(n)]
        return sep.join(filter(None, reversed(s)))

    def ancestor(self, n: int) -> Optional['Element']:
        """
        Return the n-th ancestor.

        For example, ``elem.ancestor(1) == elem.parent``, and
        ``elem.ancestor(0)`` is element itself.
        """
        if n < 0:
            # To prevent infinite iteration
            raise ValueError(f'Ancestor index needs to be non negative, '
                             f'received {n}')
        elif n == 0:
            return self
        elif n == 1 or self.parent is None:
            return self.parent
        else:
            return self.parent.ancestor(n - 1)

    def count(self) -> int:
        """Count the number of elements, including children elements and self."""
        return sum((1 for _ in self.walk()))

    # Iteration

    def walk(self, b2t=False):
        """
        Return a generator that iterates all children elements and self.

        This function will integrate all children elements including
        children of children and finally self.
        """
        if not b2t:
            yield self
        if self.content is not None:
            for c in self.content:
                yield from c.walk(b2t)
        if b2t:
            yield self

    def ancestors(self, n: int):
        """Return a generator that iterates from self to n-th ancestor."""
        yield self
        if n == 0:
            return
        else:
            if self.parent is None:
                return
            else:
                yield from self.parent.ancestors(n-1)

    def children(self, n: int):
        """
        Return a generator that iterates all children of n-th generation.

        For example, ``elem.children(1)`` will iterate over ``elem.content``,
        and ``elem.children(0)`` will iterate only self.
        """
        if n < 0:
            # To prevent infinite iteration
            raise ValueError(f'Children index needs to be non negative, '
                             f'received {n}')
        if n == 0:
            yield self
        elif self.content is None:
            return
        elif n == 1:
            yield from self.content
        else:
            for c in self.content:
                yield from c.children(n - 1)

    def copy(self):
        """
        Return a deep copy version of this element.

        This function return a new copied element of self, and recursively
        copies of it's content.

        Note: The copied element will has same parent with original one.
        """
        copied = copy.copy(self)
        if self.content is not None:
            # ``copy.copy()`` create a new list, but this list contains
            # references to original objects. We need a new list for copied
            # children elements.
            copied.content = [elem.copy() for elem in self.content]
            # The copied children elements have ``parent`` attribute reference
            # to self, change it to copied one
            for elem in copied.content:
                elem.parent = copied
        return copied
