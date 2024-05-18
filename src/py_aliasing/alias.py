from functools import wraps, partial


class alias:
    def __init__(self, alias_for: str, alias_name: str | None = None):
        self._for = alias_for
        # optionally provide the name here in case you want to init it without a containing class
        self._name = alias_name
        self.__doc__ = f"Alias for {self._for}"

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, owner, owner_type=None):
        if owner is None:
            # this happens when called from class level
            return self
        # just return the aliased attribute
        value = getattr(owner, self._for)
        # if value and hasattr(value, "__get__"):
        #     value = value.__get__(owner, owner_type)
        return value

    def attach(self, owner, name: str | None = None):
        self._name = name or self._name
        if not self._name:
            raise RuntimeError("must provide name to attach alias")
        cls = owner
        if type(cls) is not type:
            # we have to attach the descriptor to the class, not the instance
            # this way we support both
            cls = type(cls)
        setattr(cls, owner, self._name)
        # needs to happen after setattr as that's when it happens in the
        # typical descriptor workflow. In this class, the statement has
        # no effect, but child classes might add functionality to __set_name__
        self.__set_name__(owner, self._name)


class aliased:
    def __init__(self, func):
        if isinstance(func, alias):
            name = func._for
        else:
            name = func.__name__
        self._func = func
        self._name = name
        self._init_doc = func.__doc__

        self._private_name = f"_aliased_{self._name}"
        self._aliases = [self._name]
        self._doc_sep = '\n'
        self._doc = self._init_doc
        self._refresh_doc()

    def _refresh_doc(self):
        alias_list = ",".join(self._aliases)
        aliases_prefix = f"(aliases {alias_list})" if self._aliases else ""
        # renders a docstring like "(aliases method1,method2)\n<your original doc string here"
        self._doc = self._doc_sep.join(filter(None, [aliases_prefix, self._init_doc]))
        self.__doc__ = self._doc

    def __set_name__(self, owner, name: str):
        print(self, '__set_name__', owner, name)
        self._name = name
        self._private_name = f"_aliased_{self._name}"
        func = self._func
        self._init_doc = func.__doc__
        setattr(owner, self._private_name, func)

    def __get__(self, owner, owner_type=None):
        print(self, '__get__', owner, owner_type)
        self._refresh_doc()
        if owner is None:
            return self

        func = getattr(owner, self._private_name)

        if callable(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__doc__ = self._doc
            return wrapper

        return func

    def alias(self, member: any = None) -> alias:
        name: str | None = None
        if member is not None and hasattr(member, '__name__'):
            name = member.__name__
        elif member is not None and isinstance(member, str):
            name = member
        elif member is None:
            # rely on __set_name__ or attach to assign the name
            name = None
        else:
            raise RuntimeError(f"could not resolve alias name from non-None, non-str member {member}"
                               f" without `__name__` attribute")

        return alias(alias_for=self._name, alias_name=name)
