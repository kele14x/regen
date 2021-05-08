"""Base module contains basic Element class for use."""
from typing import Union


class Element(object):
    """Basic element of other regen elements."""

    __slots__ = ['eid', 'parent', 'content']
    eid: str  # Element ID
    parent: Union['Element', None]
    content: Union[list, None]

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

    def to_dict(self):
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
            # To prevent infinite iteration
            raise ValueError(f'Ancestor index needs to be non negative, '
                             f'received {n}')
        elif n == 0:
            return self
        elif n == 1 or self.parent is None:
            return self.parent
        else:
            return self.parent.ancestor(n - 1)

    # Iteration

    def walk(self):
        """
        Return a generator that iterates all children elements and self.

        This function will integrate all children elements including
        children of children and finally self.
        """
        if self.content is not None:
            for c in self.content:
                yield from c.walk()
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
