"""Base module contains basic Element class for use."""
import json
from typing import Union


class Element(object):
    """Basic element of other regen elements."""

    __slots__ = ['id', 'parent', 'content']
    id: str
    parent: Union['Element', None]
    content: Union[list, None]

    def __new__(cls, *args, **kwargs):
        """
        Initialize newly created ``Element`` instance.

        This is just to initialize ``self.parent`` and ``self.content`` to
        ``None``.
        """
        elem = super(Element, cls).__new__(cls)
        elem.id = ''
        elem.parent = None
        elem.content = None
        return elem

    def to_dict(self):
        """Return a ``dict`` contains needed attribute, which is suitable for JSON serialize."""
        return {
            'id': self.id,
            'content': self.content
        }

    def symbol(self, n=-1, sep='_') -> str:
        """
        Return the symbol represent of the element based on ``id``.

        ``n`` controls how many ancestors' id to be append to ``self.id``.

        ``seq`` is the separator between each ancestors' id.
        """
        s = [elem.id for elem in self.ancestors(n)]
        return sep.join(filter(None, reversed(s))).lower()

    # Navigation

    @property
    def container(self):
        """
        Get the container that contains this element.

        Usually the container is a ``list``. If no such container exists,
        ``None`` is returned.

        Don't confuse this property with ``parent``.
        """
        if self.parent is not None:
            return self.parent.content

    @property
    def index(self):
        """Get the index of this element in it's container."""
        container = self.container
        if container is not None:
            return container.index(self)

    def sibling(self, n):
        """Return n-th sibling in parent's content."""
        idx = self.index
        if idx is not None:
            idx = idx + n
            container = self.container
            if 0 <= idx < len(container):
                return container[idx]

    @property
    def next(self):
        """Return the next sibling element."""
        return self.sibling(1)

    @property
    def prev(self):
        """Return the previous sibling element."""
        return self.sibling(-1)

    def ancestor(self, n: int) -> Union['Element', None]:
        """
        Return the n-th ancestor.

        For example, ``elem.ancestor(1) == elem.parent``, and
        ``elem.ancestor(0)`` is element itself.
        """
        if n < 0:
            raise ValueError(f'Ancestor index needs to be non negative, '
                             f'received {n}')
        if n == 0:
            return self
        if n == 1 or self.parent is None:
            return self.parent
        else:
            return self.parent.ancestor(n - 1)

    # Iteration

    def walk(self):
        """
        Return a generator that iterates all children elements.

        This function will integrate all children elements including
        children of child and self.
        """
        if self.content is not None:
            for c in self.content:
                yield from c.walk()
        yield self

    def ancestors(self, n: int):
        """Return a generator that iterates to n-th ancestor."""
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
        Return a generator that iterates n-th level child elements.

        For example, ``for e in elem.children(1)`` will iterates over ``elem.content``.
        """
        if n < 1:
            raise ValueError(f'Children index needs to be positive, received '
                             f'{n}')
        if self.content is None:
            return
        if n == 1:
            for c in self.content:
                yield c
        else:
            for c in self.content:
                yield from c.children(n - 1)
