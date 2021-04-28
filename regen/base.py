import json


class Element(object):
    """
    Basic element of other regen elements.
    """

    __slots__ = ['parent', 'content']

    def __new__(cls, *args, **kwargs):
        element = super(Element, cls).__new__(cls)
        element.parent = None
        element.content = None
        return element

    def to_json(self):
        """Serialize this object to a JSON string."""
        if self.content is not None:
            return {
                'content': self.content
            }
        else:
            return {}

    def dumps(self):
        return json.dumps(self, cls=JSONEncoder, indent=2)

    # Navigation

    @property
    def container(self):
        """
        Get the container (a ``list``) that contains this element,
        or None if no such container exists.
        """
        if self.parent is not None:
            return self.parent.content

    @property
    def index(self):
        """Get the index of this element in parent's content."""
        container = self.container
        if container is not None:
            return container.index(self)

    def sibling(self, n):
        """Return n-th sibling in parent's content"""
        idx = self.index
        if idx is not None:
            idx = idx + n
            container = self.container
            if 0 <= idx < len(container):
                return container[idx]

    @property
    def next(self):
        return self.sibling(1)

    @property
    def prev(self):
        return self.sibling(-1)

    def ancestor(self, n: int):
        """
        Return the n-th ancestor.
        For example, ``elem.ancestor(1) == elem.parent``.
        """
        if n < 1:
            raise ValueError(f'Ancestor index needs to be positive, received '
                             f'{n}')
        if n == 1:
            return self.parent
        else:
            return self.parent.ancestor(n-1)

    # Iteration

    def walk(self):
        if self.content is not None:
            for c in self.content:
                yield from c.walk()
        yield self

    def children(self, n: int):
        """
        Return a generator that iterates all n-th child element.
        For example, ``elem.children(1)`` wil iterates over ``elem.content``.
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
                yield from c.children(n-1)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder for Block object."""

    def default(self, o):
        """Overloaded method to return an dict for json encoding."""
        if isinstance(o, Element):
            return o.to_json()

        return super(JSONEncoder, self).default(o)
