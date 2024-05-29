from . import aliased


class valiased(aliased):
    """
    returned from valiases.__call__
    descriptor that adds the named aliases to the object during the __set_name__ phase
    """
    def __init__(self, func, *aliases: str):
        super().__init__(func)
        self._aliases = list(map(lambda name: self.alias(name), aliases))

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        for alias in self._aliases:
            alias.attach(owner)


class valiases:
    """
    Usage:
        @valiases("a", "b")
        def method(): ...
        ...
        assert method() == a()
    """
    def __init__(self, *aliases: str):
        self._aliased = aliased(*aliases)

    def __call__(self, func):
        return self._aliased(func)
